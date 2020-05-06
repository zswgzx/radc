#!/bin/bash

# author: Shengwei
# purpose: run Azure Batch in CLI for FSL randomise (parallel)
# prerequisites: FSL, Azure CLI (check version by "az -v") installed on Ubuntu 16.04 LTS
# notes: 
# 1. using Azure AD instead of shared key auth. (see az batch account login option) to create pool in batch

# Some references:
# https://docs.microsoft.com/en-us/azure/batch/batch-automatic-scaling
# https://docs.microsoft.com/en-us/rest/api/batchservice/pool
# https://github.com/MicrosoftDocs/azure-docs/blob/master/articles/batch/tutorial-rendering-cli.md
# https://github.com/Azure-Samples/azure-cli-samples/blob/master/batch/render-scene/render_scene.sh
# https://github.com/khilscher/AzureBatch_CLI/blob/master/sendtoazurebatch.sh

Usage() {
    echo ""
    echo "Usage: $0 <single EV of Interest (EVoI)> <vxl EV:n> <DTI analysis? 1:y 0:n>"
    echo "E.g. $0 diabetes 6 1"
    exit 1
}

[ "$1" = "" ] && Usage
dg='^[0-9]+$'
if ! [[ $2 =~ $dg ]];then Usage;fi
if ! [[ $3 =~ $dg ]];then Usage;fi

# user defined actions
trap ctrlC SIGINT

ctrlC()
{
        echo -en "\n*** User pressed CTRL + C ***\n"

        az storage container list --query "[*].name" -o tsv > containers
        if [ -s containers ];then
                if [ ! -z "`grep $inputContainer containers`" ] && [ ! -z "`grep $outputContainer containers`" ] ;then
                        read -rp "Delete containers [$inputContainer] & [$outputContainer] ? [y/N] " response
                        if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
                                blobDelete=`az storage blob delete-batch -s $inputContainer` # --pattern *gz
                                containerDel=`az storage container delete -n $inputContainer`
                                blobDelete=`az storage blob delete-batch -s $outputContainer` # --pattern *gz
                                containerDel=`az storage container delete -n $outputContainer`
                        fi
                fi
        fi
        rm containers

        az batch job list --query "[*].id" -o tsv | grep $jobId > batchjob
        if [ -s batchjob ];then
                read -rp "Delete job [$jobId] ? [y/N] " response
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
                        rm task*.json
                        az batch job delete --job-id $jobId -y
                fi
        fi
        rm batchjob

        az batch pool list --query "[*].id" -o tsv | grep $poolId > batchpool
        if [ -s batchpool ];then
                read -rp "Delete pool [$poolId] ? [y/N] " response
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
                        rm pool.json stdout scaleFormula
                        az batch pool delete --pool-id $poolId -y
                        while [ ! "`az batch pool list|grep $poolId`" = "" ];do
                                i=$(( (i+1) %4 ))
                                printf "\r[`date "+%x %T"`] Deleting ${spin:$i:1}"
                        done
                fi
        fi
        rm batchpool
	exit 0
}

resourceGroup='rg'
location='eastus'

if [ ! -f ~/.azure/config ];then
    echo "Can't find Azure config. file...";exit 1
fi

user=`az account show --query "user.name" -o tsv`
[[ ! -z "$user" ]] && echo -e "Login as [$user]\n" || az login

# add defaults as needed to avoid using -g/l option
if [ -z "`grep group ~/.azure/config`" ] || [ -z "`grep location ~/.azure/config`" ] ;then
    az configure -d group=$resourceGroup location=$location
    echo "Configured default azure resource group and location"
fi

# edit default storage account info as needed in ~/.azure/config to avoid using --account-name(key) options
storageName='storage'
storageKey=`az storage account keys list -n $storageName --query [0].value -o tsv`

if [ -z "`grep storage ~/.azure/config`" ];then 
    cat << storageInfo >> ~/.azure/config
[storage]
account = $storageName
key = $storageKey

storageInfo
    echo "Added default storage account info"
fi

# batch account login as needed
batchName='batch'
[[ -z "`grep batch ~/.azure/config`" ]] && az batch account login -n $batchName || echo -e "Using batch account [$batchName]\n"

# global parameters
imageName='vm-image'
poolId='pool'
lowPriorityNodes=0
nodeMaxTasks=2
vmSize='standard_d2_v3'
echo "`az vm list-sizes --query "[*].name" -o tsv |grep -in $vmSize|cut -d: -f1` -1"|bc > line
line=`cat line`;rm line
vmVCPUs=`az vm list-sizes --query "[$line].numberOfCores" -o tsv`
jobId='randomiseSz'
inputContainer='inputs-rdm-sz'
fourDImg='all_FA_skeletonised.nii.gz'
maskImg='mean_FA_skeleton_mask.nii.gz'
vxImg='wmh_skeletonised.nii.gz'
design='design.mat'
contrasts='contrasts.con'
outputContainer='outputs-rdm-sz'

# TODO: need to specify the following
totalTasks=100
totalIter=5000
outPrefix=$1
vxl=$2
if [ $3 = 1 ] ;then dti='-T2';else dti='T';fi

dedicatedNodes=$totalTasks

# inputs-fsl-sz/
# ├── $fourDImg
# ├── $maskImg
# ├── $vxImg
# ├── $design
# └── $contrasts

echo -e "Pool: vm image [$imageName]; vm size [$vmSize]: each has [$vmVCPUs] vCPU(s)\n"
echo -e "Total tasks [$totalTasks]; max. task/node [$nodeMaxTasks]; low priority node(s) [$lowPriorityNodes]\n"

# check if AccountCoreQuotaReached
ACCNT_CORE_QUOTA=100;HALFQUOTA=`echo "$ACCNT_CORE_QUOTA/2"|bc`;
az batch pool list --query "[*].currentDedicatedNodes" -o tsv > countDedicated
if [ -s countDedicated ];then
	for vmsize in `az batch pool list --query "[*].vmSize" -o tsv`;do
		line=`az vm list-sizes --query "[*].name" -o tsv |grep -in $vmsize|cut -d: -f1`
		((line--))
		az vm list-sizes --query "[$line].numberOfCores" -o tsv >> ncores
	done
	coresInUse=`pr -mts ncores countDedicated |sed 's/\t/*/g'|bc |paste -sd+ |bc`
	rm ncores countDedicated
else
	coresInUse=0;rm countDedicated
fi

if [ `echo "$dedicatedNodes * $vmVCPUs + $coresInUse" | bc ` -gt $ACCNT_CORE_QUOTA ] ;then
	if [ `echo "($ACCNT_CORE_QUOTA - $coresInUse)/$vmVCPUs" | bc` -ge $HALFQUOTA ];then 
		dedicatedNodes=`echo "$HALFQUOTA/$vmVCPUs" | bc`
	else
		dedicatedNodes=`echo "($ACCNT_CORE_QUOTA - $coresInUse)/$vmVCPUs" | bc`
	fi	

	if [ $dedicatedNodes -gt 0 ] ;then
		echo -e "AccountCoreQuotaReached! Dedicated nodes set to [$dedicatedNodes]\n"
	else 
		echo "No more core to use, exiting"
		exit 1
	fi
else
	echo -e "Dedicated nodes set to [$dedicatedNodes]\n"
fi 

# create containers
containerState=`az storage container create -n $inputContainer`
containerState=`az storage container create -n $outputContainer`
expiry=`date -d "18 hours" '+%Y-%m-%dT%H:%MZ'`
sasIn=`az storage container generate-sas -n $inputContainer --permission r --https-only --expiry $expiry -o tsv`
sasOut=`az storage container generate-sas -n $outputContainer --permission w --https-only --expiry $expiry -o tsv`

echo "[`date "+%x %T"`] Containers [$inputContainer] [$outputContainer] created"
# echo -ne "Container [$inputContainer] sas token is:\n$sasIn\n\n"
# echo -ne "Container [$outputContainer] sas token is:\n$sasOut\n\n"

# upload files
echo -n "Uploading files ..."
uploadState=`az storage blob upload-batch -d $inputContainer -s $PWD/$inputContainer --no-progress &> stdout`
printf "\r[`date "+%x %T"`] Files from local folder $PWD/$inputContainer all uploaded to [$inputContainer]\n"

# create pool and check status
# make pool json file
echo -e "{
  \"id\": \"$poolId\",
  \"vmSize\": \"$vmSize\",
  \"virtualMachineConfiguration\": {
    \"imageReference\": {
      \"virtualMachineImageId\": \"/subscriptions/xxx/resourceGroups/$resourceGroup/providers/Microsoft.Compute/images/$imageName\"
    },
    \"nodeAgentSKUId\": \"batch.node.ubuntu 16.04\"
  },
  \"resizeTimeout\": \"PT9M\",
  \"targetDedicatedNodes\": $dedicatedNodes,
  \"targetLowPriorityNodes\": $lowPriorityNodes,
  \"maxTasksPerNode\": $nodeMaxTasks,
  \"taskSchedulingPolicy\": {
    \"nodeFillType\": \"spread\"
  },
  \"enableAutoScale\": false,
  \"enableInterNodeCommunication\": false
}" > pool.json

az batch pool create --json-file pool.json
if [ $? != 0 ];then 
	echo "Error creating pool, exiting...";	exit 1
fi

i=0
spin='-\|/'
while [ `az batch pool show --pool-id $poolId --query "allocationState" -o tsv` = "resizing" ];do
	i=$(( (i+1) %4 ))
	printf "\r[`date "+%x %T"`] Creating pool [$poolId] ${spin:$i:1}"
done
echo " steady"

# check node(s) status
while [ `az batch node list --pool-id $poolId --query "[*].state" -o tsv |grep idle|wc -l` != $dedicatedNodes ];do
	nodesIdle=`az batch node list --pool-id $poolId --query "[*].state" -o tsv |grep idle|wc -l`
	nodesStart=`az batch node list --pool-id $poolId --query "[*].state" -o tsv |grep start|wc -l`
	printf "\r[`date "+%x %T"`] nodes (total/starting/idle) $dedicatedNodes/%02d/%02d" $nodesStart $nodesIdle
done
echo " all ready"

# enable pool autoscale
echo -e "\$NodeDeallocationOption=taskcompletion;\$tasks=(\$ActiveTasks.GetSamplePercent(150*TimeInterval_Second)<70) ? max(0,\$ActiveTasks.GetSample(1)) : max(\$ActiveTasks.GetSample(1),avg(\$ActiveTasks.GetSample(TimeInterval_Second*150)));\$targetVMs = \$tasks>0 ? \$tasks : max(\$RunningTasks.GetSample(TimeInterval_Second*150))/$nodeMaxTasks;\$TargetDedicated = min($dedicatedNodes, \$targetVMs)" > scaleFormula
az batch pool autoscale enable --pool-id $poolId --auto-scale-evaluation-interval "PT5M" --auto-scale-formula "`cat scaleFormula`"
# echo -e "\nPool autoscale enabled with formula: `cat scaleFormula`"

# create job 
az batch job create --id $jobId --pool-id $poolId
echo -e "\nJob [$jobId] created and being monitored ...\n"

# create tasks
for (( count=1; count<= $totalTasks; count++ )) ; do
	echo -e "{
  \"id\": \"task$count\",
  \"commandLine\": \"/bin/bash -c '. /usr/local/software/addpaths;randomise -i $fourDImg -o ${outPrefix}_SEED$count -D -m $maskImg -d $design -t $contrasts -$dti --uncorrp -n `echo "$totalIter/$totalTasks"|bc` --vxl=$vxl --vxf=$vxImg --seed=$count'\",
  \"resourceFiles\": [
    {
      \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$fourDImg?$sasIn\",
      \"filePath\": \"$fourDImg\"
    },
    {
      \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$maskImg?$sasIn\",
      \"filePath\": \"$maskImg\"
    },
    {
      \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$vxImg?$sasIn\",
      \"filePath\": \"$vxImg\"
    },
    {
      \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$design?$sasIn\",
      \"filePath\": \"$design\"
    },
    {
      \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$contrasts?$sasIn\",
      \"filePath\": \"$contrasts\"
    }
  ],
  \"userIdentity\": {
    \"autoUser\": {
      \"scope\": \"pool\",
      \"elevationLevel\": \"admin\"
    }
  },
  \"outputFiles\": [
    {
      \"filePattern\": \"$outPrefix*.nii.gz\",
      \"destination\": {
        \"container\": {
          \"containerUrl\": \"https://$storageName.blob.core.windows.net/$outputContainer?$sasOut\"
        }
      },
      \"uploadOptions\": {
         \"uploadCondition\": \"TaskCompletion\"
      }
    }
  ]
}" > task$count.json

    task=`az batch task create --job-id $jobId --json-file task$count.json`
done

# check task/job
az batch job set --job-id $jobId --on-all-tasks-complete terminatejob

if [ `az batch task list --job-id $jobId --query "[*].state" -o tsv|wc -l` = 0 ];then exit 1;echo "No task submitted...";fi

while [ `az batch task list --job-id $jobId --query "[*].state" -o tsv|grep complete|wc -l` != $totalTasks ];do
	taskComplete=`az batch task list --job-id $jobId --query "[*].state" -o tsv|grep complete|wc -l`
	taskRunning=`az batch task list --job-id $jobId --query "[*].state" -o tsv|grep run|wc -l`
	taskPending=`az batch task list --job-id $jobId --query "[*].state" -o tsv|grep active|wc -l`
	printf "\r[`date "+%x %T"`] tasks running/completed/active : %02d/%03d/%03d" $taskRunning $taskComplete $taskPending
done
echo " all done"

# download files to local
echo -n "Downloading outputs from container [$outputContainer] ..."
# az batch task file download --job-id antsReg --task-id task --destination ./121016_07_39721045-warped.nii.gz --file-path wd/121016_07_39721045-warped.nii.gz
mkdir -p $outputContainer
az storage blob download-batch -d ./$outputContainer -s $outputContainer --no-progress &> stdout
printf "\r[`date "+%x %T"`] Files from [$outputContainer] all downloaded locally.\n"
echo

# delete input container
read -rp "Delete container [$inputContainer] ? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
	blobDelete=`az storage blob delete-batch -s $inputContainer` # --pattern *gz
	containerDel=`az storage container delete -n $inputContainer`
fi
echo

# delete output container
read -rp "Delete container [$outputContainer] ? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
	blobDelete=`az storage blob delete-batch -s $outputContainer` # --pattern
	containerDel=`az storage container delete -n $outputContainer`
fi
echo

# delete job
read -rp "Delete job [$jobId] ? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
	rm task*.json
	az batch job delete --job-id $jobId -y
fi
echo

# delete pool
read -rp "Delete pool [$poolId] ? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]];then
	rm pool.json stdout scaleFormula
	az batch pool delete --pool-id $poolId -y
	#while [ ! "`az batch pool list|grep $poolId`" = "" ];do
	#	i=$(( (i+1) %4 ))
	#	printf "\r[`date "+%x %T"`] Deleting ${spin:$i:1}"	
	#done
fi
echo -e "\nAzure processes done! Defragmenting ..."

cd $outputContainer
# as in defragment script from randomise_parallel
echo "Merging stat images"
for FIRSTSEED in `imglob -extension ${outPrefix}_SEED1_*_p_* ${outPrefix}_SEED1_*_corrp_*` ; do 
  ADDCOMMAND=""
  ACTIVESEED=1
  if [ -e $FIRSTSEED ] ; then
    while [ $ACTIVESEED -le 2 ] ; do
      ADDCOMMAND=`echo $ADDCOMMAND -add ${FIRSTSEED/_SEED1_/_SEED${ACTIVESEED}_}`
      let "ACTIVESEED=ACTIVESEED+1"
    done
    ADDCOMMAND=${ADDCOMMAND#-add}
    #echo $ADDCOMMAND
    fslmaths $ADDCOMMAND -mul `echo "$totalIter/$totalTasks"|bc` -div `echo "$totalIter+1-$totalTasks"|bc` ${FIRSTSEED/_SEED1/}
  fi
done

echo "Renaming raw stats"
for TYPE in _ _tfce_ ; do
  for FIRSTSEED in `imglob -extension ${outPrefix}_SEED1${TYPE}tstat*` ; do 
    if [ -e $FIRSTSEED ] ; then cp $FIRSTSEED ${FIRSTSEED/_SEED1/}; fi
  done
done

rm *SEED*
cd ..
echo "all done!"

