#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2015, Marcel Jackwerth <marceljackwerth@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
"""Ansible library to handle installation of Xcode"""

import sys
import os
import re
import shlex
import subprocess

DOCUMENTATION = '''
---
module: xcversion
author: "Marcel Jackwerth (@sirlantis)"
short_description: installs versions of Xcode
description:
    - Installs or selects a specified version of Xcode.
options:
    version:
        description:
            - version of Xcode to install/select
        required: true
    state:
        description:
            - indicate the desired state of the resource
        required: false
        default: "selected"
        choices: ["present", "selected"]
    clean:
        description:
            - If C(no), C(xcode-install) won't remove the downloaded
              installation file to allow faster re-installation.
        choices: [ "yes", "no" ]
        required: false
    user:
        description:
            - The Apple ID / e-mail for talking to Apple servers
        required: false
        default: null
    password:
        description:
            - The password for C(user)
        required: false
        default: null
requirements:
    - OS X
    - xcode-install Ruby Gem
'''

EXAMPLES = '''
- name: Installs Xcode 7.1.1
  xcversion: state=present version=7.1.1

- name: Selects (and installs if necessary) Xcode 7.1.1
  xcversion: state=selected version=7.1.1
'''

def check_xcodeinstall():
    """Returns True if xcode-install gem executable can be found."""
    null_device = open(os.devnull, 'w')
    return subprocess.call(['xcversion', '--version'], shell=True, stdout=null_device) == 0

class Xcversion(object):
    """Representation of a single Ansible job."""

    def __init__(self, module):
        self.module = module
        self.version = module.params['version']
        self.check_mode = module.check_mode

    def check_installed(self):
        """Checks whether the desired version of Xcode is installed."""
        output = subprocess.check_output(['xcversion', 'installed'])
        lines = output.split('\n')

        for line in lines:
            parts = re.split(r'\s', line)
            if self.version in parts:
                return True

        return False

    def ensure_installed(self):
        """Installs the desired version of Xcode if necessary."""
        if self.check_installed():
            return (False, "Xcode %s already present." % self.version)
        if self.check_mode:
            return (True, None)

        (user, password) = (self.module.params['user'], self.module.params['password'])

        if not (user and password):
            self.module.fail_json(msg=("You must provide a user or password "
                                       "(or set the FASTLANE_USER and "
                                       "FASTLANE_PASSWORD env variables)"))

        env = os.environ.copy()
        env["FASTLANE_USER"] = user
        env["FASTLANE_PASSWORD"] = password

        subprocess.check_call(['xcversion', 'update'], env=env) # TODO: only call if needed

        install_cmd = ['xcversion', 'install']
        if not self.module.params['clean']:
            install_cmd.append('--no-clean')
        install_cmd.append(self.version)
        subprocess.check_call(install_cmd, env=env)

        return (True, None)

    def check_selected(self):
        """Checks whether the desired version of Xcode is selected."""
        output = subprocess.check_output(['xcversion', 'selected'])
        lines = output.split('\n')
        return self.version in lines[0]

    def ensure_selected(self):
        """Selects the desired version of Xcode if necessary."""
        if self.check_selected():
            return (False, "Xcode %s already selected." % self.version)
        if self.check_mode:
            return (True, None)

        subprocess.check_call(['xcversion', 'select', self.version])

        return (True, None)

    def run(self):
        """Executes the Ansible command."""
        if not check_xcodeinstall():
            if self.check_mode:
                self.module.exit_json(changed=True)

            self.module.fail_json(msg=("xcode-install not found. "
                                       "Add `gem: name=xcode-install` "
                                       "to your playbook."))

        state = self.module.params['state']
        (changed, message) = (False, None)

        if state in ('selected', 'present'):
            (changed, message) = self.ensure_installed()

        if state == 'selected':
            (changed, message) = self.ensure_selected()

        self.module.exit_json(changed=changed, msg=message)

def parse_options():
    """Parses parameters passed by Ansible into a dictionary."""
    args_file = sys.argv[1]
    args_data = file(args_file).read()

    options = dict()
    arguments = shlex.split(args_data)
    for arg in arguments:
        if "=" in arg:
            (key, value) = arg.split("=")
            options[key] = value

    return options

def main():
    """Entry-point of script."""
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(required=True),
            state=dict(default='selected', choices=['present', 'selected']),
            clean=dict(default=True, choices=BOOLEANS),
            user=dict(default=os.getenv("FASTLANE_USER")),
            password=dict(default=os.getenv("FASTLANE_PASSWORD"), no_log=True),
        ),
        supports_check_mode=True,
    )
    Xcversion(module).run()

#pylint: disable=redefined-builtin
#pylint: disable=unused-wildcard-import
#pylint: disable=wildcard-import
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()