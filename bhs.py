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

svn_revision = r176 (2008-02-22 18:22:35)

'''

import re
import sys
import os
import optparse
import copy

sys.path.append(os.environ['HOME']+'/WCs/PublishedSoftware/PythonModules')

import DataManipulation as DM
import FileManipulation as FM
import System as S

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

(o,args) = parser.parse_args()

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

def get_log(url):
  '''
  Retrieve the log file from the URL.
  '''

  if o.verbose:
    S.cli('wget '+url+' -O host.gz')

  else:
    S.cli("wget -q "+url+' -O host.gz')

def save_log(project,stringa,stringb):

  if not re.search('\n',stringa): stringa += '\n'
  if not re.search('\n',stringb): stringb += '\n'

  fn = os.environ['HOME']+'/.LOGs/boinc/'+project+'.nhosts.dat'
  f = FM.myopen(fn,'a')
  f.write(stringa)
  f.close()

  fn = os.environ['HOME']+'/.LOGs/boinc/'+project+'.credit.dat'
  f = FM.myopen(fn,'a')
  f.write(stringb)
  f.close()

  stringc = "%-15s logged at %10s on %1s\n" % (project,S.hour(),S.day())
  fn = os.environ['HOME']+'/.LOGs/boinc/entries.log'
  f = FM.myopen(fn,'a')
  f.write(stringc)
  f.close()

def make_plot(fn,type,png=False):
  '''
  Plot results with Xmgrace, either interactively or saving to a PNG file.
    fn   = file name of data file
    type = whether you want raw values ('total') or their (approx. numeric) derivative vs. time ('speed')
    png  = whether to save to PNG files (True) or not.
  '''

  parf = os.environ['HOME']+'/.LOGs/boinc/boinc.par'

  [out_string,tot] = proc_data(fn,type)

  subtit = title[t][type]

  units = ['','k','M','G']
  stot = tot
  iu   = 0
  while stot > 10000:
    stot = stot / 1000
    iu += 1

  subtit = " %s: %i %s" % (subtit,stot,units[iu])

  tit = name[o.project]

  FM.w2file(tmpf,out_string)

  xtra = ''
  if o.png:
    fout = fn.replace('.dat','_'+type+'.png')
    fout = fout.replace('@','_at_')
    xtra += '-hardcopy -hdevice PNG -printfile '+fout

  S.cli(xmgr+" -noask -nxy "+tmpf+' -p '+parf+' -pexec \'SUBTITLE "'+subtit+'"\' -pexec \'TITLE "'+tit+'"\' '+xtra)

  os.unlink(tmpf)

def proc_data(fn,type):
  '''
  Process data and generate output string to plot or analize.
  '''

  f = FM.myopen(fn,'r')
  lines = f.readlines()
  f.close()

  out_string = ''

  if type == 'total':
    for line in lines:
      line = [float(x) for x in line.split()]

      tot = 0
      for x in line[1:]:
        tot += x

      if tot != 0:
        val = [0.0,0.0,0.0,0.0,0.0]
        for i in range(1,5):
          val[i] = 100*line[i]/tot

        out_string += "%9.3f %8.4f %8.4f %8.4f %8.4f\n" % tuple( [(line[0]-t0)/86400 , val[1], val[2], val[3], val[4]] )

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

        out_string += "%9.3f %8.4f %8.4f %8.4f %8.4f\n" % tuple( [(line[0]-t0)/86400 , val[1], val[2], val[3], val[4]] )

      oline  = copy.deepcopy(line)

  return [out_string,tot]

def make_ana(fn,type):
  '''
  Analize data.
  '''

  [out_string,tot] = proc_data(fn,type)

  tmpf2 = 'boinc.tmp2'

  d = [ [0,0], [0,0], [0,0], [0,0] ]

  for ind in [0,1,2]:
    col = ind + 2
    S.cli('echo "'+out_string+'" | awk \'/./{print $1,$'+str(col)+'}\' > '+tmpf2)
    out = S.cli('xmfit '+tmpf2+' -f "y = a0 + a1*x" | grep "a. ="',True)
    for line in out:
      al = line.split()
      if 'a0' in line:
        d[ind][0] = float(al[2])
      elif 'a1' in line:
        d[ind][1] = float(al[2])

  os.unlink(tmpf2)
 
  mincatch = 1000
  minidx   = 0
  for ind in [1,2]:
    catch = (d[0][0] - d[ind][0])/(d[ind][1] - d[0][1])
    catch = catch/365
    if catch > 0 and catch < mincatch:
      mincatch = catch
      minidx   = ind

  so = ['Linux','Mac','Others']

  print "%1s will catch up with Windows in %.1f years from now!\n" % (so[minidx],mincatch)

########################################################
#                                                      #
#  Data to supply by user. Project lists and so forth  #
#                                                      #
########################################################

name  = {                              # Mcredit | kHosts | kDCGR  | DINH
          'malaria':'MalariaControl',  #   239   |   55   |   1010 |   146
              'qmc':'QMC@home',        #   967   |   61   |   3497 |   163
	'predictor':'Predictor@Home ', #   459   |  145   |        |
         'einstein':'Einstein@home',   #  6582   |  518   |        |
          'rosetta':'Rosetta@home',    #  3765   |  542   |        |
             'seti':'SETI@home',       # 26000   | 1876   | 445000 | 11000
	}

url   = { 'malaria':'http://www.malariacontrol.net/stats/host.gz',
              'qmc':'http://qah.uni-muenster.de/stats/host.gz',
             'seti':'http://setiathome.berkeley.edu/stats/host.gz',
          'rosetta':'http://boinc.bakerlab.org/rosetta/stats/host.gz',
	 'einstein':'http://einstein.phys.uwm.edu/stats/host_id.gz',
        'predictor':'http://predictor.chem.lsa.umich.edu/stats/host_id.gz',
	}

########################################################
#                                                      #
#           End data to supply by user                 #
#                                                      #
########################################################

title = { 'nhosts':{ 'total':'Total hosts',
                     'speed':'Daily increase in number of hosts' },

          'credit':{ 'total':'Accumulated credit',
                     'speed':'Daily Credit Generation Rate' }
	}

if o.project == 'help':

  shelp = 'Currently available projects:\n'

  for p,pu in url.iteritems():
    shelp += '  %-10s %-1s\n' % (p,pu)

  sys.exit(shelp)

# Actualy run:
if o.retrieve:
  # Retrieve, process, save, rm:

  if (o.verbose):
    print 'Retrieving stats file...'

  get_log(url[o.project])

  if (o.verbose):
    print 'Processing retrieved stats file...'

  (nstring,cstring) = host_stats('host.gz')

  if (o.verbose):
    print 'Saving log...'

  save_log(name[o.project],nstring,cstring)

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
    fn =  os.environ['HOME']+'/.LOGs/boinc/'+name[o.project]+'.'+t+'.dat'
    s = proc_data(fn,type)

    ars   = s[0].split('\n')
    begin = float(ars[0].split()[0])
    end   = float(ars[-2].split()[0])

    params = []
    for i in [1,2,3]:
      data = ''
      ars = s[0].split('\n')
      for line in ars:
        if line != '':
	  aline = line.split()
          data += aline[0]+' '+aline[i]+'\n'

      [par,r,x0] = DM.xmgrace_fit(data,'y = a0 + a1*x + a2*x^2')
      params.append(par[0:3])

    so = ['Linux','Mac']
    for i in [1,2]:
      txt  = 'clear all;\n'
      txt += 'function rval = f1(x)\n'
      txt += '  A0 = '+params[0][0]+';\n'
      txt += '  A1 = '+params[0][1]+';\n'
      txt += '  A2 = '+params[0][2]+';\n'
      txt += '  rval = A0 + A1.*x + A2*x^2 ;\n'
      txt += 'endfunction\n'
    
      txt += 'function rval = f2(x)\n'
      txt += '  B0 = '+params[i][0]+';\n'
      txt += '  B1 = '+params[i][1]+';\n'
      txt += '  B2 = '+params[i][2]+';\n'
      txt += '  rval = B0 + B1*x + B2*x^2;\n'
      txt += 'endfunction\n'

      txt += 'function rval = cross(x)\n'
      txt += '  rval = f1(x) - f2(x);\n'
      txt += 'endfunction\n'

      txt += '[xx,info] = fsolve("cross",1000);\n'
      txt += 'time  = xx/1\n'
      txt += 'error = info\n'
      txt += 'perc  = f1(time)\n'

      FM.w2file('octave.tmp',txt)
      out = S.cli('/usr/bin/octave -qf octave.tmp',True)
      os.unlink('octave.tmp')
      
      # Will ever cross? (error):
      error = float(out[1].split()[2])
      perc  = float(out[2].split()[2])
      if (abs(error) > 0.01 or perc < 0 or perc > 100):
        print "%-6s will never cross Windows!" % (so[i-1])

      else:
        time = float(out[0].split()[2])
	frac = 100*(end-begin)/time
        print "%-6s will cross Windows in %6.1f days (%7.2f %% confidence)" % (so[i-1],time,frac)

else:
  # Plot or save PNG

  t0   = 1201956633
  tmpf = 'boinc.tmp'
  xmgr = 'xmgrace -barebones -geom 1000x800 -fixed 650 500 '

  for type in ['total','speed']:
    for t in ['credit','nhosts']:
      fn =  os.environ['HOME']+'/.LOGs/boinc/'+name[o.project]+'.'+t+'.dat'
      make_plot(fn,type,o.png)
