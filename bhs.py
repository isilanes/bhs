# -*- coding=utf-8 -*-

# Standard libs:
import os
import json
import logging

# Our libs:
from libbhs import core
from logworks import logworks

# Functions:
def main():
    """Main loop."""

    # Read arguments:
    opts = core.parse_args()

    # Verbosity:
    if opts.dryrun:
        opts.verbose = True

    loglevel = logging.INFO
    if opts.verbose:
        loglevel = logging.DEBUG

    # Create logger:
    logger = logworks.Logger(level=loglevel)

    # Read conf:
    conf = core.read_conf(logger=logger)

    # Populate BHS object with opt and conf data:
    B = core.BHS(opts, conf, logger)

    # Actualy run:
    logger.info("Project that will be processed: {b.project.key}".format(b=B))

    if opts.retrieve:
        # Retrieve host.gz:
        B.project.get_hostgz(opts)
      
        # Process host.gz and save (full version, all machines):
        nstring, cstring = B.distile_stats()
        B.save_log(nstring, cstring)
      
        # Process host.gz and save (only recently active machines):
        if opts.recent:
            nstring, cstring = B.distile_stats(recent=True)
            B.save_log(nstring, cstring, recent=True)
      
        # Clean up, and say bye:
        logger.debug('Deleting hosts.gz...')
        os.unlink('host.gz')
        
        # Bye-bye:
        logger.info('Finished.')

    else:
        # Plot or save PNG:
        logger.debug('Will plot: {b.project.name}'.format(b=B))

        for what in ['nhosts', 'credit']:
            B.make_plot(what)


# Main loop:
if __name__ == "__main__":
    main()

