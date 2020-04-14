#!/bin/bash

#set -o xtrace
trap exit ERR

VCF=$1
TABIX=$2
BGZIP=$3

# Check that the path given contains an executable binary
# Note: This check will pass if any executable file is given as input
if [[ ! -x $TABIX ]]; then
	echo "tabix not found, tabix must be installed, check if path is correct and if the binary is executable, exiting"
	echo "path given: $TABIX"
	exit 1
fi

# Check that the path given contains an executable binary
# Note: This check will pass if any executable file is given as input
if [[ ! -x $BGZIP ]]; then
	echo "bgzip not found, bgzip must be installed, check if path is correct and if the binary is executable, exiting"
	echo "path given: $BGZIP"
	exit 1
fi

# Index the vcf file
tabix -p vcf $VCF

# Create basename from vcf file name
BASENAME=${VCF/.vcf.gz}
BASENAME=${BASENAME##*/}

# Split vcf file per chromosome
for chrom in $(tabix --list-chroms $VCF); do
	# Create output name variable
	OUTPUTNAME=$BASENAME-$chrom.vcf.gz

	# Create vcf file with single chromosome
	tabix -h $VCF $chrom | bgzip -c > output/$OUTPUTNAME

	# index the vcf file
	tabix -p vcf output/$OUTPUTNAME
done
