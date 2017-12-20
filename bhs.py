# -*- coding=utf-8 -*-

# Standard libs:
import os
import json

# Our libs:
from libbhs import core

# Functions:
def main():
    """Main loop."""

    # Read arguments:
    o = core.parse_args()

    if o.dryrun:
        o.verbose += 1

    # Read conf:
    fn_conf = os.path.join(os.environ["HOME"], "git", "bhs", "boinc.json")
    with open(fn_conf) as f:
        J = json.load(f)

    # Populate BHS object with opt and conf data:
    B = core.BHS(o)
    B.populate(J)

    # Help:
    if B.pkey == 'help':
        shelp = 'Currently available projects:\n'
        for pkey in sorted(B.pdict):
            shelp += '    {0:10s} {1}\n'.format(pkey, B.pdict[pkey].name)
        exit(shelp)

    # Choose project if automatic:
    if o.next:
        B.next_project()

    # Actualy run:
    if o.dryrun:
        print('Would select: {0.project.name}'.format(B))
        if o.next:
            print("Project last logged: {0:.1f} days ago".format(B.next_ago))

    elif o.retrieve:
        if o.verbose:
            print('Will retrieve: {0.project.name}'.format(B))

        # Retrieve host.gz:
        B.get_hostgz()
      
        # Process host.gz and save (full version, all machines):
        (nstring, cstring) = B.distile_stats()
        B.save_log(nstring, cstring)
      
        # Process host.gz and save (only recently active machines):
        if o.recent:
            (nstring, cstring) = B.distile_stats(recent=True)
            B.save_log(nstring, cstring, recent=True)
      
        # Clean up, and say bye:
        if (o.verbose):
            print('Deleting hosts.gz...')
        
        os.unlink('host.gz')
        
        if o.verbose:
            print('Finished.')

    else:
        # Plot or save PNG:
        if o.verbose:
            print('Will plot: {0.project}'.format(o))

        for what in ['nhosts','credit']:
            B.make_plot(what)


# Main loop:
if __name__ == "__main__":
    main()

