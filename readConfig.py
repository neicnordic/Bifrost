#!/usr/bin/env python

import yaml
import hashlib
from shutil import copyfile
import os
import datetime

basepath = "/home/oskar/01-workspace/00-temp/Bifrost/"
yml = basepath + "config.yml"

now = str(datetime.datetime.now())[:19]
now = now.replace(":","_")
now = now.replace(" ","-")

copydest = basepath + "testing-dir-" + now + "/"
# Load the config file
with open(basepath + "config.yml") as file:
	configYml = yaml.load(file)

# If statements that runs the imputation job when the filecopied field is False in the config file
if configYml[0]["jobtype"] == "imputation" and configYml[0]["filecopied"] == "False":
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

	with open(inputfile) as fileToCheck:
	# Read contents of the file into variable
		data = fileToCheck.read()

		# Calculate md5sum to verify that the file has been transferred successfully
		md5Returned = hashlib.md5(data).hexdigest()
		if configYml[0]["md5sum"] == md5Returned:
			print "File integrity is intact"

			# Create the destination directory
			os.mkdir(copydest)

			# Copy the file to the scratch disk
			copyfile(inputfile, copydest + os.path.basename(inputfile))
			print "Copied input file to " + copydest + os.path.basename(inputfile)

			# Copy yaml file to the scratch disk
			copyfile(yml, copydest + os.path.basename(yml))
			print "Copied yaml file to " + copydest + os.path.basename(yml)

			# Set the "filecopied" field to "True" so that the file does not get copied forever by the cron job
			configYml[0]["filecopied"] = "True"
			with open(yml, "w") as f:
				yaml.dump(configYml, f, default_flow_style=False)

# This gets executed when the jobtype is schizophrenia and the filecopied field is False in the config file
elif configYml[0]["jobtype"] == "schizophrenia" and configYml[0]["filecopied"] == "False":

else:
	print "Files have already been copied, not copying again."
