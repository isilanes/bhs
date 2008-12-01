#!/usr/bin/python
# coding=utf-8

'''
BOINC Host Statistics
(c) 2008, Iñaki Silanes

LICENSE

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License (version 2), as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details (http://www.gnu.org/licenses/gpl.txt).

DESCRIPTION

It retrieves some stat file(s) from some BOINC project(s), and counts how many 
hosts running it are Windows, Linux, BSD or Darwin (Mac OS X), and how much credit
is each of them yielding.

USAGE

For help, type:

% bhs.py -h

VERSION

svn_revision = r21 (2008-12-01 13:24:45)

'''

import re
import sys
import os
import optparse
import copy

sys.path.append(os.environ['HOME']+'/WCs/PythonModules')

import DataManipulation as DM
import FileManipulation as FM
import System as S
import WriteXMGR as WX

#--------------------------------------------------------------------------------#

class project:
  
  def __init__(self,name=None,url=None,logit=False,stats=[]):
    self.name  = name
    self.url   = url
    self.logit = logit

    # stats is a 4-element list, with the values of last logged
    # Mcredit, kHosts, kDCGR and DINH (see code for explanations)
    # stats has no real value at all.
    self.stats = stats

  def get_log(self):
    '''
    Retrieve the log file from the URL.
    '''

    if o.verbose:
      cmnd = 'wget %s -O host.gz'    % (self.url)

    else:
      cmnd = 'wget -q %s -O host.gz' % (self.url)

    S.cli(cmnd)

#--------------------------------------------------------------------------------#

########################################################
#                                                      #
#  Data to supply by user. Project lists and so forth  #
#                                                      #
########################################################

p = {                                        
      'poem'      : project( name = 'POEM@home',      url = 'http://boinc.fzk.de/poem/stats/host.gz',               logit = True,  stats = [  388,   28,  1247,   35] ),
      'malaria'   : project( name = 'MalariaControl', url = 'http://www.malariacontrol.net/stats/host.gz',          logit = True,  stats = [  429,   60,   963,   40] ),
      'qmc'       : project( name = 'QCM@home',       url = 'http://qah.uni-muenster.de/stats/host.gz',             logit = True,  stats = [ 1409,   74,  2185,   67] ),
      'spinh'     : project( name = 'Spinhenge',      url = 'http://spin.fh-bielefeld.de/stats/host.gz',            logit = True,  stats = [  547,  103,  1039,   97] ),
      'lhc'       : project( name = 'LHC@home',       url = 'http://lhcathome.cern.ch/lhcathome/stats/host.gz',     logit = True,  stats = [  213,  185,   152,  161] ),
      'rosetta'   : project( name = 'Rosetta@home',   url = 'http://boinc.bakerlab.org/rosetta/stats/host.gz',      logit = True,  stats = [ 5199,  648,  7546,  502] ),
      'einstein'  : project( name = 'Einstein@home',  url = 'http://einstein.phys.uwm.edu/stats/host_id.gz',        logit = True,  stats = [ 9357,  723, 13000,  849] ),
      'seti'      : project( name = 'SETI@home',      url = 'http://setiathome.berkeley.edu/stats/host.gz',         logit = True,  stats = [36000, 2135, 55000, 1201] ),
      'civis'     : project( name = 'IBERCIVIS',      url = 'http://ibercivis.es/stats/host.gz',                    logit = True,  stats = [] ),
      'milky'     : project( name = 'MilkyWay@home',  url = 'http://milkyway.cs.rpi.edu/milkyway/stats/host.gz',    logit = True,  stats = [] ),
      'abc'       : project( name = 'ABC@home',       url = 'http://abcathome.com/stats/host.gz',                   logit = True,  stats = [] ),
      'prime'     : project( name = 'PrimeGrid',      url = 'http://www.primegrid.com/stats/host.gz',               logit = True,  stats = [] ),
      'riesel'    : project( name = 'RieselSieve',    url = 'http://boinc.rieselsieve.com/stats/host_id.gz',        logit = False, stats = [] ),
      'predictor' : project( name = 'Predictor@home', url = 'http://predictor.chem.lsa.umich.edu/stats/host_id.gz', logit = False, stats = [] ),
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
		  action="store_true",
		  default=False)

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

(o,args) = parser.parse_args()

#--------------------------------------------------------------------------------#

def host_stats(file=None):
  if file == None: sys.exit("bhs.host_stats: Need a file name to process!")

  credit  = 0
  os_list = ['win','lin','dar','oth']

  stat = {}
  for osy in os_list:
    stat[osy] = [0,0]

  pattern    = r'total_credit>([^<]+)<';
  search_cre = re.compile(pattern).search
  
  win_stat_0 = 0
  win_stat_1 = 0
  lin_stat_0 = 0
  lin_stat_1 = 0
  dar_stat_0 = 0
  dar_stat_1 = 0
  oth_stat_0 = 0
  oth_stat_1 = 0

  # Distile file with Unix and connect to process:
  f = os.popen('zcat host.gz | grep -F -e total_credit -e os_name')
  
  odd = True
  for line in f:
  
    if odd:
      cre    = search_cre(line)
      credit = float(cre.group(1))
      odd    = False
  
    else:
      odd = True
      if 'Windows' in line:
        win_stat_0 += 1
        win_stat_1 += credit
  
      elif 'Linux' in line:
        lin_stat_0 += 1
        lin_stat_1 += credit
  
      elif 'Darwin' in line:
        dar_stat_0 += 1
        dar_stat_1 += credit
  
      else:
        oth_stat_0 += 1
        oth_stat_1 += credit
  
  f.close()

  stat['win'] = [win_stat_0,win_stat_1]
  stat['lin'] = [lin_stat_0,lin_stat_1]
  stat['dar'] = [dar_stat_0,dar_stat_1]
  stat['oth'] = [oth_stat_0,oth_stat_1]
  
  # Return output:
  nstring = "%12i" % (S.now())
  cstring = nstring
  for osy in os_list:
    nstring += "%9.0f "  % (stat[osy][0])
    try:
      cstring += "%15.0f " % (stat[osy][1])
    except:
      print osy,stat[osy]

  return nstring,cstring

#--------------------------------------------------------------------------------#

def save_log(project,stringa,stringb):

  if not re.search('\n',stringa): stringa += '\n'
  if not re.search('\n',stringb): stringb += '\n'

  fn = os.environ['HOME']+'/.LOGs/boinc/'+project+'.nhosts.dat'
  FM.w2file(fn,stringa,'a')

  fn = os.environ['HOME']+'/.LOGs/boinc/'+project+'.credit.dat'
  FM.w2file(fn,stringb,'a')

  stringc = "%-15s logged at %10s on %1s\n" % (project,S.hour(),S.day())
  fn = os.environ['HOME']+'/.LOGs/boinc/entries.log'
  FM.w2file(fn,stringc,'a')

#--------------------------------------------------------------------------------#

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

  print dy,miny,maxy

  data  = WX.XYset(xcol,ycol)
  graph = WX.Graph(data)
  graph.SetWorld(xmin=0,ymin=miny,xmax=maxx,ymax=maxy)
  graph.SetYaxis(majorUnit=dy,label='%')
  graph.SetXaxis(majorUnit=dx,label='Days since Feb 3, 2008')
  plot  = WX.Plot(tmpf,graph)
  plot.WriteFile()

  cmnd = '/usr/bin/xmgrace -barebones -geom 975x725 -fixed 600 420 -noask -nxy %s' % (tmpf)
  S.cli(cmnd)

#--------------------------------------------------------------------------------#

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

#--------------------------------------------------------------------------------#

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

  xtra = ' '
  if o.png:
    fout = fn.replace('.dat','_'+type+'.png')
    fout = fout.replace('@','_at_')
    xtra += '-hardcopy -hdevice PNG -pexec \'page size 1920, 1440\' -printfile '+fout

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
    str1 = xmgr+" -noask -nxy "+tmpf+' -p '+parf+' -pexec \'SUBTITLE "'+subtit+'"\' -pexec \'TITLE "'+tit+'"\' -pexec \'yaxis  label "'+yscale+'"\' '
    S.cli(str1+' -pexec "yaxis  tick major '+str(ticks[1])+'" -world 0 0 '+str(world[0])+' '+str(world[1])+xtra)

  else:
    parf = os.environ['HOME']+'/.LOGs/boinc/boinc.par'
    str1 = xmgr+' -noask -nxy '+tmpf+' -p '+parf+' -pexec \'SUBTITLE "'+subtit+'"\' -pexec \'TITLE "'+tit+'"\' '
    S.cli(str1+xtra)

  os.unlink(tmpf)

#--------------------------------------------------------------------------------#

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

    for line in lines:
      line   = [float(x) for x in line.split()]
      dt     = (line[0] - oline[0])/86400
      dline  = [(line[i]  - oline[i])/dt for i in range(len(line))]

      tot = 0
      for x in dline[1:]:
        tot += x
	if x > max_y:
          max_y = x

      if o.total:
        val = dline

      else:
        if tot != 0:
          val  = [0.0,0.0,0.0,0.0,0.0]
          for i in range(1,5):
            val[i] = 100*dline[i]/tot
 
            if val[i] < 0:
	      val[i] = 0

	    elif val[i] > 100:
	      val[i] = 100

      max_x = (line[0]-t0)/86400
      out_string += "%9.3f %8.4f %8.4f %8.4f %8.4f\n" % tuple( [(line[0]-t0)/86400 , val[1], val[2], val[3], val[4]] )

      oline  = copy.deepcopy(line)
  
  return [out_string,tot,[max_x,max_y]]

#--------------------------------------------------------------------------------#

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
    out = S.cli('/usr/bin/octave -q octave.tmp',True)
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
      now_sec   = float(S.cli('date +\%s',True)[0])
      elap_sec  = date_sec - now_sec
      elap_days = elap_sec/(24*3600)
      if elap_days < 10000:
        date = S.cli('date -d "+%i days" +%%F' % (elap_days),True)[0].replace('\n','')
      else:
        date = 'Muuu tarde'
      frac = 100*(end-begin)/time
      print "%-6s will cross Windows in %8.1f days (%s) R = %8.6f | C = %5.1f%%" % (so[i-1], elap_days, date, rpar[i-1], frac)

#--------------------------------------------------------------------------------#

def last_perc(fn):
  '''
  Return the last share percents.
  '''

  cmnd = 'tail -1 %s' % (fn)
  line = S.cli(cmnd,True)

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

def next_project(projs=None, logfile=os.environ['HOME']+'/.LOGs/boinc/last.dat'):
  '''
  Read a log file to see which was the last project logged, and log the next one,
  according to an internal list of the projects with the flag "logit=True".
  '''

  log_those = sorted(projs)

  try:
    lastone = FM.file2array(logfile)
    lastone = lastone[0].replace('\n','')
    check   = False
    if lastone == log_those[-1]:
      nextone = log_those[0]
    else:
      nextone = log_those[-1]

    for p in log_those:

      if check:
        nextone = p
        break

      if p == lastone:
        check = True
        
  except:
    lastone = 'malaria'
    nextone = 'malaria'

  FM.w2file(logfile,nextone+'\n')

  return nextone

#--------------------------------------------------------------------------------#

next_project(p)

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
  o.project  = next_project(p)
  o.retrieve = True

# Actualy run:
if o.retrieve:
  # Retrieve, process, save, rm:

  if (o.verbose):
    print 'Retrieving stats file...'

  print p[o.project].get_log()

  if (o.verbose):
    print 'Processing retrieved stats file...'

  (nstring,cstring) = host_stats('host.gz')

  if (o.verbose):
    print 'Saving log...'

  save_log(p[o.project].name,nstring,cstring)

  if (o.verbose):
    print 'Deleting hosts.gz...'

  os.unlink('host.gz')

  if (o.verbose):
    print 'Finished.'

elif o.analize:
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

  t0   = 1201956633
  tmpf = 'boinc.tmp'
  xmgr = 'xmgrace -barebones -geom 1000x800 -fixed 650 500 '

  types = ['total']
  if o.total:
    types.append('speed')

  for type in types:
    for t in ['credit','nhosts']:
      fn =  '%s/.LOGs/boinc/%s.%s.dat' % (os.environ['HOME'], p[o.project].name, t)
      make_plot(fn,type)
