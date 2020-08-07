#!/bin/bash

#--refpanel apps@haplotype-reference-consortium-1.1@1.1 \


DOCKER_CORES=4

cd /data

start-hadoop && \
cloudgene run imputationserver@1.4.1 \
--refpanel apps@hapmap-2@2.0.0 \
--files /inputs/ \
--conf /etc/hadoop/conf \
--output /outputs/ \
--population eur \
--aesEncryption no
