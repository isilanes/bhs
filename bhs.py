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

svn_revision = r2 (2008-03-10 00:42:14)

'''

import re
import sys
import os
import optparse
import copy

# Read arguments:
parser = optparse.OptionParser()

parser.add_option("-p", "--project",
                  dest="project",
                  help="Retrieve info from project PROJECT. For a list, use --project=help",
		  default='malaria')

parser.add_option("-r", "--retrieve",
                  help="Retrieve data, instead of just ploting logged values. Default: don't retrieve.",
		  action="store_true",
		  default=False)

parser.add_option("-v", "--verbose",
                  dest="verbose",
                  help="Be verbose. Default: don't be.",
		  action="store_true",
		  default=False)

(o,args) = parser.parse_args()

# Functions:

def now():
  '''
  Return current time, in seconds since epoch format.
  '''
  date = datetime.datetime.now()

  return time.mktime(date.timetuple())

def myopen(fname,mode='r'):
  '''
  Opens a file, checking whether it's gzipped or not, and acts accordingly.
    fname = name of file to open
    mode  = mode in which to open
  '''
  
  fname = fname.replace('.gz','') # rm trailing .gz, if any
  try:
    f = open(fname,mode)
  except:
    try:
      f = gzip.open(fname+'.gz',mode)
    except IOError:
      sys.exit('Could not open file \'' + fname + '\', sorry!')

  return f

def w2file(fname,string):
  '''
  Use myopen to open file, write a string to it and then close it.
    fname  = name of file to write to
    string = string to write to file
  '''
  
  f = myopen(fname,'w')
  f.write(string)
  f.close()

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
  nstring = "%12i" % (now())
  cstring = nstring
  for osy in os_list:
    nstring += "%9.0f "  % (stat[osy][0])
    try:
      cstring += "%15.0f " % (stat[osy][1])
    except:
      print osy,stat[osy]

  return nstring,cstring

def get_log(url,name):
  '''
  Retrieve the log file from the URL.
  '''

  if o.verbose:
    os.system("wget "+url+name)
  else:
    os.system("wget -q "+url+name)

def save_log(project,stringa,stringb):

  if not re.search('\n',stringa): stringa += '\n'
  if not re.search('\n',stringb): stringb += '\n'

  fn = os.environ['HOME']+'/.LOGs/boinc/'+project+'.nhosts.dat'
  f = myopen(fn,'a')
  f.write(stringa)
  f.close()

  fn = os.environ['HOME']+'/.LOGs/boinc/'+project+'.credit.dat'
  f = myopen(fn,'a')
  f.write(stringb)
  f.close()

def make_plot(fn,type):
  '''
  Generate plot data from raw data.
    fn   = name of file with raw data.
    type = whether to get direct values (total), numerical approx. to d/dt (speed) or d2/dt2 (accel).
  '''

  parf = os.environ['HOME']+'/.LOGs/boinc/boinc.par'

  f = myopen(fn,'r')
  lines = f.readlines()
  f.close()

  out_string = ''

  if type == 'total':
    for line in lines:
      line   = [float(x) for x in line.split()]

      tot = 0
      for x in line[1:]:
        tot += x

      if tot != 0:
        val = [0.0,0.0,0.0,0.0,0.0]
        for i in range(1,5):
          val[i] = 100*line[i]/tot

        out_string += "%8.3f %6.2f %6.2f %6.2f %6.2f\n" % tuple( [(line[0]-t0)/86400 , val[1], val[2], val[3], val[4]] )

  elif type == 'speed':
    oline  = [0.0,0.0,0.0,0.0,0.0]

    for line in lines:
      line   = [float(x) for x in line.split()]
      dline  = [line[i]  - oline[i]  for i in range(len(line))]

      tot = 0
      for x in dline[1:]:
        tot += x

      if tot != 0:
        val  = [0.0,0.0,0.0,0.0,0.0]
        for i in range(1,5):
          val[i] = 100*dline[i]/tot
 
          if val[i] < 0:
	    val[i] = 0
	  elif val[i] > 100:
	    val[i] = 100

        out_string += "%8.3f %6.2f %6.2f %6.2f %6.2f\n" % tuple( [(line[0]-t0)/86400 , val[1], val[2], val[3], val[4]] )

      oline  = copy.deepcopy(line)

  elif type == 'accel':
    oline  = [0.0,0.0,0.0,0.0,0.0]
    odline = copy.deepcopy(oline)
    
    for line in lines:
      line   = [float(x) for x in line.split()]
      dline  = [line[i]  - oline[i]  for i in range(len(line))]
      ddline = [dline[i] - odline[i] for i in range(len(line))]

      tot = 0
      for x in ddline[1:]:
        tot += x
    
      val  = [0.0,0.0,0.0,0.0,0.0]
      for i in range(1,5):
        val[i] = 100*ddline[i]/tot

	if val[i] < 0:
	  val[i] = 0
	elif val[i] > 100:
	  val[i] = 100

      out_string += "%8.3f %6.2f %6.2f %6.2f %6.2f\n" % tuple( [(line[0]-t0)/86400 , val[1], val[2], val[3], val[4]] )

      oline  = copy.deepcopy(line)
      odline = copy.deepcopy(dline)

  subtit = title[t][type]

  units = ['','k','M','G']
  stot = tot
  iu   = 0
  while stot > 10000:
    stot = stot / 1000
    iu += 1

  subtit = " %s: %i %s" % (subtit,stot,units[iu])

  tit = name[o.project]

  w2file(tmpf,out_string)
  os.system(xmgr+" -noask -nxy "+tmpf+' -p '+parf+' -pexec \'SUBTITLE "'+subtit+'"\' -pexec \'TITLE "'+tit+'"\'')
  os.unlink(tmpf)

# Define variables:

logf  = 'host.gz'

name  = { 'malaria':'MalariaControl',
              'qmc':'QMC@home',
             'seti':'SETI@home' }

url   = { 'malaria':'http://www.malariacontrol.net/stats/',
              'qmc':'http://qah.uni-muenster.de/stats/',
             'seti':'http://setiathome.berkeley.edu/stats/' }

title = { 'nhosts':{ 'total':'Total hosts',
           'speed':'Daily increase in number of hosts' },

          'credit':{ 'total':'Accumulated credit',
           'speed':'Daily Credit Generation Rate',
           'accel':'CGR increase per day'} }

if o.project == 'help':

  shelp = 'Currently available projects:\n'

  for p,pu in url.iteritems():
    shelp += '  %-10s (%-1s)\n' % (p,pu)

  sys.exit(shelp)

if o.retrieve:
  # Retrieve, process, save, rm:

  if (o.verbose):
    print 'Retrieving stats file...'

  get_log(url[o.project],logf)

  if (o.verbose):
    print 'Processing retrieved stats file...'

  (nstring,cstring) = host_stats(logf)

  if (o.verbose):
    print 'Saving log...'

  save_log(name[o.project],nstring,cstring)

  if (o.verbose):
    print 'Deleting hosts.gz...'

  os.unlink(logf)

  if (o.verbose):
    print 'Finished.'

else:
  # Plot:

  t0   = 1201956633
  tmpf = 'boinc.tmp'
  xmgr = 'xmgrace -barebones -geom 1000x800 -fixed 650 500 '

  for type in ['total','speed']:
    t = 'credit'
    fn =  os.environ['HOME']+'/.LOGs/boinc/'+name[o.project]+'.'+t+'.dat'
    make_plot(fn,type)

  for type in ['total','speed']:
    t = 'nhosts'
    fn =  os.environ['HOME']+'/.LOGs/boinc/'+name[o.project]+'.'+t+'.dat'
    make_plot(fn,type)
