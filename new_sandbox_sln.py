#!/usr/bin/env python3

import template, sys, os

print(sys.argv)
if len(sys.argv) == 2:
    template.unpack_solution("_static_library.zip", "SandBox", sys.argv[1])
    slnfile = "SandBox\\" + sys.argv[1] + ".sln"
    os.system("start "+ slnfile)