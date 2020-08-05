
import yaml
import os

from constants import inputFile, jobType, country, md5sum, encrMd5sum, fileCopied, decrypting, \
    encryptedInputLabel, scriptId, schizophrenia, imputation

allowedNames = [inputFile, jobType, country, md5sum, encrMd5sum, fileCopied, decrypting,
                encryptedInputLabel, scriptId]


class ConfigYml():

    def __init__(self, path):
        with open(path) as f:
            self._configYmlTop = yaml.load(f, Loader=yaml.FullLoader)
        self._configYml = self._configYmlTop[0]

    def initFromArgs(self, args):
        if args:
            self._configYml[jobType] = args.jobType
            self._configYml[country] = args.country
            if self._configYml[jobType] == schizophrenia:
                self._configYml[scriptId] = args.scriptId
                self._configYml[fileCopied] = 'False'
                self._configYml[decrypting] = 'False'
            if self._configYml[jobType] == imputation:
                self._configYml[fileCopied] = 'False'
                self._configYml[decrypting] = 'False'
                self._configYml[encryptedInputLabel] = os.path.basename(args.vcf)

    def dumpYAML(self, yamlPath):
        with open(yamlPath, "w") as f:
            yaml.dump(self._configYmlTop, f, default_flow_style=False)

    def setValue(self, name, val):
        if name in allowedNames:
            self._configYml[name] = val

    def getValue(self, name):
        if name in allowedNames and name in self._configYml:
            return self._configYml[name]
