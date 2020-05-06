#!/bin/bash

# author: Shengwei
# purpose: run Azure Batch in CLI for brain extraction of T1 image with ANTs and adjusted template/tissue probability maps from SPM12
# prerequisites: ANTs, Azure CLI (check version by "az -v") installed on Ubuntu 16.04 LTS
# expected run time: ~ 25 mins per scan
# notes: 
# 1. ants seems multi-threaded so choose a compute optimized VM instead of memory/storage opt. one (e.g. standard_a2m_v2)
# 2. using Azure AD instead of shared key auth. (see az batch account login option) to create pool in batch
# 3. antsBETsz.sh is based on antsBrainExtraction.sh from ANTs scripts
# 4. need more investigations for pool autoscale, esp. formula and node deallocate opt.

# Some references:
# https://docs.microsoft.com/en-us/azure/batch/batch-automatic-scaling
# https://docs.microsoft.com/en-us/rest/api/batchservice/pool
# https://github.com/MicrosoftDocs/azure-docs/blob/master/articles/batch/tutorial-rendering-cli.md
# https://github.com/Azure-Samples/azure-cli-samples/blob/master/batch/render-scene/render_scene.sh
# https://github.com/khilscher/AzureBatch_CLI/blob/master/sendtoazurebatch.sh

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

imageName='vm-image'
poolId='pool'
lowPriorityNodes=0
nodeMaxTasks=1
vmSize='standard_a2m_v2'
echo "`az vm list-sizes --query "[*].name" -o tsv |grep -in $vmSize|cut -d: -f1` -1"|bc > line
line=`cat line`;rm line
vmVCPUs=`az vm list-sizes --query "[$line].numberOfCores" -o tsv`
jobId='job'
inputContainer='inputs'
templateFile='IITSkull_crop.nii.gz'
tpmFile='IIT_brain_prob.nii.gz'
script='antsBETsz.sh'
outputContainer='outputs'
totalTasks=`ls $inputContainer|grep ^1|wc -l`
dedicatedNodes=$totalTasks # inputs/ looks like this:

# inputs/
# ├── 120501_07_90439144-t1.nii.gz
# ├── 120628_00_78657384-t1.nii.gz
# ├── ...
# ├── antsBETsz.sh
# ├── $template.nii.gz
# └── $tpm.nii.gz

echo -e "Pool vm image [$imageName] and size [$vmSize] with [$vmVCPUs] vCPU(s)\n"
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
  \"enableInterNodeCommunication\": false,
  \"startTask\": {
    \"resourceFiles\": [
      {
        \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$templateFile?$sasIn\",
        \"filePath\": \"$templateFile\"
      },
      {
        \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$tpmFile?$sasIn\",
        \"filePath\": \"$tpmFile\"
      },
      {
        \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$script?$sasIn\",
        \"filePath\": \"$script\"
      }
    ],
    \"commandLine\": \"/bin/bash -c 'sleep 1'\",
    \"waitForSuccess\": true
  }
}" > pool.json

az batch pool create --json-file pool.json
if [ $? != 0 ];then 
	echo "Error creating pool, exiting..."
	exit 1
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
count=1
for subjid in `ls $inputContainer|grep ^1|cut -d- -f1`; do
	echo -e "{
  \"id\": \"task$count\",
  \"commandLine\": \"/bin/bash -c '. /usr/local/software/addpaths;ln -s /mnt/batch/tasks/startup/wd/$templateFile;ln -s /mnt/batch/tasks/startup/wd/$tpmFile;ln -s /mnt/batch/tasks/startup/wd/$script;./$script -a $subjid-t1.nii.gz -e $templateFile -m $tpmFile -o $subjid;mv ${subjid}BrainExtractionMask.nii.gz $subjid-antsMask.nii.gz;fslcpgeom $subjid-t1 $subjid-antsMask;mv *N4Corrected0* $subjid-N4.nii.gz;fslcpgeom $subjid-t1 $subjid-N4;fslmaths $subjid-antsMask -add 0 $subjid-antsMask -odt char'\",
  \"resourceFiles\": [
    {
      \"blobSource\": \"https://$storageName.blob.core.windows.net/$inputContainer/$subjid-t1.nii.gz?$sasIn\",
      \"filePath\": \"$subjid-t1.nii.gz\"
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
      \"filePattern\": \"*-antsMask.nii.gz\",
      \"destination\": {
        \"container\": {
          \"containerUrl\": \"https://$storageName.blob.core.windows.net/$outputContainer?$sasOut\"
        }
      },
      \"uploadOptions\": {
         \"uploadCondition\": \"TaskCompletion\"
      }
    },
    {
      \"filePattern\": \"*-N4.nii.gz\",
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
    ((count++))
done

# check task/job
az batch job set --job-id $jobId --on-all-tasks-complete terminatejob

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
	while [ ! "`az batch pool list|grep $poolId`" = "" ];do
		i=$(( (i+1) %4 ))
		printf "\r[`date "+%x %T"`] Deleting ${spin:$i:1}"	
	done
fi
echo -e "\nall done!"
