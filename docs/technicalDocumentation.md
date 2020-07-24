# Installing and setting up Bifrost from scratch on TSD
These instructions assume that you are familiar with TSD and know your way around the command line. The instructions describe how to set up Bifrost from scratch.  
Bifrost relies on two tools for the data analysis, the [Michigan imputation server](https://github.com/genepi/imputationserver) and the [Tryggve psych](https://github.com/neicnordic/Tryggve_psych/) R markdown script, this guide covers the installation and configuration of them as well.

## Dependencies
### Inside TSD
* Python 2.7
	* pyyaml
* Python 3.6+
* Singularity 3.3.0+
* Docker
* System installation of crypt4gh
* TSD needs to enable running docker with cron

## Compute resource requirements
* 16 CPU cores
* 64 GB RAM
* 100GB disk storage per sample

## Installing the R markdown script
This will be described once the Bifrost code for the R script has been completed.

## Installing the imputation server
Begin by downloading version 1.2.7 the [Michigan imputation server](https://github.com/genepi/imputationserver).  
`wget https://github.com/genepi/imputationserver/releases/download/v1.2.7/imputationserver.zip`  

Unzip it:
`unzip imputationserver.zip`

Change directories to it:
`cd imputationserver`

Then run the imputation server once to install the imputation server application, and a reference panel that is useful for testing purposes, with this command:
`docker run -d -p 8080:80 -v $(pwd):/data/ genepi/imputationserver:v1.2.7`

Starting the web server takes about a minute, when it's up and running you reach it by going to "localhost:8080", the default admin username is admin and the password is admin1978. Start a test job with one of the test files that comes with the imputation server to verify that the imputation application and hapmap reference panels have been installed properly. Once everything works as it should you can shut down the imputation server container.

Save the imputation docker image as a tar file with this command:  
`docker save -o imputationserver.v1.2.7.tar genepi/imputationserver:v1.2.7`  

Now that you know that the imputation server runs as it should and you have saved the imputation server docker image as a tar file, you can run `cd ..` and then upload the imputation server directory with the tsd s3 tool: `tsd-s3cmd sync imputationserver s3://imputationserver`

Log into TSD and change directories to `/tsd/p1054/data/durable/BifrostWork`

Use rsync to make a copy of the imputation server:  
`rsync --progress -ah /tsd/p1054/data/durable/s3-api/imputationserver .`  
**NB:** Remember to not add a trailing `/` in the rsync command or you will copy the **contents** of the directory rather than the directory itself.

Then cd into the directory:  
`cd imputationserver`

Now load the docker container with the following command:  
`sudo -u tsdfx-p1054 docker load -i imputationserver.v1.2.7.tar`  
**NB:** You need special permission to load docker images, contact TSD support to sort this out.

The final step before you can test the imputation server is to run `chmod -R 777 database apps hadoop`, otherwise it won't run as it should.

Now you can start the imputation server like so:  
`sudo -u tsdfx-p1054 docker run --rm -d -v $(pwd):/data -p 8080:80 genepi/imputationserver:v1.2.7`

Starting the web server takes about a minute, when it's up and running you reach it by going to "hostIp:8080", the default admin username is admin and the password is admin1978.

### Installing the HRC 1.1 reference panel
Now you navigate to the admin "settings" panel and go to "applications". You will come back to this page once you have performed the following steps:  

* Change directories: `cd /tsd/p1054/data/durable/oskar/HRC1.1-processed`
* Start a python web server in this directory: `python3 -m http.server`
* Go to "hostIp:8000" with a web browser and verify that you can see the `hrc1.1.zip` file.
* Go back to the imputation server admin settings panel  
**NB**: The imputation server does not support installing reference panels from local directories which is why we must run a web server to host the zip file for us.  

Now that we have started a web server that hosts our reference panel, we can finally install it.  

Follow the [official installation instructions](https://github.com/genepi/imputationserver-docker#install-a-new-reference-panel) to install the reference panel.

**NB:** Installing the reference panel takes a very long time since it needs to be "downloaded", unzipped and then installed.

## Preparatory steps before uploading Bifrost to TSD
Run `git clone https://github.com/neicnordic/Bifrost`

Then make a zip file:  
`zip -r Bifrost.zip Bifrost`

Now you can upload the zip file with the [TSD data portal](https://data.tsd.usit.no/index.html).

## Setting up Bifrost inside TSD
Let's assume you want to install Bifrost in `/tsd/p1054/data/durable/BifrostWork`, start by running:  
`cp /tsd/p1054/data/durable/file-import/p1054-member-group/Bifrost.zip /tsd/p1054/data/durable/BifrostWork`  
`cd /tsd/p1054/data/durable/BifrostWork`  
`unzip Bifrost.zip`  
`cd Bifrost`  
Now we have extracted a fresh copy of Bifrost and cd'd to it. Let's configure Bifrost!

### Editing the constants.py file  
The `constants.py` file contains the default values for variables that are used in the python scripts for job submission, file decryption and job start inside TSD.  

All paths in the constants must be absolute.  
* `basepath`: Path to the directory that holds Bifrost, i.e `/tsd/p1054/data/durable/BifrostWork/`  
* `tsdPrivateKeyPath`: Path to the TSD crypt4gh private key, currently it is `/tsd/p1054/data/durable/BifrostWork/crypt4ghKeys`  
* `scratch`: The scratch directory, should be placed in the "basepath" directory, i.e `/tsd/p1054/data/durable/BifrostWork/bifrost-scratch`  
* `unprocessed`: The directory where the input directories are copied to from the s3-api import directory, i.e `/net/tsd-evs.tsd.usit.no/p1054/data/durable/BifrostWork/bifrost-cloned-inputs`  
* `imputationserver`: The install directory of the imputation server, i.e `/tsd/p1054/data/durable/imputationserver`  
* `bifrost`: The directory path to Bifrost, in this example it is `/tsd/p1054/data/durable/BifrostWork/Bifrost`  
* `finishedJobs`: This constant is not used at the moment and only serves as a placeholder for a future release.  

### Editing the updater.sh script
Since it is not possible to edit, or delete, files that are in the `s3-api` directory, they need to be cloned to a new directory before files can be decrypted etc. This is done automatically by the `scripts/updater.sh` script.  
Simply change the `SOURCE` variable to where the files are uploaded with the submit script, this is probably `tsd/p1054/data/durable/s3-api/bifrost-inputs/`, remember to include the trailing `/`. If this directory/bucket does not exist in your project you can create it with `tsd-s3cmd mb s3://bifrost-inputs`.  
Then change the `DESTINATION` variable to the same path as the `unprocessed` constant in the `contants.py` file, i.e `/net/tsd-evs.tsd.usit.no/p1054/data/durable/BifrostWork/bifrost-cloned-inputs`

### Configuring crontab
Open the file named `crontabSettings` in the `Bifrost/settings` directory, edit the `BIFROST` variable file path to where `Bifrost` has been installed, in our current example it is `/tsd/p1054/data/durable/BifrostWork/Bifrost`. The default setting is to run the cron job once per minute, change this to once every 10 minute for production use. Then uncomment the lines for the `updates.sh`, `readConfig.py` and `runJob.py` scripts when you are ready to go live and enable Bifrost. 

That's it, Bifrost should be up and running now. Submit a test job just to verify that it runs as it should.