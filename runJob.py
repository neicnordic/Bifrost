#!/usr/bin/env python2.7

import re
import docker
import sys
import subprocess
import yaml
import hashlib
from shutil import copyfile
from shutil import copyfileobj
import os
import datetime
from glob import glob

# TODO Put this path in a separate config file?
basepath = "/home/ubuntu/imputeDisk/01-workspace/00-temp/bifrost-testing/"
imputationserver = "/home/ubuntu/imputeDisk/01-workspace/00-temp/imputationserver"
bifrost = "/home/ubuntu/imputeDisk/01-workspace/00-temp/Bifrost"
searchpath = glob(basepath + "/decrypted-*")

# Setting current work directory to the "next one" that gets globbed when the searchpath variable is created
# No fancy job prioritization is done
i = 0
for dir in searchpath:
	if os.path.isfile(dir + "/lockfile"):
		print dir + " has a lockfile, a job is running, exiting now."
		quit()

print "No job is running, will process data in " + searchpath[0] + ", creating lockfile and attempting to start job."
cwd = searchpath[0] + "/"
os.chdir(cwd)
yml = "config.yml"

# Create lockfile
open("lockfile", 'a').close()
print "Created lock file so no other job can be started."
if not os.path.isdir("outputs"):
	os.makedirs("outputs")
	print("Created outputs directory.")
else:
	print("Outputs directory folder already exists.")

outputs = cwd + "outputs"

# Load the config file
try:
	with open("config.yml") as file:
		configYml = yaml.load(file, Loader=yaml.FullLoader)
# Print error message if file is not found
except IOError:
	print("Config file not found, exiting")
	quit()

# If statements that runs the imputation job when the filecopied field is False in the config file
if configYml[0]["jobtype"] == "imputation":
	# While loop that runs until job is successful or fails
	while True:
		if configYml[0]["filecopied"] == "True" and configYml[0]["decrypting"] == "True":
			# Put the encrypted input file in a variable with absolute path added
			inputfile = configYml[0]["inputfile"]

			# Verify that the file exists on disk
			try:
#				print "Checking for encrypted input file"
				f = open(inputfile)
#				print "Found encrypted input file"
			# Print error message if file is not found
			except IOError:
				print("Input file not found, exiting")
			# Close file handle if the file is found
			finally:
				f.close()

			# Calculate md5sum
			with open(inputfile) as fileToCheck:
				# TODO make this into a function
				# Read contents of the file into variable
				print "Loading decrypted input file"
				data = fileToCheck.read()

				# Calculate md5sum to verify that the file has been transferred successfully
				print "Calculating md5sum"
				md5Returned = hashlib.md5(data).hexdigest()
				print "Finished calculating md5sum"

				# Compare md5sum and copy files to the scratch disk if the md5sum is intact after decryption
				if configYml[0]["md5sum"] == md5Returned:
					# TODO make this into a function
					print "File integrity is intact"
					print "Starting impute job"

					# Start the imputation job
					client = docker.from_env()
					container = client.containers.run(
						'genepi/imputationserver:latest',
						"/data/start-impute.sh",
						volumes = {
							bifrost: {
								'bind':'/bifrost/',
								'mode':'rw'
									},
							outputs: {
								'bind':'/outputs/',
								'mode':'rw'
									},
							cwd: {
								'bind':'/inputs/',
								'mode':'rw'
									},
							imputationserver: {
								'bind':'/data/',
								'mode':'rw'
									},
								}, detach = False
					)
					# Create "done" file to stop cron job from starting new imputation job
					open(cwd + "done", 'a').close()
					print "Job has exited, 'done' file has been created"
					print "Removing lockfile"
					os.remove("lockfile")
					exitedDirName = re.sub("decrypted", "Exited", cwd)
					os.rename(cwd, exitedDirName)
					break
				else:
					print "File is not the same, did the decryption fail? Exiting"
					quit()
					# Go back to the decryption step here?

		elif configYml[0]["filecopied"] == "False" and configYml[0]["decrypting"] == "True":
			print "File decryption has started, files have not been transferred, waiting"
			break

# This gets executed when the jobtype is schizophrenia and the filecopied field is False in the config file
elif configYml[0]["jobtype"] == "schizophrenia" and configYml[0]["filecopied"] == "False":
	print "Test"
