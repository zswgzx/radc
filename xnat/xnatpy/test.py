import xnat
# https://xnat.readthedocs.io/en/latest/static/tutorial.html

session = xnat.connect('http://radcxnat.rush.edu', user='admin', password='admin')
# project = 'pr000r00'
# proj = session.projects[project]

# download scan (includes all dicom/nii/resource files
session.experiments['XNAT_E00001'].scans['MPRAGE'].download('./MPRAGE.zip')

# for subject in proj.subjects.values():
#     print(subject.label)

session.disconnect()
