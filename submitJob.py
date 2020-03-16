#!/usr/bin/env python

import yaml
import hashlib
import argparse

parser = argparse.ArgumentParser(description='Define job parameters for query submission')
parser.add_argument('--vcf', type = str, action = 'store', help = 'VCF file for imputation job submission')
parser.add_argument('--jobtype', type = str, action = 'store', help = 'Define job type, imputation and schizophrenia are valid')
parser.add_argument('--country', type = str, action = 'store', help = 'Define in which country to run the job or jobs')

args = parser.parse_args()
yam = "config.yml"

# Open the config file
with open("config.yml") as f:
	configYml = yaml.load(f)

# if statements that decide if the config file will define an imputation or schizophrenia job
if args.jobtype == "imputation":
	# Open,close, read file and calculate md5sum on its contents 
	with open(args.vcf) as fileToCheck:
		# read contents of the file
		data = fileToCheck.read()
		# pipe contents of the file through
		md5Returned = hashlib.md5(data).hexdigest()
# Add imputation specific lines to the config.yml file
	configYml[0]["inputfile"] = args.vcf
	configYml[0]["jobtype"] = args.jobtype
	configYml[0]["country"] = args.country
	configYml[0]["md5sum"] = md5Returned

# Add schizophrenia specific lines to the config.yml file
elif args.jobtype == "scz" or "schizophrenia":
	configYml[0]["jobtype"] = args.jobtype
	configYml[0]["country"] = args.country

# Write changes to the config.yml file
with open("config.yml", "w") as f:
	yaml.dump(configYml, f, default_flow_style=False)
