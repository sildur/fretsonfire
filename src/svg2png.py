#!/usr/bin/python

import os, fnmatch

for root, dirs, files in os.walk("."):
  for svg in fnmatch.filter(files, "*.svg"):
    svg = os.path.join(root, svg)
    result = os.system("inkscape -e '%s' -D '%s' -b black -y 0.0" % (svg.replace(".svg", ".png"), svg))
    print(svg, result)
