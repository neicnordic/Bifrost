#!/usr/bin/env python3

import re
import os
import sys
import yaml
import hashlib
import argparse
import subprocess
from subprocess import Popen, PIPE
from shutil import copy
from datetime import datetime
from ConfigYml import ConfigYml

from constants import yamlFileName, basePath, schizophrenia, encryptedInputLabel

# Inputs from the command line
parser = argparse.ArgumentParser(description='Define job parameters for query submission')
parser.add_argument('--vcf', type=str, action='store',
					help='VCF file for imputation job submission')
parser.add_argument('--jobType', type=str, action='store', required=True,
					help='Define job type, imputation and schizophrenia are valid')
parser.add_argument('--country', type=str, action='store', required=True,
					help='Define in which country to run the job or jobs, currently only norway is valid')
parser.add_argument('--scriptId', type=str, action='store',
					help='Define what script to run (for schizophrenia use case)')
parser.add_argument('--remotePubKey', type=str, action='store',
					help='Supply the public key for encryption of input file')
parser.add_argument('--personalPubKey', type=str, action='store', required=True,
					help='Supply the public key for encryption of input file')
parser.add_argument('--personalSecKey', type=str, action='store',
					help='Supply the secret key for encryption of input file')
parser.add_argument('--sczConfig', type=str, action='store',
					help='Schizophrenia config/parameters file')
args = parser.parse_args()

def imputeJob(args):

	configYml = ConfigYml(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings', yamlFileName))
	vcf = args.vcf
	assert vcf.endswith(".c4gh"), "File name does not end with .c4gh, is the input file encrypted?"

	inputBasename = os.path.basename(vcf)
	personalPubKey = os.path.abspath(args.personalPubKey)

	# Open,close, read file and calculate md5sum on its contents
	with open(os.path.abspath(vcf), "rb") as fileToCheck:
		# read contents of the file
		data = fileToCheck.read()
		# pipe contents of the file through
		print("Calculating md5sum")
		md5Returned = hashlib.md5(data).hexdigest()

	configYml.initFromArgs(args)

	configYml.setValue("md5sum", md5Returned)
	configYml.setValue("personalPubKey", personalPubKey)

	configYml.dumpYAML(os.path.join("settings/", yamlFileName))

	# Define destination folder and input files, then send them
	inputDir = os.path.join("unprocessed-" + re.sub('\.vcf.gz.c4gh$', '', inputBasename), '')
	s3dest = "s3://bifrost-inputs/" + inputDir
	inputs = vcf, args.personalPubKey, os.path.join("settings", yamlFileName), s3dest
	inputs = ' '.join(inputs)
	transferFiles(inputs)

# Run scz job
def sczJob(args):
	configYml = ConfigYml(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings', yamlFileName))
	configYml.initFromArgs(args)

	encryptedConfig = encryptFile(os.path.abspath(args.sczConfig), os.path.abspath(args.personalPubKey), os.path.abspath(args.personalSecKey))
	encrInDir = os.path.abspath("unprocessed-" + datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
	os.mkdir(encrInDir)
	copy(encryptedConfig, encrInDir)
	copy(args.personalPubKey, encrInDir)

	configYml.setValue(encryptedInputLabel, encryptedConfig)

	configYml.dumpYAML(os.path.join(encrInDir, yamlFileName))

	# Run scp to copy the file
	transferFiles(encrInDir)


def encryptFile(filePath, remotePubKey, personalSecKey):
	# Encrypt input file
	print("Encrypting file")
	inputBaseName = os.path.basename(filePath)
	encryptedInput = inputBaseName + '.c4gh'

	encrypt = "crypt4gh encrypt --sk " + personalSecKey + " --recipient_pk " + remotePubKey + " < " + filePath + " > " + encryptedInput

	subprocess.run(encrypt, shell=True, check=True)
	#TODO check if encrypting was completed succesfully
	print("Input file has been encrypted")

	return encryptedInput

def transferFiles(inputFiles):
	s3command = "tsd-s3cmd put " + inputFiles
	print("We are now ready to transfer the input files, please enter your username, password and one time code \n")
	subprocess.run(s3command, shell=True, check=True)

def clearYml():
	# Clear the yaml file once the files have been uploaded
	with open(r'settings/config.yml', 'w') as file:
		documents = yaml.dump([{'country' : []}], file)

def main():
	clearYml()
	if args.jobType == "imputation":
		imputeJob(args)
		clearYml()
	elif args.jobType == "schizophrenia":
		sczJob(args)
		clearYml()

if __name__ == "__main__":
	main()
