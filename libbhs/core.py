import re
import os
import sys
import datetime

sys.path.append(os.environ['HOME']+'/git/pythonlibs')
sys.path.append('/usr/lib/python2.7/site-packages')

import DataManipulation as DM
import FileManipulation as FM
import System as S
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

def make_plot(fn, type, opts, t0, title, t, p, tmpf):
  '''Plot results with Xmgrace, either interactively or saving to a PNG file.
    fn   = file name of data file
    type = whether you want raw values ('total') or their (approx. numeric) derivative vs. time ('speed')'''

  [out_string,tot,world] = proc_data(fn,type, opts, t0)

  subtit = title[t][type]

  units = ['','k','M','G']
  stot = tot
  iu   = 0
  while stot > 10000:
    stot = stot / 1000
    iu += 1

  subtit = " %s: %i %s" % (subtit,stot,units[iu])

  tit = p[opts.project].name

  FM.w2file(tmpf,out_string)

  if opts.png:
    fout = fn.replace('.dat','_'+type+'.png')
    fout = fout.replace('@','_at_')

  if opts.total:
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

  if opts.png:
    DM.xmgrace([tmpf],parf,pexec=pexec,fn=fout)

  else:
    DM.xmgrace([tmpf],parf,pexec=pexec)

  os.unlink(tmpf)

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

def fit_n_cross(fn,type='total',order=1,npoints=5):
  '''Use polynomial of N-order to fit curves, and then find crossing.
    fn    = name of file to get info from
    type  = type of data
    order = N of N-order polynomial'''

  # Get last "npoints" points only:
  fntail = '%s.tailed' % (fn)
  cmnd = 'tail --lines=%i %s > %s' % (npoints,fn,fntail)
  S.cli(cmnd)
  s = proc_data(fntail, type, t0)
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

def next_project(p=None, verbosity=0, logfile=None):
    '''Read a log file to see which was the project logged longest ago, and log it,
    according to an internal list of the projects with the flag "log=True".'''

    if not logfile:
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
    for k,v in p.items():
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

    return max_name, max_ago/86400.


#--------------------------------------------------------------------------------#
