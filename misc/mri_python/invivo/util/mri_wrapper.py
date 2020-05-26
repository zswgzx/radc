import re

# This class obtains meta data (i.e. date, visit, projid, protocol) of scan from its path
class MriWrapper(object):
    def __init__(self, path):
        self.path = path
        scankey_search = re.search('\d{6}_\d{2}_\d{8}', path)

        if scankey_search is None:
            sys.exit('Could not find scan key from ' + path)
        else:
            scan_key = scankey_search.group(0).split('_')
            self.date = scan_key[0]
            self.visit = scan_key[1]
            self.projid = scan_key[2]

        if re.search('bannockburn', path):
            self.protocol = ('bannockburn',)
        elif re.search('mg', path):
            self.protocol = ('mg',)
        elif re.search('uc', path):
            self.protocol = ('uc',)
        else:
            sys.exit('No such active or valid protocol exists')
