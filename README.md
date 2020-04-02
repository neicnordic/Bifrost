# Bifrost
This is a service that enables job submissions on secure compute platforms from the outside

<h1 align="center">
  <br>
  <a href="https://github.com/neicnordic/Bifrost"><img src="https://github.com/neicnordic/Bifrost/blob/master/.bifrost-logo.png" alt="Bifrost" width="200"></a>
</h1>

The name Bifrost (pronounced Biv-rost) comes from the old Norse mythology and is the name of the bridge that connects the world of man with the world of the gods. In the same manner this project is like a bridge that enables job start from the outside of secure compute infrastructures in the Nordics, on the inside of these secure compute infrastructures.  

## Usage instructions  
### Creating public and private encryption keys
Because we are working with sensitive data we need to generate a pair of encryption keys that we use to encrypt the data before we transfer it to the sensitive data compute platform, and decrypt the data when it has been transfered to the sensitive data compute platform and is ready to be analyzed. Remember to be very careful with these keys because if you lose access to them you also lose access to the data that has been encrypted with these keys.  
The official instructions are found [here](https://github.com/EGA-archive/crypt4gh#demonstration), in short you run this:  
```bash
crypt4gh-keygen --sk MySecretKey.sec --pk MyPublicKey.pub
```

### Cloning this repository  
To submit a job you need to first clone this repository to your local machine like so: 
```bash
git clone https://github.com/neicnordic/Bifrost/
```

### How to submit an imputation job  
Navigate to the Bifrost directory, for example:
```bash
cd /home/username/Bifrost
```
Because we are going to run an imputation job we can begin by writing:
```bash
./submitJob.py --jobtype imputation
```
Now locate your input file, let's assume it's at:
```bash
/home/username/inputFiles/dataToImpute.vcf
```
now you can write:
```bash
./submitJob.py --jobtype imputation --vcf /home/username/inputFiles/dataToImpute.vcf
```
Then you select which country to run in, currently it is only possible to run in Norway, so you therefore select country as such:
```bash
./submitJob.py --jobtype imputation --vcf /home/username/inputFiles/dataToImpute.vcf --country Norway
```
Next we add the TSD public encryption key like this:
```bash
./submitJob.py --jobtype imputation --vcf /home/username/inputFiles/dataToImpute.vcf --country Norway --pubkey /home/username/path/to/TSDPubKey.pub
```
The last step is to supply your personal secret encryption key, the one you generated with:
`crypt4gh-keygen` tool earlier, like this:
```bash
./submitJob.py --jobtype imputation --vcf /home/username/inputFiles/dataToImpute.vcf --country Norway --pubkey /home/username/path/to/TSDPubKey.pub --seckey /home/username/path/to/MySecretKey.sec
```
## Note: You cannot actually submit a job to TSD now, the following text is only a placeholder  
Now that all this is done you can hit enter to run the command. It will start by encrypting your file, which will take a while if your input file is large, and when the encryption is finished you need to be ready to write your username, password and one time password (OTP) to actually send the files.  

### Setting up the readConfig.py script on TSD
You need to edit the `basepath` variable and set it to where your files are transfered to when you transfer them to TSD. Remember to include the trailing "/".
