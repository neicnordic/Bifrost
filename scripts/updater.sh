#!/bin/bash

rsync --progress -ahu /tsd/p1054/data/durable/s3-api/bifrost-inputs/unprocessed-* \
/net/tsd-evs.tsd.usit.no/p1054/data/durable/BifrostWork/cloned-bifrost-inputs/
