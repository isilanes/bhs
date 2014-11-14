import re
import os
import sys
import pylab
import datetime
import subprocess as sp

sys.path.append(os.environ['HOME']+'/git/pythonlibs')
sys.path.append('/usr/lib/python2.7/site-packages')

#import DataManipulation as DM
import FileManipulation as FM
#import System as S
#import WriteXMGR as WX
import Time as T

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

    def get_hostgz(self, opts):
        '''Retrieve the host.gz file from the URL.'''

        if (opts.verbose):
            print('Retrieving stats file...')

        # Limit bw usage, in KiB/s:
        bwlimit = 100

        cmd = 'wget --limit-rate={0:d}k {1} -O host.gz'.format(bwlimit, self.url)
        if not opts.verbose:
            cmd += ' -q'

        s = sp.Popen(cmd, shell=True)
        s.communicate()


class BHS(object):
    '''This holds all projects, as list, plus general info.'''

    def __init__(self, opts):
        self.opts = opts
        self.plist = {}
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

    def populate(self, dict):
        for pname, val in dict.items():
            self.plist[pname] = Project(n=val["name"], u=val["url"], l=val["log"], s=val["s"])

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
                    if not pname in ago:
                        ago[pname] = 99999999
                    t = datetime.datetime.strptime(day+' '+hour, '%Y.%m.%d %H:%M:%S')
                    dt = now - t
                    dt = dt.days*86400 + dt.seconds
                    if dt < ago[pname]:
                        ago[pname] = dt

        pnames = {}
        for k,v in self.plist.items():
            pnames[v.name] = v

        max_ago = 0
        max_name = None
        for pname, seconds_ago in ago.items():
            # Ignore inactive projects:
            if pname in pnames and pnames[pname].log:
                # Save up the one last logged the longest ago:
                if seconds_ago > max_ago:
                    max_name = pname
                    max_ago = seconds_ago

        self.opts.project = max_name
        self.next_ago = max_ago/86400.

    def get_hostgz(self):
        self.opts.project.get_hostgz(self.opts)

    def make_plot(self, fn):
        '''Plot data of file fn.'''

        X = [] # x axis (time)
        W = [] # values for Windows
        L = [] # values for Linux
        D = [] # values for Darwin (Mac)
        O = [] # values for other
        with open(fn) as f:
            for line in f:
                aline = [ int(x) for x in line.split() ]
                t = aline[0]
                tot = sum(aline[1:])
                w, l, d, o = [ x for x in aline[1:] ]
                X.append(t)
                W.append(w)
                L.append(l)
                D.append(d)
                O.append(o)
  
        pylab.figure(0, figsize=(13,8), dpi=100)
        pylab.plot(X, W)
        pylab.plot(X, L)
        pylab.plot(X, D)
        pylab.plot(X, O)
        pylab.show()


#--------------------------------------------------------------------------------#

def host_stats(file=None,recent=False):
  '''The "recent" flag selects host active in the last "recent" days (rpc_time greater
  than (date +%s - 30*86400)). If set to False, all computers are counted.'''

  if file == None:
    sys.exit("bhs.host_stats: Need a file name to process!")

  if (o.verbose):
    print 'Processing retrieved stats file...'

  credit  = 0
  os_list = ['win','lin','dar','oth']

  stat = {}
  for osy in os_list:
    stat[osy] = [0,0]

  pattern    = r'total_credit>([^<]+)<';
  search_cre = re.compile(pattern).search
  
  if recent:
    # rpc_time extraction pattern:
    pattern    = r'rpc_time>([^<]+)<';
    search_rpc = re.compile(pattern).search

    # rpc threshold:
    t_now = T.now()
    rpc_threshold = t_now - 30*86400 # 30 being the number of days to look back

    # Distile file with Unix and connect to process:
    f = os.popen('zcat host.gz | grep -F -e total_credit -e os_name -e rpc_time')

    current_os = None
    get_credit = True
    for line in f:

      if get_credit:
	credit = float(search_cre(line).group(1))

	get_credit = False
	get_os     = True

      elif get_os:
        if 'Windows' in line:
	  current_os = 'win'

        elif 'Linux' in line:
	  current_os = 'lin'
  
        elif 'Darwin' in line:
	  current_os = 'dar'
  
        else:
	  current_os = 'oth'

        get_os  = False
	get_rpc = True

      elif get_rpc:
	rpc_t  = float(search_rpc(line).group(1))
	if rpc_t > rpc_threshold:
	  stat[current_os][0] += 1
	  stat[current_os][1] += credit

        get_rpc    = False
	get_credit = True

    f.close()

  else:
    # Distile file with Unix and connect to process:
    f = os.popen('zcat host.gz | grep -F -e total_credit -e os_name')
  
    odd = True
    for line in f:
      if odd:
        credit = float(search_cre(line).group(1))
        odd    = False
  
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
  
    f.close()

  # Return output:
  nstring = "%12i" % (T.now())  # string containing number of hosts info (nhosts)
  cstring = nstring             # string containing amount of credit info (credit)
  for osy in os_list:
    nstring += "%9.0f "  % (stat[osy][0])
    try:
      cstring += "%15.0f " % (stat[osy][1])
    except:
      print osy,stat[osy]

  return nstring,cstring

def save_log(project,logfile,stringa,stringb):
    if (o.verbose):
        print 'Saving log...'
  
    if not re.search('\n',stringa): stringa += '\n'
    if not re.search('\n',stringb): stringb += '\n'
  
    logdir = '%s/.LOGs/boinc' % (os.environ['HOME'])
  
    # Number of hosts:
    fn = '%s/%s.nhosts.dat' % (logdir, project)
    FM.w2file(fn,stringa,'a')
  
    # Amount of credit:
    fn = '%s/%s.credit.dat' % (logdir, project)
    FM.w2file(fn,stringb,'a')
  
    # Log entry:
    project = project.replace('_active','')
    stringc = "%-16s logged at %10s on %1s\n" % (project,T.hour(),T.day())
    fn      = '%s/%s' % (logdir,logfile)
    FM.w2file(fn,stringc,'a')

def make_plot_new(fn, type, t="total", opts=None):
  '''Plot results with Xmgrace, using Thomas's WriteXMGR module.
    fn   = file name of data file
    type = whether you want raw values ('total') or their (approx. numeric) derivative vs. time ('speed')'''

  [datastr,tot,world] = proc_data(fn, type, opts, t0)

  subtit = title[t][type]

  units = ['','k','M','G']

  stot = tot
  iu   = 0
  while stot > 10000:
    stot = stot / 1000
    iu += 1

  subtit = " %s: %i %s" % (subtit,stot,units[iu])

  tit = p[o.project].name

  miny = 100
  maxy = 0
  xcol = []
  ycol = []
  for line in datastr.split('\n'):
    if line:
      aline = [float(x) for x in line.split()]
      xx = aline[0]
      yy = aline[1]

      if yy > maxy:
        maxy = yy
 
      elif yy < miny:
        miny = yy

      xcol.append(xx)
      ycol.append(yy)

  dy   = int(miny / 10)
  dx   = 30

  miny = round2val(miny,dy)
  maxy = round2val(maxy,dy,True)
  maxx = round2val(xcol[-1],dx,True)

  data  = WX.XYset(xcol,ycol)
  graph = WX.Graph(data)
  graph.SetWorld(xmin=0,ymin=miny,xmax=maxx,ymax=maxy)
  graph.SetYaxis(majorUnit=dy,label='%')
  graph.SetXaxis(majorUnit=dx,label='Days since Feb 3, 2008')
  plot  = WX.Plot(tmpf,graph)
  plot.WriteFile()

  cmnd = '/usr/bin/xmgrace -barebones -geom 975x725 -fixed 600 420 -noask -nxy %s' % (tmpf)
  S.cli(cmnd)

def round2val(number=0,rounder=1,up=False):
  '''Rounds a number to multiples of a rounder, and returns it.
    number  = number to round
    rounder = number the rounded number should be multiple of
    up      = whether to round up (true) or down (false)'''

  remainder = number % rounder
  rounded   = (number - remainder) / rounder
  rounded   = rounded*rounder

  if up:
    rounded += rounder

  return rounded 

def proc_data(fn, type, opts, t0):
  '''Process data and generate output string to plot or analize.'''

  lines = FM.file2array(fn)

  out_string = ''

  max_x = 0
  max_y = 0

  if type == 'total':
    for line in lines:
      line = [float(x) for x in line.split()]

      tot = 0
      for x in line[1:]:
        tot += x
	if x > max_y:
          max_y = x 

      if opts.total:
        val = line

      else:
        if tot != 0:
          val = [0.0,0.0,0.0,0.0,0.0]
          for i in range(1,5):
            val[i] = 100*line[i]/tot

      max_x = (line[0]-t0)/86400
      out_string += "%9.3f %8.4f %8.4f %8.4f %8.4f\n" % tuple( [max_x , val[1], val[2], val[3], val[4]] )

  elif type == 'speed':
    oline  = [0.0,0.0,0.0,0.0,0.0]

    smooth_n = int(opts.smooth)

    for i in range(smooth_n,len(lines)):

      linei = [float(x) for x in lines[i].split()]          # present, ith, line
      liner = [float(x) for x in lines[i-smooth_n].split()] # reference line

      dt   = linei[0] - liner[0]
      dydt = [86400*(linei[j] - liner[j])/dt for j in range(1,len(linei))]

      tot = 0
      for y in dydt:
        tot += y
	if y > max_y:
	  max_y = y

      if opts.total:
        val = [666]
	val.extend(dydt)

      else:
        if tot != 0:
	  val = [None]
	  for j in range(1,5):
	    va = 100*dydt[j]/tot

	    if va < 0:
	      va = 0
	      
	    elif va > 100:
	      va = 100

	    val.append(va)

      max_x       = (linei[0]-t0)/86400
      out_string += "%9.3f %8.4f %8.4f %8.4f %8.4f\n" % (max_x , val[1], val[2], val[3], val[4])

  return [out_string,tot,[max_x,max_y]]

def last_perc(fn):
  '''Return the last share percents.'''

  cmnd = 'tail -1 %s' % (fn)
  line = S.cli(cmnd,1).split('\n')

  vals = [float(x) for x in line[0].split()]
  
  tot = 0
  for v in vals[1:]:
    tot += v

  out_str = '\nLast percents:\n'
  i = 1
  for OS in ['Windows', 'Linux', 'Mac', 'Other']:
    perc     = 100*vals[i]/tot
    out_str += '%10s: %6.2f %%\n' % (OS,perc)
    i       += 1

  return out_str


#--------------------------------------------------------------------------------#
