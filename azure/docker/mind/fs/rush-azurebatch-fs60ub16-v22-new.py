# Script to process FreeSurfer v6.0.0 in Azure BATCH
# RUSH script by Cyrus Eierud, Alec Burgess and Ashish Tamhane
# In this version the subject IDs may have project IDs with flexible lengths
from __future__ import print_function
import datetime
import os
import time
import sys
import string
import random
import glob
import subprocess
from math import ceil
try:
    input = raw_input
except NameError:
    pass
import azure.storage.blob as azureblob
import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
from azure.common.credentials import ServicePrincipalCredentials

sys.path.append('.')
sys.path.append('..')

# global variables
_CLOUD_BASH = 'rush-fs60ub16c.sh'
_POOL_ID = 'YB-FS60'
_CLOUD_CONTAIN_TIME_HOURS = 240
_POOL_DELETE = True
_POOL_VM_SIZE = 'standard_d11_v2'
_CLOUD_CONTAIN_DELETE = True
_CLOUD_CONTAIN_IN = 'in-yb'
_CLOUD_CONTAIN_OUT = 'out-yb'
_JOB_ID = 'fs60tp1'
_JOB_DELETE = True
_BATCH_ACCOUNT_NAME = 'batch'
_BATCH_ACCOUNT_KEY = 'key1'
_BATCH_ACCOUNT_URL = 'https://xxx.eastus.batch.azure.com'
_BATCH_CORE_QUOTA = 500
_STORAGE_ACCOUNT_NAME = 'storage'
_STORAGE_ACCOUNT_KEY = 'key2'
_TENANT_ID = 'tID'
_APPLICATION_ID = 'appID'
_APPLICATION_SECRET = 'key3'
_VM_IMG = '/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/' \
          'images/vm-image'
_MAX_TASK_PER_NODE = 2
_AUTO_SCALE_EVAL_INT = datetime.timedelta(minutes=5)
_SCALE_INT = 'Minute*5'


def print_batch_exception(batch_exception):
    """
    Prints the contents of the specified Batch exception.

    :param batch_exception:
    """
    print('-------------------------------------------')
    print('Exception encountered:')
    if batch_exception.error and \
            batch_exception.error.message and \
            batch_exception.error.message.value:
        print(batch_exception.error.message.value)
        if batch_exception.error.values:
            print()
            for mesg in batch_exception.error.values:
                print('{}:\t{}'.format(mesg.key, mesg.value))
    print('-------------------------------------------')


def upload_file_to_container(block_blob_client, container_name, file_path):
    """
    Uploads a local file to an Azure Blob storage container.

    :param block_blob_client: A blob service client.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str container_name: The name of the Azure Blob storage container.
    :param str file_path: The local path to the file.
    :rtype: `azure.batch.models.ResourceFile`
    :return: A ResourceFile initialized with a SAS URL appropriate for Batch
    tasks.
    """
    blob_name = os.path.basename(file_path)

    print('Uploading file {} to container [{}]...'.format(file_path,
                                                          container_name))

    block_blob_client.create_blob_from_path(container_name,
                                            blob_name,
                                            file_path)

    # Obtain the SAS token for the container.
    sas_token = get_container_sas_token(block_blob_client,
                                        container_name, azureblob.BlobPermissions.READ)

    sas_url = block_blob_client.make_blob_url(container_name,
                                              blob_name,
                                              sas_token=sas_token)

    return batchmodels.ResourceFile(file_path=blob_name,
                                    http_url=sas_url)


def get_container_sas_token(block_blob_client,
                            container_name, blob_permissions):
    """
    Obtains a shared access signature granting the specified permissions to the
    container.

    :param block_blob_client: A blob service client.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str container_name: The name of the Azure Blob storage container.
    :param BlobPermissions blob_permissions:
    :rtype: str
    :return: A SAS token granting the specified permissions to the container.
    """
    # Obtain the SAS token for the container, setting the expiry time and
    # permissions. In this case, no start time is specified, so the shared
    # access signature becomes valid immediately. Expiration is in 15 hours.
    container_sas_token = \
        block_blob_client.generate_container_shared_access_signature(
            container_name,
            permission=blob_permissions,
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=_CLOUD_CONTAIN_TIME_HOURS))

    return container_sas_token


def get_container_sas_url(block_blob_client,
                          container_name, blob_permissions):
    """
    Obtains a shared access signature URL that provides write access to the
    ouput container to which the tasks will upload their output.

    :param block_blob_client: A blob service client.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str container_name: The name of the Azure Blob storage container.
    :param BlobPermissions blob_permissions:
    :rtype: str
    :return: A SAS URL granting the specified permissions to the container.
    """
    # Obtain the SAS token for the container.
    sas_token = get_container_sas_token(block_blob_client,
                                        container_name, azureblob.BlobPermissions.WRITE)

    # Construct SAS URL for the container
    container_sas_url = "https://{}.blob.core.windows.net/{}?{}".format(_STORAGE_ACCOUNT_NAME, container_name,
                                                                        sas_token)

    return container_sas_url


def create_job(batch_service_client, job_id, pool_id):
    """
    Creates a job with the specified ID, associated with the specified pool.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID for the job.
    :param str pool_id: The ID for the pool.
    """
    print('Creating job [{}]...'.format(job_id))

    job = batch.models.JobAddParameter(
        id=job_id,
        pool_info=batch.models.PoolInformation(pool_id=pool_id))

    batch_service_client.job.add(job)


def create_pool(batch_service_client, pool_id, scale_interval, auto_scale_eval_interval, dedicated_node_count):
    """Creates a pool of compute nodes with the specified OS settings.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str pool_id: An ID for the new pool.
    :param str scale_interval: as in auto scale formula.
    :param timedelta auto_scale_eval_interval: time that specify the auto scale evaluation interval
    :param int dedicated_node_count: number of dedicated nodes in pool."""
    # TODO: monitor nodes

    # check core quota
    cores_limit = _BATCH_CORE_QUOTA
    cores = subprocess.run(['./countCoresUsed.sh ' + _POOL_VM_SIZE], shell=True, capture_output=True).stdout
    cores = cores.decode().split(',')

    if _MAX_TASK_PER_NODE > int(cores[1]):
        print('Max. task/node is more that cores/node! Exiting...')
        exit(1)

    if dedicated_node_count * int(cores[1]) + int(cores[0]) > cores_limit:
        dedicated_node_count = floor((cores_limit - int(cores[0]))/int(cores[1]))
        print('Core limit {} reached!'.format(cores_limit))

    print('Creating pool [{}] with [{}] dedicated nodes from custom image [{}]'.format(
        pool_id, dedicated_node_count, _VM_IMG.split('/')[-1]))
    print('VM size is [{}], vCPUs is [{}] each, max. task(s)/node is [{}]'.format(
        _POOL_VM_SIZE, int(cores[1]), _MAX_TASK_PER_NODE))
    if int(cores[0]) > 0:
        print('Cores currently in use from other pool(s) is [{}]'.format(int(cores[0])))

    # Create a new pool of Linux compute nodes using an Azure Virtual Machines Marketplace or customized image.
    # For more information about creating pools of Linux nodes, see:
    # https://azure.microsoft.com/documentation/articles/batch-linux-nodes/

    new_pool = batchmodels.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(virtual_machine_image_id=_VM_IMG),
            node_agent_sku_id='batch.node.ubuntu 16.04'),
        vm_size=_POOL_VM_SIZE,
        target_dedicated_nodes=dedicated_node_count,
        max_tasks_per_node=_MAX_TASK_PER_NODE,
        enable_inter_node_communication=False,
        resize_timeout=datetime.timedelta(minutes=10),
        task_scheduling_policy=batchmodels.TaskSchedulingPolicy(node_fill_type='spread')

        # Configure the start task for the pool
        # https://docs.microsoft.com/en-us/python/api/azure-batch/azure.batch.models.starttask?view=azure-python
        # start_task=batchmodels.StartTask(
        #     command_line="printenv AZ_BATCH_NODE_STARTUP_DIR", #STARTTASK_RESOURCE_FILE,
        #     run_elevated=True,
        #     wait_for_success=True,
        #     resource_files=[
        #         batchmodels.ResourceFile(file_path=STARTTASK_RESOURCE_FILE, blob_source=SAS_URL)
        #     ]),
    )
    batch_service_client.pool.add(new_pool)

    while True:
        new_pool = batch_service_client.pool.get(pool_id)
        if new_pool.allocation_state != 'steady':
            print(time.strftime('[%H:%M:%S %x]') + ' Waiting pool to be steady', end='\r')
            time.sleep(1)
        else:
            break

    batch_service_client.pool.enable_auto_scale(
        pool_id,
        auto_scale_formula=('$NodeDeallocationOption=taskcompletion;$tasks=($PendingTasks.'
                            'GetSamplePercent(TimeInterval_{})<70) ? max(0,$PendingTasks.GetSample(1)) : '
                            'max($PendingTasks.GetSample(1),avg($PendingTasks.GetSample(TimeInterval_{})));'
                            '$targetVMs = max($tasks/{}, max($RunningTasks.GetSample(TimeInterval_{})/{}));'
                            '$TargetDedicated = min({}, $targetVMs)'.format(
                                scale_interval, scale_interval, _MAX_TASK_PER_NODE, scale_interval, _MAX_TASK_PER_NODE,
                                dedicated_node_count)),
        auto_scale_evaluation_interval=auto_scale_eval_interval)
    print(time.strftime('[%H:%M:%S %x]') + ' Pool steady and autoscale enabled')


def add_tasks(batch_service_client, job_id, lsFilesNCommands, output_container_sas_url):
    """
    Adds a task for each pair with input file and command line in the collection to the specified job.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID of the job to which to add the tasks.
    :param list lsFilesNCommands: A collection with pairs of input files and commands. One task per pair.
    :param output_container_sas_token: A SAS token granting write access to
    the specified Azure Blob storage container.
    """

    print('Adding {} tasks to job [{}]...'.format(len(lsFilesNCommands), job_id))

    tasks = list()

    output_pattern = '*.tar.gz'  # This is bottleneck..Copy fourd file over and over causes issues try "%s_*.nii.gz"%(pathology) again
    for ix in range(len(lsFilesNCommands)):
        command = "/bin/bash -c \"" + lsFilesNCommands[ix][1] + "\""
        tasks.append(batch.models.TaskAddParameter(
            id='Task{}'.format(ix),
            command_line=command,
            resource_files=[batchmodels.ResourceFile(http_url=lsFilesNCommands[ix][0].http_url,file_path=lsFilesNCommands[ix][0].file_path),
                            batchmodels.ResourceFile(http_url="https://radcmri02.blob.core.windows.net/yb-init/" + _CLOUD_BASH, file_path=_CLOUD_BASH)],
            output_files = [batchmodels.OutputFile(file_pattern=output_pattern,
                            destination=batchmodels.OutputFileDestination(
                                container=batchmodels.OutputFileBlobContainerDestination(
                                    container_url=output_container_sas_url)),
                            upload_options=batchmodels.OutputFileUploadOptions(
                                upload_condition=batchmodels.OutputFileUploadCondition.task_success))],
            user_identity = batch.models.UserIdentity(
                            auto_user=batch.models.AutoUserSpecification(scope=batch.models.AutoUserScope.task,
                                                                    elevation_level=batch.models.ElevationLevel.admin)
            )
        )
        )
        batch_service_client.task.add_collection(job_id, tasks)


def wait_for_tasks_to_complete(batch_service_client, job_id, timeout):
    """
    Returns when all tasks in the specified job reach the Completed state.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The id of the job whose tasks should be monitored.
    :param timedelta timeout: The duration to wait for task completion. If all
    tasks in the specified job do not reach Completed state within this time
    period, an exception will be raised.
    """
    timeout_expiration = datetime.datetime.now() + timeout

    print("Monitoring all tasks for 'Completed' state, timeout in {}..."
          .format(timeout), end='\n')

    while datetime.datetime.now() < timeout_expiration:
        tasks = batch_service_client.task.list(job_id)

        incomplete_tasks = [task for task in tasks if
                            task.state != batchmodels.TaskState.completed]
        task_counts = batch_service_client.job.get_task_counts(job_id=job_id)

        print((time.strftime('[%H:%M:%S %x]') +
               ' tasks running/completed/active, succeed/failed: {}/{}/{}, {}/{}').format(
                task_counts.running, task_counts.completed, task_counts.active, task_counts.succeeded,
                task_counts.failed), end='\r', flush=True)
        if not incomplete_tasks:
            print()
            return True
        else:
            time.sleep(1)

    print()
    raise RuntimeError("ERROR: Tasks did not reach 'Completed' state within "
                       "timeout period of " + str(timeout))


def main(argv):
    sLabel = str(sys.argv[1]) #label for downloads

    start_time = datetime.datetime.now().replace(microsecond=0)
    print('Sample start: {}'.format(start_time))
    print()

    blob_client = azureblob.BlockBlobService(
        account_name=_STORAGE_ACCOUNT_NAME,
        account_key=_STORAGE_ACCOUNT_KEY)

    input_container_name = _CLOUD_CONTAIN_IN
    output_container_name = _CLOUD_CONTAIN_OUT

    input_container_created = blob_client.create_container(input_container_name, fail_on_exist=True)
    if (not input_container_created):
        print('Error creating input container [{}]. Has this job already been run?'.format(input_container_name))
        sys.ext("Error running batch job")

    output_container_created = blob_client.create_container(output_container_name, fail_on_exist=True)
    if (not output_container_created):
        print('Error creating output container [{}]. Has this job already been run?'.format(output_container_name))
        sys.ext("Error running batch job")

    # Get the files
    lsSubjId = glob.glob('../upload/*.nii')

    if len(lsSubjId) > 98:
        raise ValueError("This version supports at most 98 subjects. Please reduce the number of subjects in the upload folder.")

    lsFilesNCommands = []
    for i in range(len(lsSubjId)):
        sFile_to_append = lsSubjId[i]
        sSubjID = lsSubjId[i][10:len(lsSubjId[i])-4]
        sCommand_to_append = './' + _CLOUD_BASH + ' ' + sLabel + ' ' + sSubjID # Cloud BASH script run here
        # Upload input files to blob input container
        objFileTmp = upload_file_to_container(blob_client, input_container_name, sFile_to_append)
        lsFilesNCommands.append([objFileTmp, sCommand_to_append])

    # Obtain a shared access signature URL that provides write access to the output
    # container to which the tasks will upload their output.
    output_container_sas_url = get_container_sas_url(
        blob_client,
        output_container_name,
        azureblob.BlobPermissions.WRITE)

    # Create a Batch service client. We'll now be interacting with the Batch
    # service in addition to Storage
    credentials = ServicePrincipalCredentials(
        client_id=_APPLICATION_ID,
        secret=_APPLICATION_SECRET,
        tenant=_TENANT_ID,
        resource='https://batch.core.windows.net/'
    )

    batch_client = batch.BatchServiceClient(credentials, batch_url=_BATCH_ACCOUNT_URL)

    try:
        # Create the pool that will contain the compute nodes that will execute the tasks.
        dedicated_node_count = ceil(len(lsFilesNCommands)/_MAX_TASK_PER_NODE)
        create_pool(batch_client, _POOL_ID, _SCALE_INT, _AUTO_SCALE_EVAL_INT, dedicated_node_count)
    except batchmodels.BatchErrorException as err:
        print_batch_exception(err)
        print('Error creating pool [{}]'.format(_POOL_ID))
        blob_client.delete_container(input_container_name)
        blob_client.delete_container(output_container_name)
        print('Deleted containers [{}] & [{}] and exiting'.format(input_container_name, output_container_name))
        sys.exit(2)

    try:
        # Create the job that will run the tasks.
        create_job(batch_client, _JOB_ID, _POOL_ID)

        # Add the tasks to the job. Pass the input files and a SAS URL
        # to the storage container for output files.
        add_tasks(batch_client, _JOB_ID, lsFilesNCommands, output_container_sas_url)

        # Pause execution until tasks reach Completed state.
        wait_for_tasks_to_complete(batch_client,
                                   _JOB_ID,
                                   datetime.timedelta(minutes=60*48))

        print("  Success! All tasks reached the 'Completed' state within the "
              "specified timeout period.")

        # TODO: Download files in output containers and merge. Do in this script or merge manually?
        try:
            block_blob_service = azureblob.BlockBlobService(account_name=_STORAGE_ACCOUNT_NAME,
                                                            account_key=_STORAGE_ACCOUNT_KEY)

            blobs = block_blob_service.list_blobs(output_container_name)

            s_dir_out = os.getcwd() + '/../down_' + sLabel + '/'
            if not os.path.exists(s_dir_out):
                os.mkdir(s_dir_out)

            for blob in blobs:
                block_blob_service.get_blob_to_path(output_container_name, blob.name,
                                                    s_dir_out + blob.name)

        except Exception as e:

            print(e)
    except batchmodels.BatchErrorException as err:
        print_batch_exception(err)
        raise

    # Delete input container in storage
    print('Deleting container [{}]...'.format(input_container_name))
    blob_client.delete_container(input_container_name)

    if _CLOUD_CONTAIN_DELETE:
        print('Deleting container [{}]...'.format(output_container_name))
        blob_client.delete_container(output_container_name)

    # Print out some timing info
    end_time = datetime.datetime.now().replace(microsecond=0)
    print()
    print('Sample end: {}'.format(end_time))
    print('Elapsed time: {}'.format(end_time - start_time))
    print()

    # Clean up Batch resources (if the user so chooses).
    if _JOB_DELETE:
        batch_client.job.delete(_JOB_ID)

    if _POOL_DELETE:
        batch_client.pool.delete(_POOL_ID)

if __name__ == '__main__':
    main(sys.argv[1:])
