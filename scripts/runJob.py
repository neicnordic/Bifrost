#!/usr/bin/env python3

import re
import sys
import subprocess
import yaml
import hashlib
from shutil import copyfile, copy
from shutil import copyfileobj
import os
import datetime
from glob import glob
from ConfigYml import ConfigYml

from constants import yamlFileName, basePath, imputationserver, bifrost, encryptedInputLabel, schizophrenia, scratch

# If statements that runs the imputation job when the fileCopied field is False in the config file
def imputeJob():
	# Put the encrypted input file in a variable
	inputFile = re.sub('\.c4gh$', '', configYml[0]["encryptedInput"])

	# Verify that the file exists on disk
	try:
		f = open(inputFile)
	except IOError:
		print("Input file not found, exiting")
	finally:
		f.close()

	# TODO make this into a function
	print("Splitting vcf by chromosome")

	global bifrost
#	split = bifrost + "/scripts/splitByChromosome.sh " + os.path.join(cwd, inputFile) + " /usr/bin/tabix " + "/usr/bin/bgzip"
	split = [os.path.join(cwd, inputFile), "/usr/bin/tabix", "/usr/bin/bgzip"]
	split = ' '.join(split)
	split = bifrost + "scripts/splitByChromosome.sh " + split
	subprocess.run(split, shell=True, check=True)
	print("Finished splitting vcf file by chromosome")
	print("Starting impute job")

	# Build mount points for docker
	inputs = os.path.join(cwd, "inputs")
	inputs = "-v " + inputs + ":/inputs "
	global outputs
	outputs = "-v " + outputs + ":/outputs "
	bifrost = "-v " + bifrost + ":/bifrost "

	global imputationserver
	imputationserver = "-v " + imputationserver + ":/data "
	mounts = inputs + outputs + bifrost + imputationserver

	# Build docker run command
	dockerCmd = "docker run --rm -t --name impute "
	imageName = "genepi/imputationserver:v1.4.1 "
	startImpute = "sh -c '/bifrost/scripts/startImpute.sh'"

	# Complete docker command
#	imputeJob = "sudo -u p1054-tsdfx " + dockerCmd + mounts + imageName + startImpute
	imputeJob = dockerCmd + mounts + imageName + startImpute
	subprocess.run(imputeJob, shell=True, check=True)
	# Start the imputation job

	# Create "done" file to show that the docker job exited (successfully)
	open(cwd + "done", 'a').close()
	print("Job has exited, 'done' file has been created")
	print("Removing lockfile")
	os.remove("lockfile")
	exitedDirName = re.sub("decrypted", "JobFinished", cwd)
	os.rename(cwd, exitedDirName)
	print("Work directory has been renamed from " + cwd + " to " + exitedDirName)
	print("Job finished successfully!")


def sczJob():
	print("Test scz run job")
	config = ConfigYml(yamlFileName)
	inputFilename = os.path.splitext(config.getValue(encryptedInputLabel))[0]
	print("Input filename: " + inputFilename)

	print("Running Rscript")

#	command = '''singularity exec -B /net/tsd-evs.tsd.usit.no/p1054/data/durable/BifrostWork/Tryggve_psych/tryggve.query1.v2:/INPUTS /tsd/p1054/data/durable/rmd-tidyverse_test.sif Rscript --verbose -e "rmarkdown::render('/INPUTS/tryggve.query1.v2.Rmd',params=list(arg1='/INPUTS',arg2='NOR'))" '''
	command = '''singularity exec -B /home/ubuntu/imputeDisk/01-workspace/00-temp/Tryggve_psych/tryggve.query1.v2:/INPUTS /home/ubuntu/imputeDisk/01-workspace/00-temp/rmd-tidyverse.sif Rscript --verbose -e "rmarkdown::render('/INPUTS/tryggve.query1.v2.Rmd',params=list(arg1='/INPUTS',arg2='NOR'))" '''
	subprocess.run(command, shell=True, check=True)
	global outputs
	copy('/home/ubuntu/imputeDisk/01-workspace/00-temp/Tryggve_psych/tryggve.query1.v2/tryggve.query1.v2.html', outputs)

	open(cwd + "done", 'a').close()
	print("Job has exited, 'done' file has been created")
	print("Removing lockfile")
	os.remove("lockfile")
	exitedDirName = re.sub("decrypted", "JobFinished", cwd)
	os.rename(cwd, exitedDirName)
	print("Work directory has been renamed from " + os.path.basename(cwd) + " to " + exitedDirName)
	print("Job finished successfully!")


def main():
	searchPath = glob(os.path.join(scratch, "decrypted-*"))

	# Setting current work directory to the "next one" that gets globbed when the searchPath variable is created
	# No fancy job prioritization is done
	i = 0
	for dir in searchPath:
		if os.path.isfile(dir + "/lockfile"):
			print(dir + " has a lockfile, a job is running, exiting now.")
			quit()

	print("No job is running, will process data in " + searchPath[0] + ", creating lockfile and attempting to start job.")
	global cwd
	cwd = os.path.join(searchPath[0])
	os.chdir(cwd)

	# Create lockfile
	open("lockfile", 'a').close()
	print("Created lock file so no other job can be started.")
	if not os.path.isdir("outputs"):
		os.makedirs("outputs")
		os.chmod("outputs", 0o777)
		print("Created outputs directory.")
	else:
		print("Outputs directory folder already exists.")

	global outputs
	outputs = os.path.join(cwd, "outputs", '')

	# Load the config file
	try:
		with open(yamlFileName) as file:
			global configYml
			configYml = yaml.load(file, Loader=yaml.FullLoader)
	# Print error message if file is not found
	except IOError:
		print("Config file not found, exiting")
		quit()

	if configYml[0]["jobType"] == "imputation":
		if configYml[0]["fileCopied"] == "True" and configYml[0]["decrypting"] == "True":
			print("impute")
			imputeJob()
		elif configYml[0]["fileCopied"] == "False" and configYml[0]["decrypting"] == "True":
			print("File decryption has started, files have not been transferred, waiting")
			print("Removing lockfile")
			os.remove('lockfile')
	elif configYml[0]["jobType"] == "schizophrenia":
		if configYml[0]["fileCopied"] == "True" and configYml[0]["decrypting"] == "True":
			# This gets executed when the jobType is schizophrenia and the fileCopied field is False in the config file
			print("scz")
			sczJob()

if __name__ == "__main__":
        main()
