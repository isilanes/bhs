#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
BOINC Host Statistics
(c) 2008-2014, Iñaki Silanes

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
'''

import os
import sys
import json
import argparse

from libbhs import core

'''
sys.path.append(os.environ['HOME']+'/git/pythonlibs')
sys.path.append('/usr/lib/python2.7/site-packages')

import DataManipulation as DM
import FileManipulation as FM
import System as S
#import WriteXMGR as WX
import Time as T
'''

#--------------------------------------------------------------------------------#

# ----- Arguments ----- #

# Read arguments:
parser = argparse.ArgumentParser()

parser.add_argument("-P", "--png",
                  dest='png',
                  help="Make plots non-interactively, and save them as PNG.",
		  action="store_true",
		  default=False)

parser.add_argument("-p", "--project",
                  dest="project",
                  help="Retrieve info from project PROJECT. For a list, use --project=help",
		  default='malaria')

parser.add_argument("-r", "--retrieve",
                  help="Retrieve data, instead of ploting logged values. Default: don't retrieve.",
		  action="store_true",
		  default=False)

parser.add_argument("-v", "--verbose",
                  help="Be verbose. Default: don't be.",
		  action="count",
		  default=0)

parser.add_argument("-a", "--analize",
                  help="Instead of plotting, guess which OS will overtake Windows, and when.",
		  action="store_true",
		  default=False)

parser.add_argument("-T", "--total",
                  help="Plot total figures, instead of percents. Default: percents.",
		  action="store_true",
		  default=False)

parser.add_argument("-n", "--next",
                  help="If true, check what was last project logged, and log the next one in internal list. Implies -r. Default: False.",
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

o = parser.parse_args()

if o.dryrun:
    o.verbose += 1

# ----- Configuration ----- #

# Read conf:
fn_conf = os.path.join(os.environ["HOME"], "git", "bhs", "boinc.json")
with open(fn_conf) as f:
    J = json.load(f)

# Populate dictionary with data:
p = {}
for pname, val in J.items():
    p[pname] = core.Project(n=val["name"], u=val["url"], l=val["log"], s=val["s"])

# --- Start with the run thing --- #

title = { 
    'nhosts':{ 'total':'Total hosts',
                     'speed':'Daily increase in number of hosts' },

    'credit':{ 'total':'Accumulated credit',
                     'speed':'Daily Credit Generation Rate' }
	}

# Help:
if o.project == 'help':
    shelp = 'Currently available projects:\n'
    for pr in sorted(p):
        shelp += '    {0:10s} {1}\n'.format(pr,p[pr].name)

    sys.exit(shelp)

# Choose project if automatic:
if o.next:
    o.project, days_ago = core.next_project(p, o.verbose)

# Actualy run:
if o.dryrun:
    print('Would select: {0.project}'.format(o))
    if o.next:
        print("Project last logged: {0:.1f} days ago".format(days_ago))

elif o.retrieve:
    if o.verbose:
        print('Will retrieve: {0.project}'.format(o))

    # Retrieve host.gz:
    p[o.project].get_hostgz()
  
    # Process host.gz and save (full version, all machines):
    (nstring,cstring) = core.host_stats('host.gz')
    core.save_log(p[o.project].name,'entries.log',nstring,cstring)
  
    # Process host.gz and save (only recently active machines):
    if o.recent:
        (nstring,cstring) = core.host_stats('host.gz',True)
        pname = '%s_active' % (p[o.project].name)
        core.save_log(pname,'entries_active.log',nstring,cstring)
  
    # Clean up, and say bye:
    if (o.verbose):
      print 'Deleting hosts.gz...'
    
    os.unlink('host.gz')
    
    if (o.verbose):
        print('Finished.')
elif o.analize:
    if o.verbose:
        print('Will analize: {0.project}'.format(o))

    # Analize:
    t0 = 1201956633
    type = 'total'
  
    for t in ['nhosts']:
        print 'According to '+t+':'
        fn =  os.path.join(os.environ['HOME'], '.LOGs', 'boinc', '{0}.{1}.dat'.format(p[o.project].name,t))
        print(core.last_perc(fn))

        for order in [1]: # order of polynomial fit
            print '\nWith a polynomial of order %i:' % (order)
            for npoints in [2,3,4,5,10,20]: # number of last points to use for fit
                npoints = npoints + order
                core.fit_n_cross(fn,type,order,npoints)
else:
  # Plot or save PNG
  if o.verbose:
      print 'Will plot: %s' % (o.project)

  t0 = 1201956633
  tmpf = 'boinc.tmp'
  xmgr = 'xmgrace -barebones -geom 1050x900 -fixed 650 500 '

  types = ['total']
  if o.total:
      types.append('speed')

  for type in types:
      for t in ['nhosts','credit']:
          if o.recent:
              fn = '%s/.LOGs/boinc/%s_active.%s.dat' % (os.environ['HOME'], p[o.project].name, t)
          else:
              fn = '%s/.LOGs/boinc/%s.%s.dat' % (os.environ['HOME'], p[o.project].name, t)
          core.make_plot(fn, type, o, t0, title, t, p, tmpf)
