import re
import os
import sys
import pylab
import datetime
import subprocess as sp

#--------------------------------------------------------------------------------#

class Project(object):

    def __init__(self,n=None,u=None,l=False,s=[]):
        self.name = n
        self.url  = 'http://' + u
        self.log  = l

        # stats is a 4-element list, with the values of last logged
        # Mcredit, kHosts, kDCGR and DINH (see code for explanations)
        # stats has no real value at all.
        self.stats = s

    def get_hostgz(self, opts, bwlimit=100):
        '''Retrieve the host.gz file from the URL.'''

        if (opts.verbose):
            print('Retrieving stats file...')

        cmd = 'wget --limit-rate={0:d}k {1} -O host.gz'.format(bwlimit, self.url)
        if not opts.verbose:
            cmd += ' -q'

        s = sp.Popen(cmd, shell=True)
        s.communicate()


class BHS(object):
    '''This holds all projects, as list, plus general info.'''

    def __init__(self, opts):
        self.ref_time = datetime.datetime(1970,1,1) # reference time
        self.opts = opts
        self.pdict = {}
        self.pkey = opts.project # selected project key (e.g. "seti" for SETI@Home)
        self.title = { 
                'nhosts' : { 
                    'total':'Total hosts',
                    'speed':'Daily increase in number of hosts'
                    },
                'credit' : {
                    'total':'Accumulated credit',
                    'speed':'Daily Credit Generation Rate'
                    }
                }
        self.bwlimit = 250 # bandwidth limit for download, in kB/s
        self.name2key = {} # dict of "project name" (SETI@home) -> "project key" (seti)

    def populate(self, dict):
        for pkey, val in dict.items():
            self.pdict[pkey] = Project(n=val["name"], u=val["url"], l=val["log"], s=val["s"])
            self.name2key[val["name"]] = pkey

    @property
    def project(self):
        '''Return Project object corresponding to self.pkey.'''

        return self.pdict[self.pkey]

    def next_project(self):
        '''Read a log file to see which was the project logged longest ago, and log it,
        according to an internal list of the projects with the flag "log=True".'''

        logfile = os.path.join(os.environ['HOME'], '.LOGs', 'boinc', 'entries.log')

        ago = {} # dict: project name -> seconds ago logged last:
        now = datetime.datetime.now()
        with open(logfile) as f:
            for line in f:
                if "logged at" in line:
                    pname, kk, kk, hour, kk, day = line.split()
                    pname = str(pname)
                    pkey = self.name2key[pname]
                    if not pkey in ago:
                        ago[pkey] = 99999999
                    t = datetime.datetime.strptime(day+' '+hour, '%Y.%m.%d %H:%M:%S')
                    dt = now - t
                    dt = dt.days*86400 + dt.seconds
                    if dt < ago[pkey]:
                        ago[pkey] = dt

        max_ago = 0
        max_name = None
        for pkey, seconds_ago in ago.items():
            # Ignore inactive projects:
            if self.pdict[pkey].log:
                # Save up the one last logged the longest ago:
                if seconds_ago > max_ago:
                    max_name = pkey
                    max_ago = seconds_ago

        self.pkey = max_name
        self.next_ago = max_ago/86400.

    def get_hostgz(self):
        self.project.get_hostgz(self.opts, self.bwlimit)

    def make_plot(self, what):
        '''Plot data of file fn.'''

        fmt = '{0}.{1}.dat'
        if self.opts.recent:
            fmt = '{0}_active.{1}.dat'
        fn = fmt.format(self.project.name, what)
        fn = os.path.join(os.environ['HOME'], ".LOGs", "boinc", fn)

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
        pylab.figure(0, figsize=(13,8), dpi=100)
        for ycol in Y:
            pylab.plot(X, ycol)
        wt = self.title[what]["total"]
        pylab.title(wt)
        pylab.xlabel("Date")
        pylab.ylabel(wt)
        pylab.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
        pylab.show()

    def distile_stats(self, file=None, recent=False):
        '''The "recent" flag selects host active in the last "recent" days (rpc_time greater
        than (date +%s - 30*86400)). If set to False, all computers are counted.'''
        
        now = (datetime.datetime.now() - self.ref_time).total_seconds()
        now = int(now)
  
        if file == None:
            sys.exit("bhs.host_stats: Need a file name to process!")
  
        if self.opts.verbose:
            print('Processing retrieved stats file...')
  
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

    def save_log(self, logfile, stringa, stringb):
        if self.opts.verbose:
            print('Saving log...')
      
        if not re.search('\n',stringa): stringa += '\n'
        if not re.search('\n',stringb): stringb += '\n'
      
        logdir = os.path.join(os.environ['HOME'], '.LOGs', 'boinc')
      
        # Number of hosts:
        fn = '{0}.nhosts.dat'.format(self.project.name)
        fn = os.path.join(logdir, fn)
        with open(fn, 'a') as f:
            f.write(stringa)
      
        # Amount of credit:
        fn = '{0}.credit.dat'.format(self.project.name)
        fn = os.path.join(logdir, fn)
        with open(fn, 'a') as f:
            f.write(stringb)
      
        # Log entry:
        pname = self.project.name.replace('_active','')
        now = datetime.datetime.now()
        hourday = datetime.datetime.strftime(now, '%H:%M:%S on %Y.%m.%d')
        stringc = '{0:16} logged at {1}\n'.format(pname, hourday)
        fn = os.path.join(logdir,logfile)
        with open(fn, 'a') as f:
            f.write(stringc)


#--------------------------------------------------------------------------------#
