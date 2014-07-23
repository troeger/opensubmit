#! /usr/bin/env python
import sys

perffile = open(sys.argv[1], "w")
perffile.write("42;43")
perffile.close()
print("Your solution produced the correct output.")
exit(0)
