#!/usr/bin/env bash
#
# script to run automated test framework on POSIX systems
#
# 1. setting up the environment
# 2. running actual test scripts
# 3. running coverage scripts
# 4. running sphinx scripts
# 5. running setuptools scripts
# 6. clean up afterwards
#
# All steps can be run in a single task or invokes individually providing command arguments
#

VERSION="3.7"
TESTFILE="test.py"
SYSTEM=uname

if [[ ! -e ${TESTFILE} ]]; then
    echo '*** no test.py, please make sure to have a text file ***';
    exit
fi;

run_setup()
{
    # 1. setup the environment
    echo '*** setup environment requirements ***';
    python -m pip freeze > freeze_requirements.txt;
    python -m pip install --upgrade -r requirements.txt;
    if [[ -e upgrade_requirements.txt ]]; then
        python -m pip install --upgrade -r upgrade_requirements.txt;
    fi;
}   # end of run_setup

run_test()
{
    # 2. running actual test scripts
    echo '*** run test scripts ***';
    python ${TESTFILE}
}   # end of run_test

run_coverage()
{
    # 2. running coverage scripts
    mkdir ./.bin;
    # todo switch system case
    case ${SYSTEM} in
        "Darvin" )
            echo '*** download coverage reporter for macOS ***';
            curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > "$./.bin/cc-test-reporter" && chmod +x "./.bin/cc-test-reporter";;
        "Linux" )
            echo '*** download coverage reporter for Linux ***';
            curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-darwin-amd64 > "$./.bin/cc-test-reporter" && chmod +x "./.bin/cc-test-reporter";;
    esac
    echo '*** run coverage scripts ***';
    cc-test-reporter before-build
    coverage run ${TESTFILE};
    coverage report -m;
    coverage html -d ./doc/coverage;
    coverage xml;

    echo '*** upload coverage report ***';
    ./.bin/cc-test-reporter after-build -t coverage.py --exit-code $? --prefix /home/rof/src/github.com/sonntagsgesicht/businessdate
    rm -r-f ./.bin;
    coverage erase;
}   # end of run_coverage

run_sphinx()
{
    # todo add sphinx build and doctest
    echo '*** run sphinx scripts ***';
    cd ./doc/sphinx/;
    make clean;
    make html;
    make doctest;
    cd ../..;
}   # end of run_sphinx

run_setuptools()
{
    # todo add python setup.py bdist_wheel
    echo '*** run setuptools scripts ***';
    python setup.py build
}   # end of run_setuptools

run_cleanup()
{
    echo '*** clean environment ***';
    # 3. clean up afterwards
    python -m pip uninstall -y -r requirements.txt;
    python -m pip uninstall -y -r upgrade_requirements.txt;
    # sed -i 's/==/>=/g' freeze_requirements.txt
    python -m pip install --upgrade -r freeze_requirements.txt;
}   # end of run_cleanup


# run full test pine line

#pyenv 2.7
run_setup
run_test
run_cleanup

#pyenv 3.5
#run_setup
#run_test
#run_cleanup
#
#pyenv 3.6
#run_setup
#run_test
#run_cleanup
#
#pyenv 3.7
#run_setup
#run_test
#run_coverage
#run_sphinx
#run_setuptools
#run_cleanup
