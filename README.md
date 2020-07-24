# Bifrost
This is a service that enables job submissions on secure compute platforms from personal computers on the open internet

<h1 align="center">
  <br>
  <a href="https://github.com/neicnordic/Bifrost"><img src="https://github.com/neicnordic/Bifrost/blob/master/.bifrost-logo.png" alt="Bifrost" width="200"></a>
</h1>

The name Bifrost (pronounced Biv-rost) comes from the old Norse mythology and is the name of the bridge that connects the world of men with the world of the gods. This project is like Bifrost since it is like a bridge that enables job submission from the open internet to secure compute infrastructures in the Nordics.  

**This tool will allow a registered members of the p1054 project in TSD to submit vcf files or shizophrenia cohort data for analysis inside TSD. The tool performs the following steps:**  
1. Uploading of input data to TSD  
    - Cohort data is automatically encrypted upon submission  
    - VCF files must be manually encrypted before submission   
2. Decryption of uploaded data inside TSD  
3. Analysis of uploaded data according to job type
    - Imputation for VCF files
    - Statistical calculations for cohort data.  
* End users must check manually if a compute job has finished before they can download their output data.  
    - If your input file name is `nameOfInputFile.vcf.gz`, your output files will be located in `/tsd/p1054/data/durable/BifrostWork/bifrost-scratch/JobFinished-nameOfTheInputFile/outputs`.  
* It is up to you, the user, to encrypt the output files before you can download them from TSD, a future release will automatically encrypt the output files with your personal crypt4gh public key and the TSD crypt4gh secret key.  
* An imputation job takes about 100 hours to finish, an R cohort job takes mere minutes to complete once it has started, starting a job may take up to 30 minutes if there are no other jobs in the queue.  
    - Only one job can run at a time, if an imputation job is running it will take up to 100 hours before the next job can start.

## End user instructions  
### Dependencies
* Python 3.6+
* Python 2.7
    * Install python 2.7 dependencies with this command: `pip install --user -r requirements.txt`  

### tsd-s3cmd instructions
Bifrost uses the tsd-api-client to upload the files, follow their [installation instructions](https://github.com/unioslo/tsd-api-client#install) to install your own copy.

### Generating a personal key pair for encrypting and decrypting files
All sensitive data needs to be encrypted before it is sent to TSD, we use [crypt4gh](https://github.com/EGA-archive/crypt4gh) for that. Follow the [installation instructions](https://github.com/EGA-archive/crypt4gh#installation) to install it locally. Follow the [demonstration](https://github.com/EGA-archive/crypt4gh#demonstration) to learn how to generate your own key pair and encrypt/decrypt your sensitive files. Remember to be very careful with these keys, if you lose access to them you also lose access to the data that has been encrypted with these keys.  

### Acquiring the TSD public encryption key
Log in to the [TSD data portal](https://data.tsd.usit.no/index.html) and download the `TSD.pub` file, you need this to encrypt your vcf files that you want to analyze with the imputation server.

### Encrypt your vcf files
Follow the instructions in the [demonstration](https://github.com/EGA-archive/crypt4gh#demonstration) to encrypt your vcf files.  
**NB**: *Only vcf files for imputation need to be encrypted manually before they can be submitted, "schizophrenia" related files for the R script are encrypted automatically upon submission.*

### Cloning this repository  
To submit a job you need to first clone this repository to your local machine like so: 
`git clone https://github.com/neicnordic/Bifrost/`

### How to submit an imputation job  
Navigate to the Bifrost directory:
`cd Bifrost`

To run an imputation job we begin building the command by writing:  
`./submitJob.py --jobType imputation`

Now locate your encrypted input file, let's assume it's at:  
`/home/username/inputFiles/dataToImpute.vcf.gz.c4gh`

Now you can write:  
`./submitJob.py --jobType imputation --vcf /home/username/inputFiles/dataToImpute.vcf.gz.c4gh`

Then you select which country to run in, currently it is only possible to run in Norway, so you therefore select country as such:  
`./submitJob.py --jobType imputation --vcf /home/username/inputFiles/dataToImpute.vcf.gz.c4gh --country Norway`

Next we add the TSD public encryption key like this:  
`./submitJob.py --jobType imputation --vcf /home/username/inputFiles/dataToImpute.vcf.gz.c4gh --country Norway --remotePubKey /home/username/path/to/TSD.pub`

Then supply your personal secret encryption key, the one you generated with the `crypt4gh-keygen` tool earlier:  
`./submitJob.py --jobType imputation --vcf /home/username/inputFiles/dataToImpute.vcf.gz.c4gh --country Norway --remotePubKey /home/username/path/to/TSDPubKey.pub --personalSecKey /home/username/path/to/mySecretKey.sec`

The last step is to supply your personal public key:  
`./submitJob.py --jobType imputation --vcf /home/username/inputFiles/dataToImpute.vcf.gz.c4gh --country Norway --remotePubKey /home/username/path/to/TSDPubKey.pub --personalSecKey /home/username/path/to/mySecretKey.sec --personalPubKey /home/username/path/to/myPublicKey.pub`

Now that all this is done you can hit enter to run the command, you now need to be ready to write your TSD username, password and one time password (OTP) to actually upload the files.  

### How to submit a schizophrenia R job  
This will be described once the code for it is ready.

## Developer documentation
To set Bifrost up on TSD from scratch, follow [these instructions](docs/technicalDocumentation.md).
