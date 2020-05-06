#!/bin/bash
# count cores in use on Azure Batch pools for python script
# author: Shengwei

Usage() {
    echo ""
    echo "Usage: countCoresUsed.sh <vm_size>"
    echo "E.g. countCoresUsed.sh standard_a1"
    exit 1
}

[ "$1" = "" ] && Usage

vmSize=$1
echo "`az vm list-sizes --query "[*].name" -o tsv |grep -in $vmSize|head -1|cut -d: -f1` -1"|bc > line
line=`cat line`;rm line
vmVCPUs=`az vm list-sizes --query "[$line].numberOfCores" -o tsv`

# check if AccountCoreQuotaReached
az batch pool list --query "[*].currentDedicatedNodes" -o tsv > countDedicated
if [ -s countDedicated ];then
	for vmsize in `az batch pool list --query "[*].vmSize" -o tsv`;do
		line=`az vm list-sizes --query "[*].name" -o tsv |grep -in $vmsize|head -1|cut -d: -f1`
		((line--))
		az vm list-sizes --query "[$line].numberOfCores" -o tsv >> ncores
	done
	coresInUse=`pr -mts ncores countDedicated |sed 's/\t/*/g'|bc |paste -sd+ |bc`
	rm ncores countDedicated
else
	coresInUse=0;rm countDedicated
fi
echo "$coresInUse,$vmVCPUs,"
