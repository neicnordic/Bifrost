#!/usr/bin/env python2.7

from glob import glob
import re
import subprocess
import yaml
import hashlib
from shutil import copyfile
import os
import datetime

# TODO Put this path in a separate config file?
basepath = "/home/ubuntu/imputeDisk/01-workspace/00-temp/bifrost-testing/"

now = str(datetime.datetime.now())[:19]
now = now.replace(":","_")
now = now.replace(" ","-")

searchpath = glob(basepath + "encrypted-*")
if len(searchpath) >= 1:
	print "Found directory with encrypted data"
else:
	print "No directory with encrypted data found, exiting"
	quit()

yml = searchpath[0] + "/config.yml"

copydest = re.sub("encrypted", "decrypted", searchpath[0])
copydest = os.path.abspath(copydest) + "/"

# Load the config file
try:
	with open(yml) as file:
		configYml = yaml.load(file, Loader=yaml.FullLoader)
# Print error message if file is not found
except IOError:
	print("Config file not found, nothing to do, exiting")
	quit()

# If statements that runs the imputation job when the filecopied field is False in the config file
if configYml[0]["jobtype"] == "imputation":
	while True:
		if configYml[0]["filecopied"] == "False" and configYml[0]["decrypting"] == "False":
			# Put the encrypted input file in a variable with absolute path added
			encryptedFile = searchpath[0] + "/" + configYml[0]["encryptedinput"]

			# Verify that the file exists on disk
			try:
				f = open(encryptedFile)
				print "Preparing to calculate md5sum on encrypted input file"
				data = f.read()

				# Calculate md5sum to verify that the file has been transferred successfully
				print "Calculating md5sum on encrypted input file"
				md5Returned = hashlib.md5(data).hexdigest()
				print "Finished calculating md5sum on encrypted input file"

				# Compare md5sum and copy files to the scratch disk if the md5sum is intact after decryption
				if configYml[0]["encryptedmd5sum"] == md5Returned:
					print "md5sum on encrypted input file is correct, proceeding."
				else:
					print "md5sum on encrypted input file is not correct, file may be incomplete, exiting and retrying next time"
					quit()

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
			# TODO Make this as general and easy as possible to configure
			# TODO Make the script exit if the decryption fails with the "No supported encryption method" error message, this means that the sender had the wrong public key during encryption before sending the file
			decrypt = "/usr/local/bin/crypt4gh decrypt --sk /home/ubuntu/.c4gh/nrec.sec < " + encryptedFile + " > " + searchpath[0] + "/" + configYml[0]["inputfile"]
			subprocess.call(decrypt, shell=True)
			print "Done decrypting"

			# Put the input file in a variable with absolute path added
			decryptedFile = searchpath[0] + "/" + configYml[0]["inputfile"]

			# Verify that the input file exists on disk
			try:
				f = open(decryptedFile)
			# Print error message if file not found
			except IOError:
				print("Decrypted input file not found")
			# Close file handle if the file is found
			finally:
				f.close()

			# Calculate md5sum
			with open(decryptedFile) as fileToCheck:
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

					# Create the destination directory
					os.mkdir(copydest)

					# Copy the file to the scratch disk
					print "Copying decrypted input files to " + copydest
					copyfile(decryptedFile, copydest + os.path.basename(decryptedFile))
					print "Copied input file to " + copydest + os.path.basename(decryptedFile)

					# Calculate md5sum
					while True:
						with open(copydest + os.path.basename(decryptedFile)) as fileToCheck:
							# TODO make this into a function
							# Read contents of the file into variable
							print "Loading decrypted input file"
							data = fileToCheck.read()

							# Calculate md5sum to verify that the file has been transferred successfully
							print "Calculating md5sum"
							md5Returned = hashlib.md5(data).hexdigest()

							if configYml[0]["md5sum"] == md5Returned:
								# TODO make this into a function
								# Delete input file after copying it to the scratch disk
								print "Removing " + decryptedFile + " and " + searchpath[0] + "/" + configYml[0]["encryptedinput"]
								os.remove(decryptedFile)
								os.remove(searchpath[0] + "/" + configYml[0]["encryptedinput"])
								print "Deleted " + decryptedFile + " and " + searchpath[0] + "/" + configYml[0]["encryptedinput"] + " after transfer to scratch disk"

								# Copy yaml file to the scratch disk
								copyfile(yml, copydest + os.path.basename(yml))
								print "Copied yaml file to " + copydest + os.path.basename(yml)

								# Set the "filecopied" field to "True" so that the file does not get copied forever by the cron job
								configYml[0]["filecopied"] = "True"
								with open(copydest + os.path.basename(yml), "w") as f:
									yaml.dump(configYml, f, default_flow_style=False)

								# Delete config file after transferring it
								os.remove(yml)
								os.rmdir(searchpath[0])
								print "Deleted config file after transfer to scratch disk"
								print "All done!"
								break
							else:
								# TODO make this into a function
								print "File transfer failed, retrying"
								# Copy the file to the scratch disk
								print "Copying decrypted input files to " + copydest
								copyfile(inputfile, copydest + os.path.basename(inputfile))
								print "Copied input file to " + copydest + os.path.basename(inputfile)
				else:
					print "File is not the same, did the decryption fail? Exiting"
					# Probably go back to the decryption step here

		elif configYml[0]["filecopied"] == "False" and configYml[0]["decrypting"] == "True":
			print "File decryption has started, files have not been transferred, waiting"
			break

		elif configYml[0]["filecopied"] == "True" and configYml[0]["decrypting"] == "True":
			break

# This gets executed when the jobtype is schizophrenia and the filecopied field is False in the config file
elif configYml[0]["jobtype"] == "schizophrenia" and configYml[0]["filecopied"] == "False":
	print "Test"
