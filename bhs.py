#!/usr/bin/python2
# coding=utf-8

# BOINC Host Statistics
# (c) 2008-2014, Iñaki Silanes
# 
# LICENSE
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License (version 2), as
# published by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details (http://www.gnu.org/licenses/gpl.txt).
# 
# DESCRIPTION
# 
# It retrieves some stat file(s) from some BOINC project(s), and counts how many 
# hosts running it are Windows, Linux, BSD or Darwin (Mac OS X), and how much credit
# is each of them yielding.
# 
# USAGE
# 
# For help, type:
# 
# % bhs.py -h
# 

import re
import sys
import os
import optparse

sys.path.append(os.environ['HOME']+'/git/pythonlibs')
sys.path.append('/usr/lib/python2.7/site-packages')

import DataManipulation as DM
import FileManipulation as FM
import System as S
import WriteXMGR as WX
import Time as T

#--------------------------------------------------------------------------------#

class prj(object):

    def __init__(self,n=None,u=None,l=False,s=[]):
        self.name = n
        self.url  = 'http://'+u
        self.log  = l

        # stats is a 4-element list, with the values of last logged
        # Mcredit, kHosts, kDCGR and DINH (see code for explanations)
        # stats has no real value at all.
        self.stats = s

    def get_hostgz(self):
        '''Retrieve the host.gz file from the URL.'''

        if (o.verbose):
            print 'Retrieving stats file...'

        # Limit bw usage, in KiB/s:
        bwlimit = 100

        if o.verbose:
            cmnd = 'wget --limit-rate=%ik    %s -O host.gz' % (bwlimit,self.url)

        else:
            cmnd = 'wget --limit-rate=%ik -q %s -O host.gz' % (bwlimit,self.url)

        S.cli(cmnd)


#--------------------------------------------------------------------------------#

########################################################
#                                                      #
#  Data to supply by user. Project lists and so forth  #
#                                                      #
########################################################

p = {                                        
 'poem'      : prj(n='POEM@home',      u='boinc.fzk.de/poem/stats/host.gz',               l=True,  s=[  388,   28,  1247,   35]),
 'malaria'   : prj(n='MalariaControl', u='www.malariacontrol.net/stats/host.gz',          l=True,  s=[  429,   60,   963,   40]),
 #'qmc'       : prj(n='QMC@home',       u='qah.uni-muenster.de/stats/host.gz',             l=True,  s=[ 1409,   74,  2185,   67]),
 'spinh'     : prj(n='Spinhenge',      u='spin.fh-bielefeld.de/stats/host.gz',            l=True,  s=[  547,  103,  1039,   97]),
 'rosetta'   : prj(n='Rosetta@home',   u='boinc.bakerlab.org/rosetta/stats/host.gz',      l=True,  s=[ 5199,  648,  7546,  502]),
 'einstein'  : prj(n='Einstein@home',  u='einstein.phys.uwm.edu/stats/host_id.gz',        l=True,  s=[ 9357,  723, 13000,  849]),
 'seti'      : prj(n='SETI@home',      u='setiathome.berkeley.edu/stats/host.gz',         l=True,  s=[36000, 2135, 55000, 1201]),
 'civis'     : prj(n='IBERCIVIS',      u='ibercivis.es/stats/host.gz',                    l=False, s=[]),
 'milky'     : prj(n='MilkyWay@home',  u='milkyway.cs.rpi.edu/milkyway/stats/host.gz',    l=True,  s=[]),
 'abc'       : prj(n='ABC@home',       u='abcathome.com/stats/host.gz',                   l=True,  s=[]),
 'prime'     : prj(n='PrimeGrid',      u='www.primegrid.com/stats/host.gz',               l=True,  s=[]),
 'riesel'    : prj(n='RieselSieve',    u='boinc.rieselsieve.com/stats/host_id.gz',        l=False, s=[]),
 'predictor' : prj(n='Predictor@home', u='predictor.chem.lsa.umich.edu/stats/host_id.gz', l=False, s=[]),
 'lhc'       : prj(n='LHC@home',       u='lhcathome.cern.ch/lhcathome/stats/host.gz',     l=False, s=[  213,  185,   152,  161]),
 }

########################################################
#                                                      #
#           End data to supply by user                 #
#                                                      #
########################################################

# Read arguments:
parser = optparse.OptionParser()

parser.add_option("-P", "--png",
                  dest='png',
                  help="Make plots non-interactively, and save them as PNG.",
		  action="store_true",
		  default=False)

parser.add_option("-p", "--project",
                  dest="project",
                  help="Retrieve info from project PROJECT. For a list, use --project=help",
		  default='malaria')

parser.add_option("-r", "--retrieve",
                  help="Retrieve data, instead of ploting logged values. Default: don't retrieve.",
		  action="store_true",
		  default=False)

parser.add_option("-v", "--verbose",
                  help="Be verbose. Default: don't be.",
		  action="count",
		  default=0)

parser.add_option("-a", "--analize",
                  help="Instead of plotting, guess which OS will overtake Windows, and when.",
		  action="store_true",
		  default=False)

parser.add_option("-T", "--total",
                  help="Plot total figures, instead of percents. Default: percents.",
		  action="store_true",
		  default=False)

parser.add_option("-n", "--next",
                  help="If true, check what was last project logged, and log the next one in internal list. Implies -r. Default: False.",
		  action="store_true",
		  default=False)

parser.add_option("-s", "--smooth",
                  help="For rate plots (in contrast to instantaneous data ones), use last [i-SMOOTH,i] data points for averaging at ith point. Default: 1.",
		  default=1)

parser.add_option("-R", "--recent",
                  help="Count and log also active hosts (those reporting results in the last 30 days). Default: count and log only all hosts.",
		  action="store_true",
		  default=False)

parser.add_option("-y", "--dryrun",
                  help="Perform a dry run: just tell what would be done, but don't do it. Default: real run (plotting, if nothing else is specified).",
		  action="store_true",
		  default=False)

(o,args) = parser.parse_args()

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

#--------------------------------------------------------------------------------#

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


def make_plot_new(fn,type,t='total'):
  '''
  Plot results with Xmgrace, using Thomas's WriteXMGR module.
    fn   = file name of data file
    type = whether you want raw values ('total') or their (approx. numeric) derivative vs. time ('speed')
  '''

  [datastr,tot,world] = proc_data(fn,type)

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
  '''
  Rounds a number to multiples of a rounder, and returns it.
    number  = number to round
    rounder = number the rounded number should be multiple of
    up      = whether to round up (true) or down (false)
  '''

  remainder = number % rounder
  rounded   = (number - remainder) / rounder
  rounded   = rounded*rounder

  if up:
    rounded += rounder

  return rounded 


def make_plot(fn,type):
  '''
  Plot results with Xmgrace, either interactively or saving to a PNG file.
    fn   = file name of data file
    type = whether you want raw values ('total') or their (approx. numeric) derivative vs. time ('speed')
  '''

  [out_string,tot,world] = proc_data(fn,type)

  subtit = title[t][type]

  units = ['','k','M','G']
  stot = tot
  iu   = 0
  while stot > 10000:
    stot = stot / 1000
    iu += 1

  subtit = " %s: %i %s" % (subtit,stot,units[iu])

  tit = p[o.project].name

  FM.w2file(tmpf,out_string)

  if o.png:
    fout = fn.replace('.dat','_'+type+'.png')
    fout = fout.replace('@','_at_')

  if o.total:
    parf = os.environ['HOME']+'/.LOGs/boinc/boinc_total.par'

    ticks = []
    scale = []
    for w in world:
      n = 0
      while (w > 10000):
        w  = w/1000
	n += 3
      w = int(w)/10 + 1
      ticks.append(w)
      scale.append(10**n)

    # Rescale data:
    out_string = ''
    a = FM.file2array(tmpf)
    for line in a:
      aline = line.split()
      nline = "%10.5f " % (float(aline[0])/scale[0])
      for e in aline[1:]:
        nline += "%.6f " % (float(e)/scale[1])
      out_string += nline+'\n'
    FM.w2file(tmpf,out_string)

    world = [10*x for x in ticks]
    yscale = "x 10\S%s" % (len(str(scale[1]))-1)

    pexec = [' -pexec \'SUBTITLE "{0}"\' '.format(subtit)]
    pexec.append('\'TITLE "{0}"\''.format(tit))
    pexec.append('\'yaxis  label "{0}"\' '.format(yscale))
    pexec.append('"yaxis  tick major {0}"'.format(ticks[1]))
    pexec.append('"world ymax {0}"'.fomat(world[1]))

  else:
    parf   = os.environ['HOME']+'/.LOGs/boinc/boinc.par'
    pexec = ['\'SUBTITLE "{0}"\''.format(subtit),'\'TITLE "{0}"\''.format(tit)]

  if o.png:
    DM.xmgrace([tmpf],parf,pexec=pexec,fn=fout)

  else:
    DM.xmgrace([tmpf],parf,pexec=pexec)

  os.unlink(tmpf)


def proc_data(fn,type):
  '''
  Process data and generate output string to plot or analize.
  '''

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

      if o.total:
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

    smooth_n = int(o.smooth)

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

      if o.total:
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


def fit_n_cross(fn,type='total',order=1,npoints=5):
  '''
  Use polynomial of N-order to fit curves, and then find crossing.
    fn    = name of file to get info from
    type  = type of data
    order = N of N-order polynomial
  '''

  # Get last "npoints" points only:
  fntail = '%s.tailed' % (fn)
  cmnd = 'tail --lines=%i %s > %s' % (npoints,fn,fntail)
  S.cli(cmnd)
  s = proc_data(fntail,type)
  os.unlink(fntail)

  ars   = s[0].split('\n')
  begin = float(ars[0].split()[0])
  end   = float(ars[-2].split()[0])

  params = []
  rpar   = []

  for i in [1,2,3]:
    data = ''
    for line in ars:
      if line != '':
        aline = line.split()
        data += aline[0]+' '+aline[i]+'\n'

    form = 'y = a0 '
    for d in range(order):
      n = d + 1
      form += ' + a'+str(n)+'*x^'+str(n)+' '

    form = form.replace('^1 ',' ')

    [par,r] = DM.xmgrace_fit(data,form)
    params.append(par[0:order+1])
    rpar.append(float(r))

  so = ['Linux']
  for i in range(len(so)):
    i    = i + 1
    txt  = 'clear all;\n'
    txt += 'function rval = f1(x)\n'

    for d in range(order+1):
      txt += '  A'+str(d)+' = '+str(params[0][d])+';\n'

    t = form.replace('a','A')
    t = t.replace('y =','')
    txt += '  rval = '+t+';\n'
    txt += 'endfunction\n'
    
    txt += 'function rval = f2(x)\n'

    for d in range(order+1):
      parid = str(params[i][d])
      txt += '  B'+str(d)+' = '+parid+';\n'

    t = form.replace('a','B')
    t = t.replace('y =','')
    txt += '  rval = '+t+';\n'
    txt += 'endfunction\n'

    txt += 'function rval = cross(x)\n'
    txt += '  rval = f1(x) - f2(x);\n'
    txt += 'endfunction\n'

    txt += '[xx,info] = fsolve("cross",1000);\n'
    txt += 'time  = xx/1\n'
    txt += 'error = info\n'
    txt += 'perc  = f1(time)\n'

    FM.w2file('octave.tmp',txt)
    out = S.cli('/usr/bin/octave -q octave.tmp',1).split('\n')
    os.unlink('octave.tmp')

    # Print output:
    print "%3i points: " % (npoints),

    # Will ever cross? (error):
    time  = float(out[0].split()[2])
    error = float(out[1].split()[2])
    perc  = float(out[2].split()[2])
    if (abs(error) > 0.01 or perc < 0 or perc > 100 or time < 0):
      print "%-6s will never cross Windows!" % (so[i-1])

    else:
      time_sec  = time*24*3600
      date_sec  = t0 + time_sec
      now_sec   = float(S.cli('date +\%s',1).split('\n')[0])
      elap_sec  = date_sec - now_sec
      elap_days = elap_sec/(24*3600)
      if elap_days < 3650:
        date = S.cli('date -d "+%i days" +%%F' % (elap_days),1).split('\n')[0].replace('\n','')
      else:
        date = '***'
      frac = 100.0*(end-begin)/time

      if elap_days > 3650:
        forecast = '%5.1f years ' % (elap_days/365.0)

      elif elap_days > 90:
        forecast = '%5.1f months' % (elap_days/30.0)

      else:
        forecast = '%5.1f days  ' % (elap_days)

      print "%-6s will cross Windows in %s (%s) R = %8.6f | C = %5.1f%%" % (so[i-1], forecast, date, rpar[i-1], frac)


def last_perc(fn):
  '''
  Return the last share percents.
  '''

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


def next_project(p=None, logfile=os.environ['HOME']+'/.LOGs/boinc/entries.log'):
  '''Read a log file to see which was the project logged longest ago, and log it,
  according to an internal list of the projects with the flag "log=True".'''

  # Reverse dictionary of p:
  rev_p = {}
  for item in p:
    rev_p[p[item].name] = item

  # Dic: project -> how long ago logged
  ago = {}
  for k in p:
    if p[k].log:
      ago[k] = -1

  # Get reverse list of all log lines:
  loglist = FM.file2array(logfile)
  loglist.reverse()
  
  # Read list and populate "ago":
  for line in loglist:

    pname = line.split()[0]

    if rev_p.has_key(pname):
      rp = rev_p[pname]
      if p[rp].log:
        if ago[rp] < 0:
	  agon    = line.split()[-1]
	  ago[rp] = T.days_ago(agon)

  # Decorate-Sort-Undecorate to sort by value:
  decorated_list = []
  for k in ago:
    kv = [ago[k],k]
    decorated_list.append(kv)

  decorated_list.sort()
  if o.verbose > 1:
    for item in decorated_list:
      print "%3i  %s" % tuple(item)

  dago = 0
  if decorated_list[0][0] == -1:      # if some project(s) hasn't been logged EVER, log it
    nextone = decorated_list[0][1]
  
  else:                               # else, log the one longest ago logged
    nextone = decorated_list[-1][1]
    dago    = decorated_list[-1][0]

  return nextone, dago


#--------------------------------------------------------------------------------#

# Ask not to suspend/hibernate while running:
S.keep_me_up('start','bhs')

if o.dryrun:
  o.verbose += 1

# --- Start with the run thing --- #

title = { 'nhosts':{ 'total':'Total hosts',
                     'speed':'Daily increase in number of hosts' },

          'credit':{ 'total':'Accumulated credit',
                     'speed':'Daily Credit Generation Rate' }
	}

# Help:
if o.project == 'help':

  shelp = 'Currently available projects:\n'

  for pr in sorted(p):
    shelp += '  %-10s %-1s\n' % (pr,p[pr].name)

  sys.exit(shelp)

# Choose project if automatic:
if o.next:
  o.project, dago = next_project(p)

# Actualy run:
if o.dryrun:
  print 'Would select: %s' % (o.project)
  if o.next:
    print "Project last logged: %i days ago" % (dago)

elif o.retrieve:
  if o.verbose:
    print 'Will retrieve: %s' % (o.project)

  # Retrieve host.gz:
  p[o.project].get_hostgz()

  # Process host.gz and save (full version, all machines):
  (nstring,cstring) = host_stats('host.gz')
  save_log(p[o.project].name,'entries.log',nstring,cstring)

  # Process host.gz and save (only recently active machines):
  if o.recent:
    (nstring,cstring) = host_stats('host.gz',True)
    pname = '%s_active' % (p[o.project].name)
    save_log(pname,'entries_active.log',nstring,cstring)

  # Clean up, and say bye:
  if (o.verbose):
    print 'Deleting hosts.gz...'
  
  os.unlink('host.gz')

  if (o.verbose):
    print 'Finished.'

elif o.analize:

  if o.verbose:
    print 'Will analize: %s' % (o.project)

  # Analize:
  t0   = 1201956633
  type = 'total'
  
  for t in ['nhosts']:
    print 'According to '+t+':'
    fn =  '%s/.LOGs/boinc/%s.%s.dat' % (os.environ['HOME'],p[o.project].name,t)
    print last_perc(fn)

    for order in [1]: # order of polynomial fit
      print '\nWith a polynomial of order %i:' % (order)
      for npoints in [2,3,4,5,10,20]: # number of last points to use for fit
        npoints = npoints + order
        fit_n_cross(fn,type,order,npoints)

else:
  # Plot or save PNG

  if o.verbose:
    print 'Will plot: %s' % (o.project)

  t0   = 1201956633
  tmpf = 'boinc.tmp'
  xmgr = 'xmgrace -barebones -geom 1050x900 -fixed 650 500 '

  types = ['total']
  if o.total:
    types.append('speed')

  for type in types:
    for t in ['nhosts','credit']:
      if o.recent:
        fn =  '%s/.LOGs/boinc/%s_active.%s.dat' % (os.environ['HOME'], p[o.project].name, t)

      else:
        fn =  '%s/.LOGs/boinc/%s.%s.dat' % (os.environ['HOME'], p[o.project].name, t)
      make_plot(fn,type)

# Lastly, let the computer suspend/hibernate if it wants to:
S.keep_me_up('stop','bhs')
