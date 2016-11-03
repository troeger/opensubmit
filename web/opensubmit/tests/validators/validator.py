#! /usr/bin/env python
import sys

perffile=open(sys.argv[1],"w")
perffile.write("44;45")
perffile.close()
print("Your solution produced the correct output.")
print("Did I mention that I came from a validation script ZIP file ?")
exit(0)
