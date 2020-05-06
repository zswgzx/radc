#!/bin/bash

neurodocker generate docker -b ubuntu:16.04 -p apt --matlabmcr version=2018b --copy standalone /opt/spm12_with_cat --copy cat12r1434_docker.m /opt/spm12_with_cat/ --copy run_preprocessing_docker.sh /opt/ > Dockerfile

docker build -t biokit:0.1 -f Dockerfile .

docker run --entrypoint="/bin/bash" -v /media/work/aevia/MarkVCID/cat_development/data/T1WTD/b142ec2383601225b6437d9aaa3cefa8/:/input -v /media/work/aevia/MarkVCID/cat_development/docker_out/:/output -it biokit:0.1
