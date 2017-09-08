#!/usr/bin/env python3

import subprocess, contextlib, logging, os, shutil, msbuild
from pathlib import Path

logging.basicConfig(level=logging.INFO)

@contextlib.contextmanager
def cwd(new_cwd):
    """Context manager for current working directory."""
    old_cwd = Path.cwd()
    logging.info('Change cwd: %s', str(new_cwd))
    os.chdir(str(new_cwd))
    yield
    logging.info('Restore cwd: %s', str(old_cwd))
    os.chdir(str(old_cwd))

def setup():
    with cwd('.'):
        subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])

    intermediate_path = '_obj-libs-etc'
    root_path = Path(__file__).parent.resolve()
    build_path = Path(intermediate_path) / 'windows' / 'sharedtec'
    build_path.mkdir(parents=True, exist_ok=True)
    with cwd(build_path):
        cmd = [
            'cmake',
            '-G', 'Visual Studio 15 2017 Win64',
            str(root_path) # source dir
        ]

        logging.info('Run cmake command: %s', str(cmd))

        subprocess.check_call(cmd)

    with cwd('boost-cmake/boost/boost_1_64_0'):
        if not os.path.exists("bjam.exe"):
            p = subprocess.Popen("bootstrap.bat", cwd=r".")
            stdout, stderr = p.communicate()
        subprocess.call([r'bjam', r'--stagedir=stage/x64', r'-j10', r'toolset=msvc', r'address-model=64', r'variant=release',  r'threading=multi', r'link=static', r'runtime-link=static,shared', r'define=_SECURE_SCL=0', r'define=_HAS_ITERATOR_DEBUGGING=0',  r'define=BOOST_TEST_NO_MAIN'])
        subprocess.call([r'bjam', r'--stagedir=stage/x64', r'-j10', r'toolset=msvc', r'address-model=64', r'variant=debug'  ,  r'threading=multi', r'link=static', r'runtime-link=static,shared', r'define=BOOST_TEST_NO_MAIN'])

    with cwd("third_party"):
        msbuild.build('third_party.sln', 'Release', 'x64')

    with cwd("Stable"):
        msbuild.build('libs.sln', 'Release', 'x64')

setup()