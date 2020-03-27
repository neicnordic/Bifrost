#!/usr/bin/env python2.7

import subprocess
import yaml
import hashlib
from shutil import copyfile
import os
import datetime

basepath = "/home/ubuntu/imputeDisk/01-workspace/00-temp/bifrost-testing/"
yml = basepath + "config.yml"

now = str(datetime.datetime.now())[:19]
now = now.replace(":","_")
now = now.replace(" ","-")

copydest = basepath + "testing-dir-" + now + "/"

# Load the config file
with open(basepath + "config.yml") as file:
	configYml = yaml.load(file, Loader=yaml.FullLoader)

# If statements that runs the imputation job when the filecopied field is False in the config file
if configYml[0]["jobtype"] == "imputation":
	if configYml[0]["filecopied"] == "False" and configYml[0]["decrypting"] == "False":
		# Put the encrypted input file in a variable with absolute path added
		inputfile = basepath + configYml[0]["encryptedinput"]

		# Verify that the file exists on disk
		try:
			print "Checking for encrypted input file"
			f = open(inputfile)
			print "Found encrypted input file"
		# Print error message if file is not found
		except IOError:
			print("Encrypted input file not found, exiting")
		# Close file handle if the file is found
		finally:
			f.close()

		# Change config file decrypting status to true
		print "Decrypting " + configYml[0]["encryptedinput"]
		configYml[0]["decrypting"] = "True"
		with open(yml, "w") as f:
			yaml.dump(configYml, f, default_flow_style=False)

		# Decrypt file with crypt4gh
		decrypt = "/usr/local/bin/crypt4gh decrypt --sk /home/ubuntu/.c4gh/nrec.sec <" + basepath + configYml[0]["encryptedinput"] + ">" + basepath + configYml[0]["inputfile"]
		subprocess.call(decrypt, shell=True)
		print "Done decrypting"

		# Put the input file in a variable with absolute path added
		inputfile = basepath + configYml[0]["inputfile"]

		# Verify that the input file exists on disk
		try:
			print "Checking for decrypted input file"
			f = open(inputfile)
			print "Found decrypted input file"
		# Print error message if file not found
		except IOError:
			print("Decrypted input file not found")
		# Close file handle if the file is found
		finally:
			f.close()

		# Calculate md5sum
		with open(inputfile) as fileToCheck:
			# Read contents of the file into variable
			print "Loading decrypted input file"
			data = fileToCheck.read()

			# Calculate md5sum to verify that the file has been transferred successfully
			print "Calculating md5sum"
			md5Returned = hashlib.md5(data).hexdigest()

			# Compare md5sum and copy files to the scratch disk if the md5sum is intact after decryption
			if configYml[0]["md5sum"] == md5Returned:
				print "File integrity is intact"

				# Create the destination directory
				os.mkdir(copydest)

				# Copy the file to the scratch disk
				print "Copying decrypted input files to " + copydest
				copyfile(inputfile, copydest + os.path.basename(inputfile))
				print "Copied input file to " + copydest + os.path.basename(inputfile)

				# Delete input file after copying it to the scratch disk
				print "Removing " + inputfile + "and " + basepath + configYml[0]["encryptedinput"]
				os.remove(inputfile)
				os.remove(basepath + configYml[0]["encryptedinput"])
				print "Deleted" + inputfile + "and " + basepath + configYml[0]["encryptedinput"] + "after transfer to scratch disk"

				# Copy yaml file to the scratch disk
				copyfile(yml, copydest + os.path.basename(yml))
				print "Copied yaml file to " + copydest + os.path.basename(yml)

				# Set the "filecopied" field to "True" so that the file does not get copied forever by the cron job
				configYml[0]["filecopied"] = "True"
				with open(yml, "w") as f:
					yaml.dump(configYml, f, default_flow_style=False)

				# Delete config file after transferring it
				os.remove(yml)
				print "Deleted config file after transfer to scratch disk"
				print "All done!"
			else:
				print "File is not the same, did the decryption fail? Exiting"

	elif configYml[0]["filecopied"] == "False" and configYml[0]["decrypting"] == "True":
		print "File decryption has started, files have not been transferred, waiting"

	elif configYml[0]["filecopied"] == "True" and configYml[0]["decrypting"] == "True":
		print "Files have already been decrypted and copied to a new directory, why wasn't the config file copied to the scratch disk?"

# This gets executed when the jobtype is schizophrenia and the filecopied field is False in the config file
elif configYml[0]["jobtype"] == "schizophrenia" and configYml[0]["filecopied"] == "False":
	print "Test"
