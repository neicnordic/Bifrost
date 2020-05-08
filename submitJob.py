#!/usr/bin/env python3

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

from Constants import YAML_FILENAME, BASEPATH

def submitJob(args):
	# Open the config file
	with open(YAML_FILENAME) as f:
		configYml = yaml.load(f, Loader=yaml.FullLoader)

	# if statements that decide if the config file will define an imputation or schizophrenia job
	if args.jobtype == "imputation":
		# Open,close, read file and calculate md5sum on its contents
		vcf = os.path.abspath(args.vcf)
		with open(vcf) as fileToCheck:
			# read contents of the file
			data = fileToCheck.read()
			# pipe contents of the file through
			print("Calculating md5sum")
			md5Returned = hashlib.md5(data).hexdigest()

		# Encrypt input file
		print("Encrypting file")
		pubkey = os.path.abspath(args.pubkey)
		seckey = os.path.abspath(args.seckey)
		inputBasename = os.path.basename(vcf)
		encryptedInput = inputBasename + '.c4gh'
		encrInDir = os.path.abspath("encrypted-" + re.sub('\.vcf.gz$', '', inputBasename))
		os.mkdir(encrInDir)
		os.chdir(encrInDir)
		encrypt = "crypt4gh encrypt --sk " + seckey + " --recipient_pk " + pubkey + " < " + vcf + " > " + encryptedInput
		subprocess.call(encrypt, shell=True)
		print("Input file has been encrypted")

		with open(encryptedInput) as fileToCheck:
			# read contents of the file
			data = fileToCheck.read()
			# pipe contents of the file through
			print("Calculating encrypted input file md5sum")
			encryptedMd5Returned = hashlib.md5(data).hexdigest()

		# Add imputation specific lines to the config.yml file
		configYml[0]["inputfile"] = os.path.basename(vcf)
		configYml[0]["jobtype"] = args.jobtype
		configYml[0]["country"] = args.country
		configYml[0]["md5sum"] = md5Returned
		configYml[0]["encryptedmd5sum"] = encryptedMd5Returned
		configYml[0]["filecopied"] = "False"
		configYml[0]["decrypting"] = "False"
		configYml[0]["encryptedinput"] = encryptedInput

	# Add schizophrenia specific lines to the config.yml file
	elif args.jobtype == "schizophrenia":
		configYml[0]["jobtype"] = args.jobtype
		configYml[0]["country"] = args.country
		configYml[0]["scriptid"] = args.scriptid
		configYml[0]["filecopied"] = "False"
		configYml[0]["decrypting"] = "False"

		encryptedConfig = encryptFile(os.path.abspath(args.sczconfig), os.path.abspath(args.pubkey), os.path.abspath(args.seckey))
		encrInDir = os.path.abspath("encrypted-" + datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
		os.mkdir(encrInDir)
		copy(encryptedConfig, encrInDir)

		configYml[0]["encryptedinput"] = encryptedConfig

	# Write changes to the config.yml file
	with open(os.path.join(encrInDir, YAML_FILENAME), "w") as f:
		yaml.dump(configYml, f, default_flow_style=False)

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
	scp.put([inputFolder], remote_path=BASEPATH, recursive=True)
	scp.close()


def encryptFile(filePath, pubkey, seckey):
	# Encrypt input file
	print("Encrypting file")
	inputBasename = os.path.basename(filePath)
	encryptedInput = inputBasename + '.c4gh'

	encrypt = "crypt4gh encrypt --sk " + seckey + " --recipient_pk " + pubkey + " < " + filePath + " > " + encryptedInput
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
	parser.add_argument('--jobtype', type=str, action='store',
						help='Define job type, imputation and schizophrenia are valid')
	parser.add_argument('--country', type=str, action='store',
						help='Define in which country to run the job or jobs')
	parser.add_argument('--scriptid', type=str, action='store',
						help='Define what script to run (for schizophrenia use case)')
	parser.add_argument('--pubkey', type=str, action='store',
						help='Supply the public key for encryption of input file')
	parser.add_argument('--seckey', type=str, action='store',
						help='Supply the public key for encryption of input file')
	parser.add_argument('--sczconfig', type=str, action='store',
						help='Schizophrenia config/parameters file')

	args = parser.parse_args()
	submitJob(args)


if __name__ == "__main__":
	main()
