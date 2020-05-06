# Introduction 
[Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) is a tool that can create virtualized environments to process data, and is important for standardization and reproducibility.  
More information about docker can be found [here](https://dev.to/pavanbelagatti/docker-best-practices-for-developers-what-next-1fjk),  
This repository is designed to aid creating docker images for neuroimaging. A docker image is build from a dockerfile, which is generated based on an open-source program [Neurodocker](https://github.com/kaczmarj/neurodocker).
This repository is also intended to serve as a hub for customized dockerfiles. Such dockerfiles are necessary to install software not currently supported on Neurodocker, such as [TORTOISE](https://tortoise.nibib.nih.gov/), [DRAMMS](https://github.com/ouyangming/DRAMMS), etc.


# Creating a Docker Image with Neurodocker
1. **Identify imaging software that is needed in the docker image**

2. **Set current working directory to the context directory on local computer**
    - Context directory contains code/files that will be copied into docker image (e.g. templates, user scripts, etc.). 
    - Only files in the context directory and its subdirectories can be copied.  
 
3. **Run neurodocker with the command line options necessary to install imaging software** 
    - Save neurodocker output to a file that has identifying information in filename. For example:  
        `neurodocker generate docker [Command line options] > $Dockerfile`
    - To take advantage of docker's caching feature, software that takes longer time to install should be in the earlierpart of the command line options.

4. **Build the docker image and set the tag to <Dockerhub basename>/<image_name>:<version>**
    - Example: `docker build -f $Dockerfile -t zswgzx/dti:2019.12.11 [--force-rm --compress].`

5. **Run docker image with the test data mounted and an overridden entry point**
    - Entrypoint is a command defined while building the docker image, and is immediately executed when running a docker image.  
        `docker run -it --rm -v <path to test data on computer>:<path to test data in docker image (folder does not have to exist)>:<read/write permission> --entrypoint /bin/bash <username>/<image_name>:<version>`

6. **Within docker image, run the desired command on the mounted test data**

7. **Evaluate errors, modify docker image as needed, and rebuild docker image**
    - Rebuilding a docker image will make a new entry in docker image list. 
    - At some point (usually at the end), you should remove unused docker images (see below). 

---

# Useful Commands:
1. `docker image ls` or `docker images`
    - List all docker images		  
2. `docker image rm <image id>` or `docker rmi <image id>`
    - Remove specific docker image
3. `docker image prune`
    - Remove dangling/unused images
4. `docker rm $(docker ps -aq)`
    - Remove all stopped containers
5. `docker login/logout <container repo>`
    - Login/out specific contaner repository
6. `docker push <image tag: e.g. $username/${image_name}:$version>`
    - upload specified docker image

---

#Reducing Docker Image Size
Docker images can become large when installing certain software.
Smaller Docker images allow for a faster startup of compute nodes on Azure batch.

##Trimming the [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSL) folder
A full installation of FSL can add about ~15 GB to the Docker image size, which translates to an additional 40 minutes of start up time on Azure batch. 
Removing specific folders and binaries can lower this number substantially.
However, it is advised to test the FSL programs that you need after modifying the FSL folder.

To trim the FSL folder, edit the Dockerfile as follows:
1. Remove the lines pertaining to the installation of the FSL conda environment. Specifically, these two lines:
   - `&& echo "Installing FSL conda environment ..." \`
   - `&& bash /opt/fsl-$version/etc/fslconf/fslpython_install.sh -f /opt/fsl-$version`
2. Delete $FSLDIR/bin/FSLeyes/
   - Add this line: `&& rm -rf $FSLDIR/bin/FSLeyes` 
3. Delete binaries that will not be used in $FSLDIR/bin
4. Delete lib, data, and src folder from $FSLDIR.
   - Some binaries require files in the lib folder. 
   Running the binary will notify you which file from the lib file is required.
   Determining the required lib files will be based on trial and error.

---

#Future Steps
Add instructions or dockerfile lines for the installation of third party software not included in Neurodocker (TORTOISE, DRAMMS, etc.).
Maybe add list of required lib files for each FSL binary?
