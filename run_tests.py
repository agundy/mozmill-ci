#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import signal
import sys
import tarfile
import time
import urllib2

from subprocess import check_call, Popen, check_output

DIR_TEST_ENV = "test/env"
DIR_JENKINS_ENV = 'jenkins-env'
VERSION_VIRTUALENV = '1.9.1'

os.environ["JENKINS_HOME"] = "jenkins-master"


def python(*args):
    pypath = [os.path.join(DIR_TEST_ENV, 'bin', 'python')]
    check_call(pypath + list(args))


def pip(*args):
    pippath = [os.path.join(DIR_TEST_ENV, 'bin', 'pip')]
    check_call(pippath + list(args))


def download(url, destination):
    response = urllib2.urlopen(url)
    with open(destination, "wb") as code:
        code.write(response.read())


def kill_jenkins():
    """Kill all Jenkins processes"""
    print "Killing Jenkins"
    pids = check_output(['lsof', '-i:8080', '-t'])
    pids = pids.strip().split('\n')

    for pid in pids:
        os.kill(int(pid), signal.SIGKILL)


def run_tests():
    """Main Function that handles all the tests."""
    print "Checking Patches"
    check_call('./test/check_patches.sh')

    if os.path.exists("./" + DIR_JENKINS_ENV) and not os.environ.get('CI'):
        print "Jenkins environment already exists!"
        while True:
            user_input = raw_input("Would you like to recreate it? ")
            if user_input[0].lower() == "y":
                print "Running setup:"
                check_call(["./setup.sh", DIR_JENKINS_ENV])
                break
            elif user_input[0].lower() == "n":
                break
            else:
                print "Please answer yes or no."
    else:
        print "Running setup"
        check_call(["./setup.sh", DIR_JENKINS_ENV])

    try:
        print "Starting Jenkins"
        log = open('jenkins.out', 'w')
        error = open('jenkins.error', 'w')
        Popen(['./start.py'], shell=True, universal_newlines=True, stdout=log, stderr=error)
        log.close()
        error.close()

        if os.path.exists(DIR_TEST_ENV):
            print "Using virtual environment in ", DIR_TEST_ENV
        else:
            tar_filename = 'virtualenv-%s.tar.gz' % VERSION_VIRTUALENV
            print 'Creating a virtual environment (version %s) in %s' % (VERSION_VIRTUALENV, DIR_TEST_ENV)
            url = 'https://pypi.python.org/packages/source/v/virtualenv/%s' % tar_filename
            download(url, tar_filename)

            tar = tarfile.open(name=tar_filename)
            tar.extractall(path='.')
            check_call(["virtualenv-%s/virtualenv.py" % VERSION_VIRTUALENV, 
                DIR_TEST_ENV])

        print 'Activating virtual environment'
        # Assumes Linux Platform
        activate_this_file = os.path.join(
                DIR_TEST_ENV, 'bin', 'activate_this.py')
        if not os.path.isfile(activate_this_file):
            # create venv
            check_call(['virtualenv', '--no-site-packages', DIR_TEST_ENV])

        execfile(activate_this_file, dict(__file__=activate_this_file))
        print "Virtual environment activated successfully."

        pip('install', 'selenium')

        time.sleep(60)

        python('test/configuration/save_config.py')
    except:
        print "Could not activate virtual environment"
        print "Exiting"
        kill_jenkins()
        sys.exit(1)
    kill_jenkins()
    check_call(['git', '--no-pager', 'diff', '--exit-code'])

if __name__ == '__main__':
    run_tests()
