
import yaml

from Constants import INPUT_FILE, JOBTYPE, COUNTRY, MD5_SUM, ENCR_MD5_SUM, FILE_COPIED, DECRYPTING, \
    ENCRYPTED_INPUT, SCRIPT_ID, SCHIZOPHRENIA

ALOWED_NAMES = [INPUT_FILE, JOBTYPE, COUNTRY, MD5_SUM, ENCR_MD5_SUM, FILE_COPIED, DECRYPTING,
                ENCRYPTED_INPUT, SCRIPT_ID]


class ConfigYml():

    def __init__(self, path):
        with open(path) as f:
            self._configYmlTop = yaml.load(f, Loader=yaml.FullLoader)
        self._configYml = self._configYmlTop[0]

    def initFromArgs(self, args):
        if args:
            self._configYml[JOBTYPE] = args.jobtype
            self._configYml[COUNTRY] = args.country
            if self._configYml[JOBTYPE] == SCHIZOPHRENIA:
                self._configYml[SCRIPT_ID] = args.scriptid
                self._configYml[FILE_COPIED] = 'False'
                self._configYml[DECRYPTING] = 'False'

    def dumpYAML(self, yamlPath):
        with open(yamlPath, "w") as f:
            yaml.dump(self._configYmlTop, f, default_flow_style=False)

    def setValue(self, name, val):
        if name in ALOWED_NAMES:
            self._configYml[name] = val

    def getValue(self, name):
        if name in ALOWED_NAMES and name in self._configYml:
            return self._configYml[name]
