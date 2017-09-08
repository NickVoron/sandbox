#!/usr/bin/env python3

import subprocess, os
import multiprocessing

def find_msbuild():
	possibleVariants = [r"c:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe",
						r"c:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe",
						r"c:\Program Files (x86)\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\MSBuild.exe"]
	for target in possibleVariants:
		if os.path.exists(target):
			return target
	return r"MSBuild.exe"

def msbuild(target, options):
	tool = find_msbuild()
	if os.path.exists(tool):
		subprocess.call([tool, target] + options)

def rebuild(target, configuration, platform):
	msbuild(target, ['/t:Rebuid', '/p:Configuration=' + configuration, '/property:Platform=' + platform, '/maxcpucount:' + str(multiprocessing.cpu_count())])

def build(target, configuration, platform):
	msbuild(target, ['/p:Configuration=' + configuration, '/property:Platform=' + platform, '/maxcpucount:' + str(multiprocessing.cpu_count())])