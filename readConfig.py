#!/usr/bin/env python2.7

from glob import glob
import re
import subprocess
import yaml
import hashlib
from shutil import copyfile, copy
import os
import datetime

from constants import yamlFileName, basePath, remotePrivateKeyPath, inputFile, jobType, country, md5sum, encrMd5sum, fileCopied, decrypting, \
    encryptedInput, scriptId, schizophrenia

now = str(datetime.datetime.now())[:19]
now = now.replace(":","_")
now = now.replace(" ","-")

def decryptFile(configYml, inputFolder, yml):
	encryptedFile = os.path.join(inputFolder, configYml.getValue(encryptedInput))
	# Verify that the file exists on disk
	if not os.path.isfile(encryptedFile):
		print("Encrypted file " + encryptedFile + " not found, exiting")
		quit()

	# Change config file decrypting status to true
	print("Decrypting " + configYml.getValue(encryptedInput))

	# configYml.setValue(decrypting) = "True"
	# configYml.dumpYAML(yml)

	decryptedFilePath = os.path.join(inputFolder,
									 os.path.splitext(configYml.getValue(encryptedInput))[0])
	# Decrypt file with crypt4gh
	# TODO Make this as general and easy as possible to configure
	# TODO Make the script exit if the decryption fails with the "No supported encryption method" error message, this means that the sender had the wrong public key during encryption before sending the file
	decrypt = "crypt4gh decrypt --sk " + remotePrivateKeyPath + " < " + encryptedFile + " > " + decryptedFilePath

	subprocess.call(decrypt, shell=True)
	print("Done decrypting")

	# Verify that the input file exists on disk
	try:
		f = open(decryptedFilePath)
	# Print error message if file not found
	except IOError:
		print("Decrypted input file not found")
	# Close file handle if the file is found
	finally:
		f.close()

	print('File can be opened')

	return decryptedFilePath


def main():
	searchPath = glob(os.path.join(basePath, "encrypted-*"))
	if len(searchPath) >= 1:
		print("Found directory with encrypted data")
	else:
		print("No directory with encrypted data found, exiting")
		quit()

	copydest = re.sub("encrypted", "decrypted", searchPath[0])
	copydest = os.path.abspath(copydest) + "/"

	yamlConfigPath = os.path.join(searchPath[0], yamlFileName)
	# Load the config file
	try:
		with open(yamlConfigPath) as file:
			configYml = yaml.load(file, Loader=yaml.FullLoader)
	# Print error message if file is not found
	except IOError:
		print("Config file not found, nothing to do, exiting")
		quit()

	# If statements that runs the imputation job when the fileCopied field is False in the config file
	if configYml[0]["jobType"] == "imputation":
		while True:
			if configYml[0]["fileCopied"] == "False" and configYml[0]["decrypting"] == "False":
				# Put the encrypted input file in a variable with absolute path added
				encryptedFile = searchPath[0] + "/" + configYml[0]["encryptedInput"]

				# Verify that the file exists on disk
				try:
					f = open(encryptedFile)
					print("Preparing to calculate md5sum on encrypted input file")
					data = f.read()

					# Calculate md5sum to verify that the file has been transferred successfully
					print("Calculating md5sum on encrypted input file")
					md5Returned = hashlib.md5(data).hexdigest()
					print("Finished calculating md5sum on encrypted input file")

					# Compare md5sum and copy files to the scratch disk if the md5sum is intact after decryption
					if configYml[0]["encrMd5sum"] == md5Returned:
						print("md5sum on encrypted input file is correct, proceeding.")
					else:
						print(
							"md5sum on encrypted input file is not correct, file may be incomplete, exiting and retrying next time")
						quit()

				# Print error message if file is not found
				except IOError:
					print("Encrypted input file not found, exiting")
				# Close file handle if the file is found
				finally:
					f.close()

				# Change config file decrypting status to true
				print("Decrypting " + configYml[0]["encryptedInput"])
				configYml[0]["decrypting"] = "True"
				with open(yamlConfigPath, "w") as f:
					yaml.dump(configYml, f, default_flow_style=False)

				# Decrypt file with crypt4gh
				# TODO Make this as general and easy as possible to configure
				# TODO Make the script exit if the decryption fails with the "No supported encryption method" error message, this means that the sender had the wrong public key during encryption before sending the file
				decrypt = "/usr/local/bin/crypt4gh decrypt --sk /home/ubuntu/.c4gh/nrec.sec < " + encryptedFile + " > " + \
						  searchPath[0] + "/" + configYml[0]["inputFile"]
				subprocess.call(decrypt, shell=True)
				print("Done decrypting")

				# Put the input file in a variable with absolute path added
				decryptedFile = searchPath[0] + "/" + configYml[0]["inputFile"]

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

						# Create the destination directory
						os.mkdir(copydest)

						# Copy the file to the scratch disk
						print("Copying decrypted input files to " + copydest)
						copyfile(decryptedFile, copydest + os.path.basename(decryptedFile))
						print("Copied input file to " + copydest + os.path.basename(decryptedFile))

						# Calculate md5sum
						while True:
							with open(copydest + os.path.basename(decryptedFile)) as fileToCheck:
								# TODO make this into a function
								# Read contents of the file into variable
								print("Loading decrypted input file")
								data = fileToCheck.read()

								# Calculate md5sum to verify that the file has been transferred successfully
								print("Calculating md5sum")
								md5Returned = hashlib.md5(data).hexdigest()

								if configYml[0]["md5sum"] == md5Returned:
									# TODO make this into a function
									# Delete input file after copying it to the scratch disk
									print("Removing " + decryptedFile + " and " + searchPath[
										0] + "/" + configYml[0]["encryptedInput"])
									os.remove(decryptedFile)
									os.remove(searchPath[0] + "/" + configYml[0]["encryptedInput"])
									print("Deleted " + decryptedFile + " and " + searchPath[
										0] + "/" + configYml[0][
											  "encryptedInput"] + " after transfer to scratch disk")

									# Copy yaml file to the scratch disk
									copyfile(yamlConfigPath, copydest + os.path.basename(yamlConfigPath))
									print("Copied yaml file to " + copydest + os.path.basename(
										yamlConfigPath))

									# Set the "fileCopied" field to "True" so that the file does not get copied forever by the cron job
									configYml[0]["fileCopied"] = "True"
									with open(copydest + os.path.basename(yamlConfigPath), "w") as f:
										yaml.dump(configYml, f, default_flow_style=False)

									# Delete config file after transferring it
									os.remove(yamlConfigPath)
									os.rmdir(searchPath[0])
									print("Deleted config file after transfer to scratch disk")
									print("All done!")
									break
								else:
									# TODO make this into a function
									print("File transfer failed, retrying")
									# Copy the file to the scratch disk
									print("Copying decrypted input files to " + copydest)
									copyfile(inputFile, copydest + os.path.basename(inputFile))
									print("Copied input file to " + copydest + os.path.basename(
										inputFile))
					else:
						print("File is not the same, did the decryption fail? Exiting")
				# Probably go back to the decryption step here

			elif configYml[0]["fileCopied"] == "False" and configYml[0]["decrypting"] == "True":
				print("File decryption has started, files have not been transferred, waiting")
				break

			elif configYml[0]["fileCopied"] == "True" and configYml[0]["decrypting"] == "True":
				break

	# This gets executed when the jobType is schizophrenia and the fileCopied field is False in the config file
	else:
		configYml = configYml(yamlConfigPath)
		if configYml.getValue(jobType) == schizophrenia and configYml.getValue(fileCopied) == "False":
			print("Test scz")
			inputFolder = searchPath[0]
			if configYml.getValue(fileCopied) == "False" and configYml.getValue(decrypting) == "False":
				decryptedFilePath = decryptFile(configYml, inputFolder, yamlConfigPath)

				if not os.path.isdir(copydest):
					os.mkdir(copydest)

				# Copy the file to the scratch disk
				print("Copying decrypted input files to " + copydest)
				copy(decryptedFilePath, copydest)

				# print("Removing " + decryptedFile + " and " + searchPath[0] + "/" + configYml[0]["encryptedInput"])
				# os.remove(decryptedFile)
				# os.remove(searchPath[0] + "/" + configYml[0]["encryptedInput"])
				# print("Deleted " + decryptedFile + " and " + searchPath[0] + "/" + configYml[0]["encryptedInput"] + " after transfer to scratch disk")

				# Copy yaml file to the scratch disk
				copy(yamlConfigPath, copydest)
				print("Copied yaml file to " + copydest)

				# Set the "fileCopied" field to "True" so that the file does not get copied forever by the cron job
				# configYml.setValue(fileCopied) = "True"
				# configYml.dumpYAML(copydest, os.path.basename(yamlConfigPath))

				# Delete config file after transferring it
				# os.remove(yml)
				# os.rmdir(searchPath[0])
				# print("Deleted config file after transfer to scratch disk")
				print("All done!")

if __name__ == "__main__":
	main()
