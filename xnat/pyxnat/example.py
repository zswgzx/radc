from pyxnat import Interface
from getpass import getpass
# from pyxnat import manage
# https://pyxnat.readthedocs.io/en/latest/

xnatUrl = 'http://radcxnat.rush.edu'
usr = input('Enter XNAT username: ')
xnatPasswd = getpass("Enter password for {}@{}: ".format(usr, xnatUrl[7:]))
radcxnat = Interface(server=xnatUrl, user=usr, password=xnatPasswd)

# TODO:
# add schema
# https://wiki.xnat.org/workshop-2016/step-3-of-10-adding-new-data-types-29034258.html
# manage.SchemaManager.add(self=manage.SchemaManager,
#                          url='http://central.xnat.org/schemas/xnat/xnat.xsd')

expLabel = '22711410'
sub = radcxnat.select('/project/szTest/subject/{}'.format(expLabel))
sub.attrs()

# search engine demo
# project = project
# row = 'xnat:subjectData'
# columns = ['xnat:subjectData/PROJECT', 'xnat:subjectData/SUBJECT_ID']
# criteria = [('xnat:subjectData/SUBJECT_ID', 'LIKE', '*'),
#             ('xnat:subjectData/PROJECT', '=', project), 'AND']
# # radcxnat.manage.search.save_template('shared', row, columns, criteria, sharing='public',
# #                                      description='search shared subject')
# tab = radcxnat.select(row, columns).where(criteria)
# print(tab)

radcxnat.disconnect()
