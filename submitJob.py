#!/usr/bin/env python2.7

import re
import os
import subprocess
import sys
import yaml
import hashlib
import argparse
from paramiko import SSHClient, RSAKey
from scp import SCPClient
from shutil import copy
from datetime import datetime
from configYml import configYml

from constants import yamlFileName, basePath, schizophrenia, encryptedInput

def submitJob(args):
	# if statements that decide if the config file will define an imputation or schizophrenia job
	if args.jobType == "imputation":
		# Open the config file
		with open(yamlFileName) as f:
			configYml = yaml.load(f, Loader=yaml.FullLoader)
		# Open,close, read file and calculate md5sum on its contents
		vcf = os.path.abspath(args.vcf)
		with open(vcf) as fileToCheck:
			# read contents of the file
			data = fileToCheck.read()
			# pipe contents of the file through
			print("Calculating md5sum")
			md5Returned = hashlib.md5(data).hexdigest()

		inputBasename = os.path.basename(vcf)
		pubKey = os.path.abspath(args.pubKey)
		pubKeyBasename = os.path.basename(pubKey)

		# Add imputation specific lines to the config.yml file
		configYml[0]["jobType"] = args.jobType
		configYml[0]["country"] = args.country
		configYml[0]["md5sum"] = md5Returned
		configYml[0]["pubkey"] = pubKeyBasename
		configYml[0]["inputFile"] = inputBasename
		configYml[0]["fileCopied"] = "False"
		configYml[0]["decrypting"] = "False"

		# Write changes to the config.yml file
		with open(yamlFileName, "w") as f:
			yaml.dump(configYml, f, default_flow_style=False)
		inputDir = "unprocessed-" + re.sub('\.vcf.gz.c4gh$', '', inputBasename) + "/"
		s3dest = "s3://impute-inputs/" + inputDir
		s3command = "tsd-s3cmd put " + vcf + " " + pubKey + " " + yamlFileName + " " + s3dest
		subprocess.call(s3command, shell=True)
		quit()

	# Add schizophrenia specific lines to the config.yml file
	elif args.jobType == schizophrenia:
		configYml = configYml(yamlFileName)
		configYml.initFromArgs(args)

		encryptedConfig = encryptFile(os.path.abspath(args.sczConfig), os.path.abspath(args.pubKey), os.path.abspath(args.secKey))
		encrInDir = os.path.abspath("encrypted-" + datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
		os.mkdir(encrInDir)
		copy(encryptedConfig, encrInDir)

		configYml.setValue(encryptedInput, encryptedConfig)

		configYml.dumpYAML(os.path.join(encrInDir, yamlFileName))

		# Run scp to copy the file
		transferFiles(encrInDir)


def transferFiles(inputFolder):
	ssh = SSHClient()
	ssh.load_system_host_keys()
	#key = RSAKey.from_private_key_file("/Users/radmilko/.ssh/id_rsa", '')
	#ssh.connect('158.39.77.181', username="centos", pkey=key)
	ssh.connect('bifrost', username="ubuntu")

	scp = SCPClient(ssh.get_transport(), progress=progress)

	# Do the actual file transfer
	print("Transferring files")
	scp.put([inputFolder], remote_path=basePath, recursive=True)
	scp.close()


def encryptFile(filePath, pubKey, secKey):
	# Encrypt input file
	print("Encrypting file")
	inputBaseName = os.path.basename(filePath)
	encryptedInput = inputBaseName + '.c4gh'

	encrypt = "crypt4gh encrypt --sk " + secKey + " --recipient_pk " + pubKey + " < " + filePath + " > " + encryptedInput
	subprocess.call(encrypt, shell=True)
	#TODO check if encrypting was completed succesfully
	print("Input file has been encrypted")

	return encryptedInput

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
						help='Define in which country to run the job or jobs')
	parser.add_argument('--scriptId', type=str, action='store',
						help='Define what script to run (for schizophrenia use case)')
	parser.add_argument('--pubKey', type=str, action='store',
						help='Supply the public key for encryption of input file')
	parser.add_argument('--secKey', type=str, action='store',
						help='Supply the public key for encryption of input file')
	parser.add_argument('--sczConfig', type=str, action='store',
						help='Schizophrenia config/parameters file')

	args = parser.parse_args()
	submitJob(args)


if __name__ == "__main__":
	main()
