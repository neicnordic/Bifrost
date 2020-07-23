#!/usr/bin/env python2.7

import re
import os
import sys
import yaml
import hashlib
import argparse
import subprocess
from shutil import copy
from datetime import datetime
from ConfigYml import ConfigYml

from constants import yamlFileName, basePath, schizophrenia, encryptedInputLabel

def submitJob(args):
	# if statements that decide if the config file will define an imputation or schizophrenia job
	if args.jobType == "imputation":
		# Open the config file
		with open("settings/" + yamlFileName) as f:
			configYml = yaml.load(f, Loader=yaml.FullLoader)

		vcf = os.path.abspath(args.vcf)
		inputBasename = os.path.basename(vcf)
		personalPubKey = os.path.abspath(args.personalPubKey)
		personalPubKeyBasename = os.path.basename(personalPubKey)

		encryptedInput = os.path.basename(vcf) + '.c4gh'
		encrInDir = os.path.abspath("encrypted-" + re.sub('\.vcf.gz$', '', inputBasename))

		print("Encrypting file")

		encrypt = "crypt4gh encrypt --sk " + args.personalSecKey + " --recipient_pk " + args.remotePubKey + " < " + vcf + " > " + encryptedInput
		subprocess.call(encrypt, shell=True)
		print(os.path.abspath(encryptedInput))

		# Open,close, read file and calculate md5sum on its contents
		with open(os.path.abspath(encryptedInput)) as fileToCheck:
			# read contents of the file
			data = fileToCheck.read()
			# pipe contents of the file through
			print("Calculating md5sum")
			md5Returned = hashlib.md5(data).hexdigest()

		# Add imputation specific lines to the config.yml file
		configYml[0]["jobType"] = args.jobType
		configYml[0]["country"] = args.country
		configYml[0]["md5sum"] = md5Returned
		configYml[0]["pubKey"] = personalPubKeyBasename
		configYml[0]["encryptedInput"] = encryptedInput
		configYml[0]["fileCopied"] = "False"
		configYml[0]["decrypting"] = "False"

		# Write changes to the config.yml file
		with open("settings/" + yamlFileName, "w") as f:
			yaml.dump(configYml, f, default_flow_style=False)

		inputDir = "unprocessed-" + re.sub('\.vcf.gz$', '', inputBasename) + "/"
		s3dest = "s3://bifrost-inputs/" + inputDir
		s3command = "tsd-s3cmd put " + encryptedInput + " " + args.personalPubKey + " " + "settings/" + yamlFileName + " " + s3dest
		subprocess.call(s3command, shell=True)
		os.remove(encryptedInput)
		quit()

	# Add schizophrenia specific lines to the config.yml file
	elif args.jobType == schizophrenia:
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
	subprocess.call(encrypt, shell=True)
	#TODO check if encrypting was completed succesfully
	print("Input file has been encrypted")

	return encryptedInput


def transferFiles(inputFolder):
	s3dest = "s3://bifrost-inputs"
	s3command = "tsd-s3cmd put --recursive " + inputFolder + " " + s3dest
	subprocess.call(s3command, shell=True)

# SCPCLient takes a paramiko transport as an argument
def progress(filename, size, sent):
	sys.stdout.write("%s\'s progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )


def main():
	parser = argparse.ArgumentParser(description='Define job parameters for query submission')
	parser.add_argument('--vcf', type=str, action='store',
						help='VCF file for imputation job submission')
	parser.add_argument('--jobType', type=str, action='store',
						help='Define job type, imputation and schizophrenia are valid')
	parser.add_argument('--country', type=str, action='store',
						help='Define in which country to run the job or jobs, currently only norway is valid')
	parser.add_argument('--scriptId', type=str, action='store',
						help='Define what script to run (for schizophrenia use case)')
	parser.add_argument('--remotePubKey', type=str, action='store',
						help='Supply the public key for encryption of input file')
	parser.add_argument('--personalPubKey', type=str, action='store',
						help='Supply the public key for encryption of input file')
	parser.add_argument('--personalSecKey', type=str, action='store',
						help='Supply the secret key for encryption of input file')
	parser.add_argument('--sczConfig', type=str, action='store',
						help='Schizophrenia config/parameters file')

	args = parser.parse_args()
	submitJob(args)


if __name__ == "__main__":
	main()
