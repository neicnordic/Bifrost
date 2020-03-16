#!/usr/bin/env python

import yaml
import hashlib
from shutil import copyfile
import os

basepath = "/home/oskar/01-workspace/00-temp/Bifrost/"
copydest = basepath + "testing-dir/"
# Load the config file
with open(basepath + "config.yml") as file:
	configYml = yaml.load(file)

# Put the input file in a variable with absolute path added
inputfile = basepath + configYml[0]["inputfile"]

# Verify that the input file exists on disk
try:
	f = open(inputfile)
# Print error message if file not found
except IOError:
	print("File not found")
# Close file handle if the file is found
finally:
	f.close()

# Check what the job type is and act accordingly
if configYml[0]["jobtype"] == "imputation":
	with open(inputfile) as fileToCheck:
	# Read contents of the file into variable
		data = fileToCheck.read()
		# Calculate md5sum to verify that the file has been transferred successfully
		md5Returned = hashlib.md5(data).hexdigest()
		if configYml[0]["md5sum"] == md5Returned:
			print "File integrity is intact"
			# Copy the file to scratch disk
			copyfile(inputfile, copydest + os.path.basename(inputfile))
			print "Copied file to " + copydest + os.path.basename(inputfile)
