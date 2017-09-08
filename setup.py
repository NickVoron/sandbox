#!/usr/bin/env python3

import subprocess
import contextlib
import logging
import os
import shutil

from pathlib import Path

#
# Logger
#

logging.basicConfig(level=logging.INFO)

#
# Helpers
#

@contextlib.contextmanager
def cwd(new_cwd):
    """Context manager for current working directory."""
    old_cwd = Path.cwd()
    logging.info('Change cwd: %s', str(new_cwd))
    os.chdir(str(new_cwd))
    yield
    logging.info('Restore cwd: %s', str(old_cwd))
    os.chdir(str(old_cwd))

#
# Work
#
intermediate_path = '_obj-lib-etc'

root_path = Path(__file__).parent.resolve()
build_path = Path(intermediate_path) / 'windows' / 'sharedtec'
build_path.mkdir(parents=True, exist_ok=True)

with cwd(build_path):
    # See for options help: https://developer.android.com/ndk/guides/cmake.html
    # shutil.rmtree(root_path / 'build')
    cmd = [
        'cmake',
        '-G', 'Visual Studio 15 2017 Win64',
        str(root_path) # source dir
    ]

    logging.info('Run cmake command: %s', str(cmd))

    subprocess.check_call(cmd)

with cwd('.'):
    subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])

with cwd('boost-cmake/boost/boost_1_64_0'):
    p = subprocess.Popen("bootstrap.bat", cwd=r".")
    stdout, stderr = p.communicate()
    subprocess.check_call(['bjam', '--stagedir="stage/x86"', '-j10', 'toolset=msvc', 'address-model=32', 'variant=release',  'threading=multi', 'link=static', 'runtime-link=static,shared', 'define=_SECURE_SCL=0', 'define=_HAS_ITERATOR_DEBUGGING=0',  'define=BOOST_TEST_NO_MAIN'])
    subprocess.check_call(['bjam', '--stagedir="stage/x64"', '-j10', 'toolset=msvc', 'address-model=64', 'variant=release',  'threading=multi', 'link=static', 'runtime-link=static,shared', 'define=_SECURE_SCL=0', 'define=_HAS_ITERATOR_DEBUGGING=0',  'define=BOOST_TEST_NO_MAIN'])
    subprocess.check_call(['bjam', '--stagedir="stage/x86"', '-j10', 'toolset=msvc', 'address-model=32', 'variant=debug'  ,  'threading=multi', 'link=static', 'runtime-link=static,shared', 'define=BOOST_TEST_NO_MAIN'])
    subprocess.check_call(['bjam', '--stagedir="stage/x64"', '-j10', 'toolset=msvc', 'address-model=64', 'variant=debug'  ,  'threading=multi', 'link=static', 'runtime-link=static,shared', 'define=BOOST_TEST_NO_MAIN'])

print('OK')