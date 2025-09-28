#!/usr/bin/python

import os
import fnmatch
import subprocess

for root, dirs, files in os.walk("."):
  for svg in fnmatch.filter(files, "*.svg"):
    svg = os.path.join(root, svg)
    png = os.path.splitext(svg)[0] + ".png"
    result = subprocess.run(
      [
        "inkscape",
        "-e",
        png,
        "-D",
        svg,
        "-b",
        "black",
        "-y",
        "0.0",
      ],
      check=False,
    )
    print(svg, result.returncode)
