# Standard libs:
import re
import os
import sys
import json
import datetime
import argparse
import subprocess as sp
import matplotlib.pyplot as plt

# Functions:
def parse_args(args=sys.argv[1:]):
    """Parse arguments."""

    parser = argparse.ArgumentParser()

    parser.add_argument("-P", "--png",
                      help="Make plots non-interactively, and save them as PNG.",
                      action="store_true",
                      default=False)

    parser.add_argument("-p", "--project",
            help="Retrieve info from project PROJECT. Default: None",
            default=None)

    parser.add_argument("-r", "--retrieve",
                      help="Retrieve data, instead of ploting logged values. Default: don't retrieve.",
                      action="store_true",
                      default=False)

    parser.add_argument("-v", "--verbose",
                      help="Be verbose. Default: don't be.",
                      action="count",
                      default=0)

    parser.add_argument("-T", "--total",
                      help="Plot total figures, instead of percents. Default: percents.",
                      action="store_true",
                      default=False)

    parser.add_argument("-s", "--smooth",
                      help="For rate plots (in contrast to instantaneous data ones), use last [i-SMOOTH,i] data points for averaging at ith point. Default: 1.",
                      default=1)

    parser.add_argument("-R", "--recent",
                      help="Count and log also active hosts (those reporting results in the last 30 days). Default: count and log only all hosts.",
                      action="store_true",
                      default=False)

    parser.add_argument("-y", "--dryrun",
                      help="Perform a dry run: just tell what would be done, but don't do it. Default: real run (plotting, if nothing else is specified).",
                      action="store_true",
                      default=False)


    return parser.parse_args(args)

def read_conf(fn=None, logger=None):
    """Read configuration file 'fn'. If none given, use default.
    Returns configuration dictionary.
    """
    if not fn:
        fn = os.path.join(os.environ["HOME"], ".bhs.json")

    logger.info("Reading conf file [ {f} ]".format(f=fn))

    try:
        with open(fn) as f:
            res = json.load(f)
    except:
        res = {}

    if logger:
        logger.debug("Read config for following active keys:")
        logger.debug([k for k in res if res[k]["active"]])

    return res


# Classes:
class Project(object):
    """Hold all info and methods about one project."""
    
    BWLIMIT = 250 # bandwidth limit for download, in kB/s

    # Constructor:
    def __init__(self, n=None, k=None, u=None, s=[]):
        self.name = n
        self.url  = 'http://' + u
        self.key = k

        # stats is a 4-element list, with the values of last logged
        # Mcredit, kHosts, kDCGR and DINH (see code for explanations)
        # stats has no real value at all.
        self.stats = s


    # Public methods:
    def get_hostgz(self, opts):
        """Retrieve the host.gz file from the URL."""

        if (opts.verbose):
            print('Retrieving stats file...')

        cmd = 'wget --limit-rate={0:d}k {1} -O host.gz'.format(self.BWLIMIT, self.url)
        if not opts.verbose:
            cmd += ' -q'

        s = sp.Popen(cmd, shell=True)
        s.communicate()

class BHS(object):
    """This holds all projects, as list, plus general info."""

    TITLE = {
        'nhosts' : {
            'total':'Total hosts',
            'speed':'Daily increase in number of hosts',
        },
        'credit' : {
            'total':'Accumulated credit',
            'speed':'Daily Credit Generation Rate',
        }
    }
    LOGDIR = os.path.join(os.environ['HOME'], ".LOGs", "boinc")

    # Constructor:
    def __init__(self, opts, conf, logger):
        self.opts = opts
        self.logger = logger

        self.pdict = {}
        self.name2key = {} # dict of "project name" (SETI@home) -> "project key" (seti)
        self.ref_time = datetime.datetime(1970, 1, 1) # reference time
        self.__oldest_project = None
        
        # Populate projects:
        for k, v in [(k, v) for k, v in conf.items() if v["active"]]:
            self.pdict[k] = Project(n=v["name"], k=k, u=v["url"], s=v["s"])
            self.name2key[v["name"]] = k


    # Public methods:
    def make_plot(self, what):
        """Plot data of file fn."""

        fmt = '{0}.{1}.dat'
        if self.opts.recent:
            fmt = '{0}_active.{1}.dat'

        fn = fmt.format(self.project.name, what)
        fn = os.path.join(self.LOGDIR, fn)

        X = [] # x axis (time)
        Y = [ [], [], [], [] ] # values for Windows, Linux, Darwin (Max) and other

        # Collect info:
        with open(fn) as f:
            for line in f:
                aline = [ int(x) for x in line.split() ]
                dt = datetime.timedelta(seconds=int(aline[0]))
                t = self.ref_time + dt
                X.append(t)
                for i in range(4):
                    Y[i].append(aline[i+1])
  
        # Plot:
        plt.figure(0, figsize=(13,8), dpi=100)
        for ycol in Y:
            plt.plot(X, ycol)
        wt = self.TITLE[what]["total"]
        plt.title(wt)
        plt.xlabel("Date")
        plt.ylabel(wt)
        plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
        plt.show()

    def distile_stats(self, file='host.gz', recent=False):
        """The "recent" flag selects host active in the last "recent" days (rpc_time greater
        than (date +%s - 30*86400)). If set to False, all computers are counted.
        """
        now = (datetime.datetime.now() - self.ref_time).total_seconds()
        now = int(now)
  
        self.logger.debug('Processing retrieved stats file...')
  
        credit = 0
        os_list = ['win', 'lin', 'dar', 'oth']
  
        stat = {}
        for osy in os_list:
            stat[osy] = [0, 0]
  
        pattern = r'total_credit>([^<]+)<';
        search_cre = re.compile(pattern).search
        
        if recent:
            # rpc_time extraction pattern:
            pattern = r'rpc_time>([^<]+)<';
            search_rpc = re.compile(pattern).search
  
            # rpc threshold:
            rpc_threshold = now - 30*86400 # 30 being the number of days to look back
    
            # Distile file with Unix and connect to process:
            with os.popen('zcat host.gz | grep -F -e total_credit -e os_name -e rpc_time') as f:
                current_os = None
                get_credit = True
                for line in f:
                    if get_credit:
                        credit = float(search_cre(line).group(1))
                        get_credit = False
                        get_os = True
                    elif get_os:
                        if 'Windows' in line:
                            current_os = 'win'
                        elif 'Linux' in line:
                            current_os = 'lin'
                        elif 'Darwin' in line:
                            current_os = 'dar'
                        else:
                            current_os = 'oth'
                        get_os = False
                        get_rpc = True
                    elif get_rpc:
                        rpc_t = float(search_rpc(line).group(1))
                        if rpc_t > rpc_threshold:
                            stat[current_os][0] += 1
                            stat[current_os][1] += credit
                        get_rpc = False
                        get_credit = True
        else:
            # Distile file with Unix and connect to process:
            with os.popen('zcat host.gz | grep -F -e total_credit -e os_name') as f:
                odd = True
                for line in f:
                    if odd:
                        credit = float(search_cre(line).group(1))
                        odd = False
                    else:
                        odd = True
                        if 'Windows' in line:
                            stat['win'][0] += 1
                            stat['win'][1] += credit
                        elif 'Linux' in line:
                            stat['lin'][0] += 1
                            stat['lin'][1] += credit
                        elif 'Darwin' in line:
                            stat['dar'][0] += 1
                            stat['dar'][1] += credit
                        else:
                            stat['oth'][0] += 1
                            stat['oth'][1] += credit
  
        # Return output:
        nstring = "{0:12d}".format(now) # string containing number of hosts info (nhosts)
        cstring = nstring # string containing amount of credit info (credit)
        for osy in os_list:
            nstring += "{0:9.0f} ".format(stat[osy][0])
            try:
                cstring += "{0:15.0f} ".format(stat[osy][1])
            except:
                print(osy, stat[osy])
  
        return nstring, cstring

    def save_log(self, stringa, stringb, recent=False):
        """Save log."""

        self.logger.info('Saving log...')
      
        if not re.search('\n',stringa):
            stringa += '\n'

        if not re.search('\n',stringb):
            stringb += '\n'

        # Number of hosts:
        fn = '{s.project.name}.nhosts.dat'.format(s=self)
        if recent:
            fn = '{s.project.name}_active.nhosts.dat'.format(s=self)

        fn = os.path.join(self.LOGDIR, fn)
        with open(fn, 'a') as f:
            f.write(stringa)
      
        # Amount of credit:
        fn = '{s.project.name}.credit.dat'.format(s=self)
        if recent:
            fn = '{s.project.name}_active.credit.dat'.format(s=self)

        fn = os.path.join(self.LOGDIR, fn)
        with open(fn, 'a') as f:
            f.write(stringb)
      
        # Log entry:
        logfile = "entries.log"
        if recent:
            logfile = "entries_active.log"

        now = datetime.datetime.now()
        hourday = datetime.datetime.strftime(now, '%H:%M:%S on %Y.%m.%d')
        stringc = '{s.project.name:16} logged at {h}\n'.format(s=self, h=hourday)

        fn = os.path.join(self.LOGDIR, logfile)
        with open(fn, 'a') as f:
            f.write(stringc)


    # Public properties:
    @property
    def pkey(self):
        """Project key name (e.g. "seti")."""

        if self.opts.project:
            return self.opts.project
        else:
            return self.next_project

    @property
    def project(self):
        """Return Project object corresponding to self.pkey."""

        return self.pdict[self.pkey]

    @property
    def next_project(self):
        """Read a log file to see which was the project logged longest ago, and log it,
        according to an internal list of the projects with the flag "log=True".
        """
        if not self.__oldest_project:
            logfile = os.path.join(self.LOGDIR, 'entries.log')

            latest = {} # dict: project name -> latest time it was logged
            with open(logfile) as f:
                for line in f:
                    if "logged at" in line:
                        pname, _, _, hour, _, day = line.split()
                        t = datetime.datetime.strptime(day+' '+hour, '%Y.%m.%d %H:%M:%S')

                        if pname in self.name2key:
                            pkey = self.name2key[pname]
                            latest[pkey] = max(latest.get(pkey, t), t)

            plist = sorted([ [t, pk] for pk, t in latest.items() if pk in self.pdict ])
            for t, pkey in plist:
                string = '{t:%Y-%m-%d %H:%M} {k}'.format(t=t, k=pkey)
                self.logger.debug(string)

            self.__oldest_project = plist[0][1]

        return self.__oldest_project

