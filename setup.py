#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function 
from setuptools import setup, Command

import sys, os

NAME="pmond"
PACKAGE=f"lib/{NAME}"
with open(os.path.join(f"{PACKAGE}", "version.py")) as f:
    code = compile(f.read(), "version.py", "exec")
    exec(code)


sys.path.append(".")
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    print("------------------------------")
    print("Must use python 3.5 or greater", file=sys.stderr)
    print("Found python version ", sys.version_info, file=sys.stderr)
    print("Installation aborted", file=sys.stderr)
    print("------------------------------")
    sys.exit()

class tester(Command):
    description = "Run unittests for the program"
    user_options = []
    
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        import pmon.tests.runtests as tests
        return tests.main(True, True, 2)

setup(
    name="pmond",
    version=__version__,
    packages=[f"{NAME}", f"{NAME}.probes", f"{NAME}.probes.static", f"{NAME}.dblayer"],
    package_dir={'': 'lib'},
    author="Jeremy Musser",
    author_email="jemusser@iu.edu",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    dependency_links=[
        "git+https://github.com/periscope-ps/unisrt.git/@v2.0.0#egg=mundus"
    ],
    install_requires=[
        "netifaces",
        "mundus"
    ],
    cmdclass={'test': tester },
    entry_points = {
        'console_scripts': [
            f"perimond = {NAME}:main",
        ]
    },
)
