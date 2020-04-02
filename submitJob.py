#!/usr/bin/env python

import os
import subprocess
import sys
import yaml
import hashlib
import argparse
from paramiko import SSHClient
from scp import SCPClient

parser = argparse.ArgumentParser(description='Define job parameters for query submission')
parser.add_argument('--vcf', type = str, action = 'store', help = 'VCF file for imputation job submission')
parser.add_argument('--jobtype', type = str, action = 'store', help = 'Define job type, imputation and schizophrenia are valid')
parser.add_argument('--country', type = str, action = 'store', help = 'Define in which country to run the job or jobs')
parser.add_argument('--scriptid', type = str, action = 'store', help = 'Define what script to run (for schizophrenia use case)')
parser.add_argument('--pubkey', type = str, action = 'store', help = 'Supply the public key for encryption of input file')
parser.add_argument('--seckey', type = str, action = 'store', help = 'Supply the public key for encryption of input file')

args = parser.parse_args()
yam = "config.yml"

# Open the config file
with open("config.yml") as f:
	configYml = yaml.load(f, Loader=yaml.FullLoader)

# if statements that decide if the config file will define an imputation or schizophrenia job
if args.jobtype == "imputation":
	# Open,close, read file and calculate md5sum on its contents
	with open(args.vcf) as fileToCheck:
		# read contents of the file
		data = fileToCheck.read()
		# pipe contents of the file through
		print "Calculating md5sum"
		md5Returned = hashlib.md5(data).hexdigest()

# Encrypt input file
	print("Encrypting file")
	# TODO remove hardcoded paths
	subprocess.call("(crypt4gh encrypt --sk /home/oskar/01-workspace/00-temp/Bifrost/secretEmblaKey --recipient_pk /home/oskar/01-workspace/00-temp/Bifrost/nrec.pub <" + args.vcf + "> /home/oskar/01-workspace/00-temp/Bifrost/encryptedVCF.c4gh)", shell=True)
	# TODO remove hardcoded name
	encryptedInput = 'encryptedVCF.c4gh'
	print("Encrypted file")

# Add imputation specific lines to the config.yml file
	configYml[0]["inputfile"] = os.path.basename(args.vcf)
	configYml[0]["jobtype"] = args.jobtype
	configYml[0]["country"] = args.country
	configYml[0]["md5sum"] = md5Returned
	configYml[0]["filecopied"] = "False"
	configYml[0]["decrypting"] = "False"
	configYml[0]["encryptedinput"] = encryptedInput

# Add schizophrenia specific lines to the config.yml file
elif args.jobtype == "schizophrenia":
	configYml[0]["jobtype"] = args.jobtype
	configYml[0]["country"] = args.country
	configYml[0]["scriptid"] = args.scriptid
	configYml[0]["filecopied"] = "False"
	#TODO input params for the script? Command line args or some sort of config input file?

# Write changes to the config.yml file
with open("config.yml", "w") as f:
	yaml.dump(configYml, f, default_flow_style=False)

# Do ssh things to send the files
def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

# Run scp to copy the file
ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect('ip.number', username="username")

# SCPCLient takes a paramiko transport as an argument
def progress(filename, size, sent):
    sys.stdout.write("%s\'s progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )
scp = SCPClient(ssh.get_transport(), progress=progress)

# Do the actual file transfer
print "Transferring files to TSD"
scp.put([encryptedInput, yam], remote_path='/home/ubuntu/01-workspace/00-temp/bifrost-testing')
scp.close()
