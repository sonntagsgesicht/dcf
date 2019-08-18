#!/usr/bin/env bash
#
# script to run automated test framework on POSIX systems
#
# 1. setting up the environment
# 2. running actual test and deployment scripts
# 3. clean up afterwards
#
# All steps can be run in a single task or invokes individually providing command arguments
#

# import utility functions
. pipeline_tools.sh;
if [[ -e pipeline_info.sh ]]; then . pipeline_info.sh; fi;

# ----------------------------------------------------------------------------
# run full test pine line
# ----------------------------------------------------------------------------

echo ''
run_simple 2.7

echo ''
run_simple 3.5

echo ''
run_simple 3.6

echo ''
run_full 3.7
