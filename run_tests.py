#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import signal
from subprocess import check_call, Popen, check_output
import sys
import time
import pip
import urllib2
import tarfile


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
    with open(tar_filename, "wb") as code:
        code.write(response.read())


def kill_jenkins():
    '''
     Kill all Jenkins processes
    '''
    print "Killing Jenkins"
    pids = check_output(['lsof', '-i:8080', '-t'])
    pids = pids.strip().split('\n')

    for pid in pids:
        os.kill(int(pid), signal.SIGKILL)


def run_tests():
    '''
    Main Function that handles all the tests.
    '''
    try:
        print "Checking Patches"
        check_call('./test/check_patches.sh')

        if os.path.exists("./" + DIR_JENKINS_ENV) and os.environ.get('CI') == None:
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

        print "Starting Jenkins"
        Popen(['./start.py', '>', 'jenkins.out'])

        time.sleep(60)

        if os.path.exists(DIR_TEST_ENV):
            print "Using virtual environment in ", DIR_TEST_ENV
        else:
            tar_filename = "virtualenv-" + VERSION_VIRTUALENV + ".tar.gz"
            print "Creating a virtual environment (version %s) in %s" %  (VERSION_VIRTUALENV, DIR_TEST_ENV)
            url = "https://pypi.python.org/packages/source/v/virtualenv/virtualenv-" + \
                VERSION_VIRTUALENV + ".tar.gz"
            destination = download(url, tar_filename)

            tar = tarfile.open(name=tar_filename)
            tar.extractall(path='.')
            check_call(
                ["virtualenv-" + VERSION_VIRTUALENV + "/virtualenv.py", DIR_TEST_ENV])

        pip('install', 'selenium')

        python('test/configuration/save_config.py')

    except:
        print "Could not activate virtual environment"
        print "Exiting"
        sys.exit(1)

    kill_jenkins()

if __name__ == '__main__':
    run_tests()