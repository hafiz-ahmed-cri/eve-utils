#!/usr/bin/env python
"""Adds files to facilitate deploying the API as a serverless function
   in either aws, azure, or google cloud

Usage:
    add_serverless [-h|--help] api_name
      NOTE: Run this in the folder above the API project folder

Examples:
    add_serverless my-api

License:
    MIT License

    Copyright (c) 2021 Michael Ottoson

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import os
import sys
import argparse
from subprocess import Popen, PIPE
from distutils.dir_util import copy_tree

import eve_utils


def warning():
    print('''
NOTE: this feature is still under development - use at your own risk!

*** DO NOT USE THIS UNLESS YOU KNOW WHAT YOU ARE DOING ***

This script will
- check for node/npm
- install serverless globally
- npm init the api folder
- install serverless plugins
- add  dnspython==2.1.0  to requirements.txt

You can then run the API with
    sls wsgi serve --config serverless-XXX.yml -p 2112

Before you deploy
- configure your credentials
  (e.g. sls config credentials --provider aws --key XXXX --secret YYYY -o)
- ensure your logging.yml makes no reference to the file system
  (e.g. copy logging_no-files.yml to logging.yml)
- modify as required the serverless-*.yml files (esp. connection to MongoDB!)
- test with serverless
  - sls wsgi serve --config serverless-XXX.yml -p 2112
- when you are ready to deploy:
  - sls deploy --config serverless-XXX.yml

- if you only use one cloud provider, copy that serverless-XXX.yml
  to serverless.yml, then you can leave off the --config...

''')



def run_process(cmd):
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, encoding='utf-8')
    out, err = process.communicate()
    exit_code = process.wait()

    return exit_code, out, err


def is_node_installed():
    exit_code, out, err = run_process('node -v')

    try:
        major_version = int(out[1:].split('.')[0])
    except:
        major_version = 0

    if exit_code:
        print('node.js is not installed.\nPlease install and try again.')
        return False
    elif major_version < 10:
        print('node.js is installed, version must be greater than v10 (yours is {out}).\nPlease upgrade and try again.')
        return False

    # TODO: is any of this even required given a proper installation of node.js?
    exit_code, out, err = run_process('npm -v')

    try:
        major_version = int(out.split('.')[0])
    except:
        major_version = 0

    if exit_code:
        print('npm is not installed.\nPlease install and try again.')
        return False
    elif major_version < 0:
        # UNREACHABLE: is there a minimun npm version required by serverlesss?
        print('npm is installed, version must be greater than XX (yours is {out}).\nPlease upgrade and try again.')
        return False


    return True


def ensure_serverless_is_installed():
    exit_code, out, err = run_process('sls -v')

    if not exit_code:  # TODO: serverless is installed, but should we check version?
        return True

    print('installing serverless framework')
    exit_code, out, err = run_process('npm install -g serverless')

    if exit_code:
        print('Something went wrong installing serverless.')
        return False


def ensure_node_initialized():
    if os.path.exists('./package.json'):
        return True

    print('running npm init')
    exit_code, out, err = run_process('npm init -f')

    if exit_code:
        print('Something went wrong running npm init.')
        return False

    return True


def ensure_serverless_plugins_installed():
    print('Installing serverless plugins')
    exit_code, out, err = run_process('npm install --save-dev serverless-wsgi serverless-python-requirements serverless-domain-manager')

    if exit_code:
        print('Something went wrong installing serverless plugins.')
        return False

    return True


def add_serverless(project_name):
    print(f'Adding serverless files for {project_name} API')

    warning()

    skel = os.path.join(os.path.dirname(eve_utils.__file__), 'skel/serverless')

    if not os.path.exists(f'{project_name}'):
        print(f'Please run this in the folder above {project_name}')
        return

    copy_tree(skel, f'./{project_name}')
    eve_utils.replace_project_name(project_name)

    if not is_node_installed():
        quit(1)

    if not ensure_serverless_is_installed():
        quit(2)

    os.chdir(f'./{project_name}')
    eve_utils.install_packages(['dnspython'], 'add_serverless')

    if not ensure_node_initialized():
        quit(3)

    if not ensure_serverless_plugins_installed():
        quit(4)



def main():
    parser = argparse.ArgumentParser('add_serverless', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('api_name', help='The name of the API to add serverless to.')

    args = parser.parse_args()
    project_name = args.api_name  # TODO: validate, safe name, etc.
    add_serverless(project_name)


if __name__ == '__main__':
    main()
