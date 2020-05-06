from pyxnat import Interface
from getpass import getpass
# https://pyxnat.readthedocs.io/en/latest/

# login xnat server
xnatUrl = 'http://radcxnat.rush.edu'
usr = input('Enter XNAT username: ')
xnatPasswd = getpass("Enter password for {}@{}: ".format(usr, xnatUrl[7:]))
radcxnat = Interface(server=xnatUrl, user=usr, password=xnatPasswd)

# alternative login approach (not recommended)
# config = 'radcxnatAdmin.cfg'
# with open(config, 'w') as file:
#    file.write('{"server": "'.join()'"{}", "user": "{}", "password": "{}"}'.format(xnatUrl, usr, xnatPasswd))
# file.close()
# radcxnat = Interface(config=config)

# list all xnat project/subject/experiment(s) on server, just replace 'project' with desired type
# print(radcxnat.inspect.project_values())
# OR
# print(radcxnat.select.projects().get())

# print(radcxnat.inspect.experiment_values(datatype='xnat:mrSessionData'))

# list all xnat subjects in individual xnat project
# print(radcxnat.select.project('*uc*').subjects().get())
# OR
# print(radcxnat.select('/project/*uc*/subjects').get())

# list all users for xnat
# print(radcxnat.manage.users())

# searchable datatypes & fields, as in the schema?

# currently avail. data types that may be useful are:
# 'xnat:projectData'
# 'xnat:subjectData'
# 'xnat:mrSessionData'
# 'xnat:pVisitData'
# 'val:protocolData'
# 'xnat:investigatorData'
# 'xnat:qcManualAssessorData'
# 'xnat:qcAssessmentData'

# currently avail. subjectData sub-types that may be useful are:
# ID, GENDER_TEXT, PROJECTS, PROJECT, XNAT_COL_SUBJECTDATALABEL

# currently avail. mrSessionData sub-types that may be useful are:
# PROJECT, SUBJECT_ID, SUBJECT_LABEL, SESSION_ID, DATE, TYPE, SCANNER_CSV, DTI_COUNT, MR_SCAN_COUNT_AGG, LAST_MODIFIED

# currently avail. pVisitData sub-types that may be useful are:
# SUBJECT_ID, EXPT_ID, DATE, PROJECT, PROTOCOLVERSION, PROTOCOLID

# print(radcxnat.inspect.datatypes('xnat:mrSessionData', 'SUBJECT*'))

# radcxnat.inspect.set_autolearn('True')

# delete project/subject(id, not label!)/experiment (use cautiously!)
subj = radcxnat.select('/project/{}/subject/{}/'.format(project, subject))
subj.delete()
# print('/project/{}/subject/{} deleted'.format(project, subject))

radcxnat.disconnect()
