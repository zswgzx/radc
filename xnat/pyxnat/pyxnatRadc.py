from pyxnat import Interface
from getpass import getpass
# https://pyxnat.readthedocs.io/en/latest/

xnatUrl = 'http://radcxnat.rush.edu'
usr = input('Enter XNAT username: ')
xnatPasswd = getpass("Enter password for {}@{}: ".format(usr, xnatUrl[7:]))
radcxnat = Interface(server=xnatUrl, user=usr, password=xnatPasswd)


def changeLabels(xnatProjectID, xnatSubjectID, xnatExperimentID, radcScankey):
    """modify both xnat subject & experiment labels if not 'standardized'

    :param str xnatProjectID: xnat project name
    :param str xnatSubjectID: XNAT_Sxxxxx 
    :param str xnatExperimentID: XNAT_Exxxxx
    :param str radcScankey: yymmdd_fu_projid"""

    radcProjectID = radcScankey[-8:]

    radcxnat.select(
        '/project/{}/subject/{}'.format(xnatProjectID, xnatSubjectID)).attrs.set(
        'label', radcProjectID)
    radcxnat.select(1
        '/project/{}/subject/{}/experiment/{}'.format(
            xnatProjectID, xnatSubjectID, xnatExperimentID)).attrs.set(
        'label', radcScankey)


def getXnatSubjID(xnatProjectID, xnatSubjectLabel):
    """get xnat subject ID from its label

    :param str xnatProjectID: xnat project name
    :param str xnatSubjectLabel: radc projid"""

    print(radcxnat.select('/project/{}/subject/{}'.format(xnatProjectID, xnatSubjectLabel)).id())

# changeLabels('uc_160125', 'XNAT_S00027', 'XNAT_E00020', '160125_02_09203281')

# getXnatSubjID('szTest', '22711410')

# sharing same experiment across projects (successful but returns database 'error message' below)
# projectToShare = 'TEST_AJ3'
# experiment = 'XNAT_E00006'
# radcxnat.select('/projects/subjects/experiment/{}'.format(experiment)).share(projectToShare)
# pyxnat.core.errors.DatabaseError: b'<html>\n<head>\n   <title>Status page</title>\n</head>\n<body>\n<h3>Already assigned to project:pr000r00</h3><p>You can get technical details <a href="http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.10">here</a>.<br>\nPlease continue your visit at our <a href="/">home page</a>.\n</p>\n</body>\n</html>\n'

# exps=radcxnat.select.projects().subjects().experiment('180712_00_22711410')
# for exp in exps:
#     print(exp.id())
#     print(exp.parent().id())
#     print(exp.parent().parent().id())
assessors=radcxnat.select.projects().subjects().experiment('180712_00_22711410').assessors()
for assessor in assessors:
    print(assessor.id())

radcxnat.disconnect()
