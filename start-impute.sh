#!/bin/bash

DOCKER_CORES=4

start-hadoop && \
cloudgene run imputationserver@1.2.7 \
--files /inputs/ \
--refpanel apps@hapmap-2@2.0.0 \
--conf /etc/hadoop/conf \
--output /outputs/ \
--population eur
