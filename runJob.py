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

from constants import yamlFileName, basePath

# TODO Put this path in a separate config file?
imputationserver = "/home/ubuntu/imputeDisk/01-workspace/00-temp/imputationserver"
bifrost = "/home/ubuntu/imputeDisk/01-workspace/00-temp/ifrostScz/Bifrost"
searchPath = glob(os.path.join(basePath, "decrypted-*"))

# Setting current work directory to the "next one" that gets globbed when the searchPath variable is created
# No fancy job prioritization is done
i = 0
for dir in searchPath:
	if os.path.isfile(dir + "/lockfile"):
		print(dir + " has a lockfile, a job is running, exiting now.")
		quit()

print("No job is running, will process data in " + searchPath[0] + ", creating lockfile and attempting to start job.")
cwd = searchPath[0] + "/"
os.chdir(cwd)

# Create lockfile
open("lockfile", 'a').close()
print("Created lock file so no other job can be started.")
if not os.path.isdir("outputs"):
	os.makedirs("outputs")
	print("Created outputs directory.")
else:
	print("Outputs directory folder already exists.")

outputs = cwd + "outputs"

# Load the config file
try:
	with open(yamlFileName) as file:
		configYml = yaml.load(file, Loader=yaml.FullLoader)
# Print error message if file is not found
except IOError:
	print("Config file not found, exiting")
	quit()

# If statements that runs the imputation job when the fileCopied field is False in the config file
if configYml[0]["jobType"] == "imputation":
	# While loop that runs until job is successful or fails
	while True:
		if configYml[0]["fileCopied"] == "True" and configYml[0]["decrypting"] == "True":
			# Put the encrypted input file in a variable
			inputFile = configYml[0]["inputFile"]

			# Verify that the file exists on disk
			try:
#				print "Checking for encrypted input file"
				f = open(inputFile)
#				print "Found encrypted input file"
			# Print error message if file is not found
			except IOError:
				print("Input file not found, exiting")
			# Close file handle if the file is found
			finally:
				f.close()

			# Calculate md5sum
			with open(inputFile) as fileToCheck:
				# TODO make this into a function
				# Read contents of the file into variable
				print("Loading decrypted input file")
				data = fileToCheck.read()

				# Calculate md5sum to verify that the file has been transferred successfully
				print("Calculating md5sum")
				md5Returned = hashlib.md5(data).hexdigest()
				print("Finished calculating md5sum")

				# Compare md5sum and copy files to the scratch disk if the md5sum is intact after decryption
				if configYml[0]["md5sum"] == md5Returned:
					# TODO make this into a function
					print("File integrity is intact")
					print("Splitting vcf by chromosome")
					print(cwd + inputFile)
					split = bifrost + "/splitByChromosome.sh " + cwd + inputFile + " " + imputationserver + "/apps/imputationserver/1.2.7/bin/tabix " + imputationserver + "/apps/imputationserver/1.2.7/bin/bgzip"
					print(split)
					subprocess.call(split, shell=True)
					print("Finished splitting vcf file by chromosome")
					print("Starting impute job")
					inputs = cwd + "inputs/"

					# Start the imputation job
					client = docker.from_env()
					container = client.containers.run(
						'genepi/imputationserver:latest',
						"/data/startImpute.sh",
						volumes = {
							bifrost: {
								'bind':'/bifrost/',
								'mode':'rw'
									},
							outputs: {
								'bind':'/outputs/',
								'mode':'rw'
									},
							inputs: {
								'bind':'/inputs/',
								'mode':'rw'
									},
							imputationserver: {
								'bind':'/data/',
								'mode':'rw'
									},
								}, detach = False
					)
					# Create "done" file to show that the docker job exited successfully
					open(cwd + "done", 'a').close()
					print("Job has exited, 'done' file has been created")
					print("Removing lockfile")
					os.remove("lockfile")
					exitedDirName = re.sub("decrypted", "JobFinished", cwd)
					os.rename(cwd, exitedDirName)
					print("Work directory has been renamed from " + os.basename(cwd) + " to " + exitedDirName)
					print("Job finished successfully!")
					break
				else:
					print("File is not the same, did the decryption fail? Exiting")
					quit()
					# Go back to the decryption step here?

		elif configYml[0]["fileCopied"] == "False" and configYml[0]["decrypting"] == "True":
			print("File decryption has started, files have not been transferred, waiting")
			break

# This gets executed when the jobType is schizophrenia and the fileCopied field is False in the config file
elif configYml[0]["jobType"] == "schizophrenia" and configYml[0]["fileCopied"] == "False":
	print("Test scz run job")
