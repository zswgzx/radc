from __future__ import print_function

import datetime
import os
import sys
import time
from subprocess import call

import azure.storage.blob as azureblob
import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
# from azure.common.credentials import ServicePrincipalCredentials

sys.path.append('.')
sys.path.append('..')

# global
_BATCH_ACCOUNT_NAME = 'batch'
_BATCH_ACCOUNT_KEY = 'key'
_BATCH_ACCOUNT_URL = 'https://xxx.eastus.batch.azure.com'
_STORAGE_ACCOUNT_NAME = 'storage'
_STORAGE_ACCOUNT_KEY = 'key2'
_POOL_ID = 'antspool'
# _DEDICATED_POOL_NODE_COUNT = 2
# _LOW_PRIORITY_POOL_NODE_COUNT = 0
# _POOL_VM_SIZE = 'standard_a2'
_JOB_ID = 'ants'
# _MAX_TASK_PER_NODE = 1


def query_yes_no(question, default="yes"):
    """
    Prompts the user for yes/no input, displaying the specified question text.

    :param str question: The text of the prompt for input.
    :param str default: The default if the user hits <ENTER>. Acceptable values are 'yes', 'no', and None.
    :rtype: str
    :return: 'yes' or 'no'
    """
    valid = {'y': 'yes', 'n': 'no'}
    if default is None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError("Invalid default answer: '{}'".format(default))

    while 1:
        choice = input(question + prompt).lower()
        if default and not choice:
            return default
        try:
            return valid[choice[0]]
        except (KeyError, IndexError):
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


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
    :return: A ResourceFile initialized with a SAS URL appropriate for Batch tasks.
    """
    blob_name = os.path.basename(file_path)

    print('Uploading file {} to container [{}]...'.format(file_path, container_name))

    block_blob_client.create_blob_from_path(container_name, blob_name, file_path)

    # Obtain the SAS token for the container.
    sas_token = get_container_sas_token(block_blob_client, container_name, azureblob.BlobPermissions.READ)

    sas_url = block_blob_client.make_blob_url(container_name, blob_name, sas_token=sas_token)

    return batchmodels.ResourceFile(file_path=blob_name, blob_source=sas_url)


def get_container_sas_token(block_blob_client, container_name, blob_permissions):
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
    # Obtain the SAS token for the container, setting the expiry time and permissions.
    # In this case, no start time is specified, so the shared access signature becomes valid immediately.
    # Expiration is in 2 hours.
    container_sas_token = block_blob_client.generate_container_shared_access_signature(
        container_name, permission=blob_permissions, expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=2))

    return container_sas_token


def get_container_sas_url(block_blob_client, container_name, blob_permissions):
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


def create_pool(batch_service_client, pool_id):
    """
    Creates a pool of compute nodes with the specified OS settings.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str pool_id: An ID for the new pool.
    """
    print('Creating pool [{}]...'.format(pool_id))

    # Create a new pool of Linux compute nodes using a custom VM using AAD authentication

    call(["az", "batch", "pool", "create", "--json-file",
          "/home/shengwei/work/programs/azure-batch-python/antsReg/antspool.json"])


def create_job(batch_service_client, job_id, pool_id):
    """
    Creates a job with the specified ID, associated with the specified pool.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID for the job.
    :param str pool_id: The ID for the pool.
    """
    print('Creating job [{}]...'.format(job_id))

    job = batch.models.JobAddParameter(job_id, batch.models.PoolInformation(pool_id=pool_id))

    batch_service_client.job.add(job)


def add_tasks(batch_service_client, job_id, input_files, output_container_sas_url):
    """
    Adds a task for each input file in the collection to the specified job.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID of the job to which to add the tasks.
    :param list input_files: A collection of input files. One task will be created for each input file.
    :param output_container_sas_url: A SAS token granting write access to the specified Azure Blob storage container.
    """

    print('Adding {} tasks to job [{}]...'.format(len(input_files) - 1, job_id))

    tasks = []
    output_pattern = "*-[01w]*"
    task_idx = 0

    for idx, input_file in enumerate(input_files):
        input_file_path = input_file.file_path
        subjid = "".join(input_file_path.split('.')[:-2])
        subjid = "".join(subjid.split('-')[0])
        node_file = [s for s in input_files if subjid in s]
        node_file.append(s for s in input_files if "template" in s)
        if subjid != "template":
            command = "/bin/bash -c \"$ANTSPATH/antsRegistration -d 3 -o [{}-,{}-warped.nii.gz] " \
                      "-n Linear -w [0.005,0.995] -u 0 -r [template-aging1.nii.gz,{}-masked.nii.gz,1]" \
                      " -t Rigid[0.1] -m MI[template-aging1.nii.gz,{}-masked.nii.gz,1,32,Regular,0.25]" \
                      " -c [1000x500x250x100,1e-6,10] -f 8x4x2x1 -s 3x2x1x0vox" \
                      " -t Affine[0.1] -m MI[template-aging1.nii.gz,{}-masked.nii.gz,1,32,Regular,0.25]" \
                      " -c [1000x500x250x100,1e-6,10] -f 8x4x2x1 -s 3x2x1x0vox" \
                      " -t SyN[0.25] -m CC[template-aging1.nii.gz,{}-masked.nii.gz,1,4]" \
                      " -c [100x70x50x20,1e-6,10] -f 8x4x2x1 -s 3x2x1x0vox" \
                      "\"".format(subjid, subjid, subjid, subjid, subjid, subjid)
            tasks.append(batch.models.TaskAddParameter(
                id='Task{}'.format(task_idx), command_line=command,
                environment_settings=[batchmodels.EnvironmentSetting("ANTSPATH", "/usr/local/ants/v2.3.1/bin")],
                resource_files=node_file,
                output_files=[batchmodels.OutputFile(
                    output_pattern, destination=batchmodels.OutputFileDestination(
                        container=batchmodels.OutputFileBlobContainerDestination(output_container_sas_url)),
                    upload_options=batchmodels.OutputFileUploadOptions(
                        batchmodels.OutputFileUploadCondition.task_success))]
            )
            )
            task_idx = task_idx + 1
    batch_service_client.task.add_collection(job_id, tasks)


def wait_for_tasks_to_complete(batch_service_client, job_id, timeout):
    """
    Returns when all tasks in the specified job reach the Completed state.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The id of the job whose tasks should be monitored.
    :param timedelta timeout: The duration to wait for task completion. If all tasks in the specified job
    do not reach Completed state within this time period, an exception will be raised.
    """
    timeout_expiration = datetime.datetime.now() + timeout

    print("Monitoring all tasks for 'Completed' state, timeout in {}..."
          .format(timeout), end='\n')

    while datetime.datetime.now() < timeout_expiration:
        print(time.strftime("%H:%M:%S"), end='\r')
        sys.stdout.flush()
        tasks = batch_service_client.task.list(job_id)

        incomplete_tasks = [task for task in tasks if task.state != batchmodels.TaskState.completed]
        if not incomplete_tasks:
            print()
            return True
        else:
            time.sleep(1)

    print()
    raise RuntimeError("ERROR: Tasks did not reach 'Completed' state within timeout period of " + str(timeout))


if __name__ == '__main__':

    start_time = datetime.datetime.now().replace(microsecond=0)
    print('Batch started: {}'.format(start_time))
    print()

    blob_client = azureblob.BlockBlobService(account_name=_STORAGE_ACCOUNT_NAME, account_key=_STORAGE_ACCOUNT_KEY)

    input_container_name = 'inputs'
    output_container_name = 'outputs'
    blob_client.create_container(input_container_name, fail_on_exist=False)
    blob_client.create_container(output_container_name, fail_on_exist=False)
    print('Container [{}] created.'.format(input_container_name))
    print('Container [{}] created.'.format(output_container_name))

    # Upload input files to blob input container, change as needed
    input_file_paths = []
    for folder, subs, files in os.walk('/home/data/'):
        for filename in files:
            if filename.endswith(".nii.gz"):
                input_file_paths.append(os.path.abspath(os.path.join(folder, filename)))

    # Upload the input files. This is the collection of files that are to be processed by the tasks.
    input_files = [upload_file_to_container(blob_client, input_container_name, file_path)
                   for file_path in input_file_paths]

    # Obtain a shared access signature URL that provides write access to the output container.
    output_container_sas_url = get_container_sas_url(blob_client, output_container_name,
                                                     azureblob.BlobPermissions.WRITE)

    # Create a Batch service client. We'll now be interacting with the Batch service in addition to Storage
    credentials = batchauth.SharedKeyCredentials(_BATCH_ACCOUNT_NAME, _BATCH_ACCOUNT_KEY)
    # credentials = ServicePrincipalCredentials(
    #     client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    #     secret="98ec54bb11d8db52c506",
    #     tenant="",
    #     resource="https://batch.core.windows.net/"
    # )
    batch_client = batch.BatchServiceClient(credentials, base_url=_BATCH_ACCOUNT_URL)

    try:
        # Create pool
        create_pool(batch_client, _POOL_ID)

        # Create the job that will run the tasks.
        create_job(batch_client, _JOB_ID, _POOL_ID)

        # Add the tasks to the job. Pass the input files and a SAS URL to the storage container for output files.
        add_tasks(batch_client, _JOB_ID, input_files, output_container_sas_url)

        # Pause execution until tasks reach Completed state, change timedelta as needed.
        wait_for_tasks_to_complete(batch_client, _JOB_ID, datetime.timedelta(minutes=90))

        print("Success! All tasks reached the 'Completed' state within the specified timeout period.")

    except batchmodels.batch_error.BatchErrorException as err:
        print_batch_exception(err)
        raise

    # Delete input container in storage
    print('Deleting container [{}]...'.format(input_container_name))
    blob_client.delete_container(input_container_name)

    # Print out some timing info
    end_time = datetime.datetime.now().replace(microsecond=0)
    print()
    print('Job end: {}'.format(end_time))
    print('Elapsed time: {}'.format(end_time - start_time))
    print()

    # Download contents in output container from storage and then delete container
    try:
        blobs = blob_client.list_blobs(output_container_name)
        for blob in blobs:
            blob_client.get_blob_to_path(output_container_name, blob.name, "./" + blob.name)
    except Exception as e:
        print(e)
    print('Deleting container [{}]...'.format(output_container_name))
    print()
    blob_client.delete_container(output_container_name)

    # Clean up Batch resources (if the user so chooses).
    if query_yes_no('Delete job?') == 'yes':
        batch_client.job.delete(_JOB_ID)

    if query_yes_no('Delete pool?') == 'yes':
        batch_client.pool.delete(_POOL_ID)
