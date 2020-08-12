#!/usr/bin/env python3

from glob import glob
import re
import sys
import subprocess
import yaml
import hashlib
from shutil import copyfile, copy
import os
import datetime
import errno
from ConfigYml import ConfigYml

from constants import yamlFileName, basePath, tsdSecretKeyPath, inputFile, jobType, country, md5sum, encrMd5sum, fileCopied, decrypting, \
    encryptedInputLabel, scriptId, schizophrenia, crypt4gh, scratch, unprocessed, personalPubKey

def decryptFile(configYml, inputFolder, yml):
	encryptedFile = os.path.join(inputFolder, configYml.getValue(encryptedInputLabel))
	# Verify that the file exists on disk
	if not os.path.isfile(encryptedFile):
		print("Encrypted file " + encryptedFile + " not found, exiting")
		quit()

	# Change config file decrypting status to true
	print("Decrypting " + configYml.getValue(encryptedInputLabel))

	decryptedFilePath = os.path.join(inputFolder,
		os.path.splitext(configYml.getValue(encryptedInputLabel))[0])
	# Decrypt file with crypt4gh
	# TODO Make this as general and easy as possible to configure
	# TODO Make the script exit if the decryption fails with the "No supported encryption method" error message, this means that the sender had the wrong public key during encryption before sending the file
	decrypt = crypt4gh + " decrypt --sk " + tsdSecretKeyPath + " < " + encryptedFile + " > " + decryptedFilePath

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


def calcMd5Sum(encryptedFile):
	# Verify that the encrypted file has been completely transferred before anything else is done
	try:
		f = open(encryptedFile, "rb")
		data = f.read()

		# Calculate md5sum to verify that the file has been transferred successfully
		print("Calculating md5sum on encrypted input file")
		md5Returned = hashlib.md5(data).hexdigest()

		# Compare md5sums
		if not configYml.getValue(md5sum) == md5Returned:
			print("md5sum on encrypted input file is not correct, file transfer may be incomplete, exiting and retrying next time")
			sys.exit(1)

	# Print error message if file is not found
	except IOError:
		print("Encrypted input file not found, exiting")
	# Close file handle if the file is found
	finally:
		f.close()

def imputation(yamlConfigPath, dir):
	copyDest = os.path.join(scratch, os.path.basename(dir), '')

	# Put the encrypted input file in a variable with absolute path added
	encryptedFile = os.path.join(dir, configYml.getValue(encryptedInputLabel))

	calcMd5Sum(encryptedFile)

	# Create the destination directory
	try:
		os.mkdir(copyDest)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	# Copy encrypted input file to the scratch disk
	copyfile(encryptedFile, copyDest + os.path.basename(encryptedFile))
	encryptedFile = os.path.join(copyDest, os.path.basename(encryptedFile))

	# Copy pubkey to the scratch disk
	pubKey = os.path.join(dir, configYml.getValue(personalPubKey))
	copyfile(pubKey, copyDest + os.path.basename(pubKey))
	pubKey = os.path.join(copyDest, os.path.basename(pubKey))

	calcMd5Sum(encryptedFile)
	os.chdir(copyDest)

	# Change config file decrypting status to true
	configYml.setValue(decrypting, "True")

	# Decrypt file with crypt4gh
	# TODO Make this as general and easy as possible to configure
	# TODO Make the script exit if the decryption fails with the "No supported encryption method" error message, this means that the sender had the wrong public key during encryption before sending the file
	decryptedFile = os.path.join(copyDest, re.sub('\.c4gh$', '', configYml.getValue(encryptedInputLabel)))
	decrypt = crypt4gh + " decrypt --sk " + tsdSecretKeyPath + " < " + encryptedFile + " > " + decryptedFile
	try:
		subprocess.run(decrypt, shell=True, check=True)
	except subprocess.CalledProcessError:
		print("\nDecryption failed")
		print("This is the failing command: " + decrypt)
		configYml.setValue(decrypting, "False")
		configYml.dumpYAML(os.path.join(scratch, yamlFileName))
		sys.exit(1)

	# Finally copy the yaml file to the scratch disk
	copyfile(yamlConfigPath, copyDest + os.path.basename(yamlConfigPath))

	# Rename the copy directory destination when the input file has been decrypted
	decryptedDir = re.sub("unprocessed", "decrypted", copyDest)
	os.rename(copyDest, decryptedDir)

	# Change the copied config file in its new directory to "fileCopied = True"
	# once the file has been decrypted
	configYml.setValue(fileCopied, "True")
	configYml.dumpYAML(os.path.join(scratch, yamlFileName))

	# Verify that the input file exists on disk
	try:
		f = open(os.path.join(decryptedDir, os.path.basename(decryptedFile)))
	# Print error message if file not found
	except IOError:
		print("Decrypted input file not found, exiting")
	# Close file handle if the file is found
	finally:
		f.close()

	# Change the config file in the "cloned-inputs" directory to "fileCopied = True"
	# once the file has been decrypted and copied to its new directory
	configYml.setValue(fileCopied, "True")
	configYml.dumpYAML(os.path.join(dir, yamlFileName))

	print("All done!")

def runSchizophrenia(yamlConfigPath, dir):
	# This gets executed when the jobType is schizophrenia and the fileCopied field is False in the config file
	inputFolder = dir

	destDirName = re.sub('unprocessed', 'decrypted', os.path.basename(dir))
	scratchPath = os.path.join(scratch, destDirName)

	if not os.path.isdir(scratchPath):
		os.mkdir(scratchPath)

	encryptedFile = os.path.join(inputFolder, configYml.getValue(encryptedInputLabel))
	copy(encryptedFile, scratchPath)

	configYml.setValue(decrypting, "True")

	decryptedFilePath = decryptFile(configYml, scratchPath, yamlConfigPath)

	configYml.setValue(fileCopied, "True")
	configYml.dumpYAML(os.path.join(scratchPath, yamlFileName))
	configYml.dumpYAML(os.path.join(yamlConfigPath))

	print("All done!")


def main():
	global searchPath
	searchPath = glob(os.path.join(unprocessed, "unprocessed-*"))
	if len(searchPath) >= 1:
		print("Checking all config files")
	else:
		print("No input directories found, exiting")
		quit()

	for dir in searchPath:
		yamlConfigPath = os.path.join(dir, yamlFileName)

		global configYml
		configYml = ConfigYml(yamlConfigPath)
		if configYml.getValue(jobType) == "imputation":
			if configYml.getValue(fileCopied) == "False" and configYml.getValue(decrypting) == "False":
				imputation(yamlConfigPath, dir)
			elif configYml.getValue(fileCopied) == "False" and configYml.getValue(decrypting) == "True":
				print("File decryption has started, files have not been transferred, waiting")
			elif configYml.getValue(fileCopied) == "True" and configYml.getValue(decrypting) == "False":
				print("Files have been copied but not decrypted, this should not be possible...")
			elif configYml.getValue(fileCopied) == "True" and configYml.getValue(decrypting) == "True":
				#Do nothing
				#continue
				print("")

		elif configYml.getValue(jobType) == "schizophrenia":
			if configYml.getValue(fileCopied) == "False" and configYml.getValue(decrypting) == "False":
				runSchizophrenia(yamlConfigPath, dir)
			elif configYml.getValue(fileCopied) == "False" and configYml.getValue(decrypting) == "True":
				print("File decryption has started, files have not been transferred, waiting")
			elif configYml.getValue(fileCopied) == "True" and configYml.getValue(decrypting) == "False":
				print("Files have been copied but not decrypted, this should not be possible...")
			elif configYml.getValue(fileCopied) == "True" and configYml.getValue(decrypting) == "True":
				#Do nothing
				#continue
				print("")

if __name__ == "__main__":
	main()
