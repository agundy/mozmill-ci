#!/usr/bin/env python

import os
import signal
import subprocess
import sys
import time
import pip
import urllib2
import tarfile

DIR_TEST_ENV = "test/env"
DIR_JENKINS_ENV = 'jenkins-env'
VERSION_VIRTUALENV = '1.9.1'

os.environ["JENKINS_HOME"] = "jenkins-master"

print "Checking Patches"
subprocess.check_call('./test/check_patches.sh')

if os.path.exists("./" + DIR_JENKINS_ENV) and os.environ.get('CI') == None:
    print "Jenkins environment already exists!"
    while True:
        user_input = raw_input("Would you like to recreate it? ")
        if user_input[0].lower() == "y":
            print "Running setup:"
            subprocess.call(["./setup.sh", DIR_JENKINS_ENV])
            break
        elif user_input[0].lower() == "n":
            break
        else:
            print "Please answer yes or no."
else:
    print "Running setup"
    subprocess.call(["./setup.sh", DIR_JENKINS_ENV])

print "Starting Jenkins"
subprocess.Popen(['./start.py', '>', 'jenkins.out'])

time.sleep(30)

if os.path.exists(DIR_TEST_ENV):
    print "Using virtual environment in ", DIR_TEST_ENV
else:
    tar_filename = "virtualenv-"+ VERSION_VIRTUALENV +".tar.gz"
    print "Creating a virtual environment (version ", VERSION_VIRTUALENV, ") in ", DIR_TEST_ENV
    f = urllib2.urlopen("https://pypi.python.org/packages/source/v/virtualenv/virtualenv-" + VERSION_VIRTUALENV + ".tar.gz") 
    with open(tar_filename,"wb") as code:
        code.write(f.read())
    tar = tarfile.open(name=tar_filename)
    tar.extractall(path='.')
    subprocess.call(["virtualenv-" + VERSION_VIRTUALENV + "/virtualenv.py" ,DIR_TEST_ENV])

virtualenv_path = DIR_TEST_ENV + "/bin/"

subprocess.call([virtualenv_path+'pip','install','selenium'])

subprocess.call([virtualenv_path+'python','test/configuration/save_config.py'])


print "Killing Jenkins"
pids = subprocess.check_output(['lsof','-i:8080','-t'])
pids = pids.strip().split('\n')

for pid in pids:
    os.kill(int(pid), signal.SIGKILL)
