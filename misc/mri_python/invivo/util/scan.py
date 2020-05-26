from datetime import datetime

MRI_RAW_BASE_DIR = '/mri/invivo/raw/'


class ScanKey(object):
    #Scankey example 090429_06_75833578
    def __init__(self, scan_key):
        self.scan_key = scan_key

        key_array = scan_key.split('_')

        self.datestr = key_array[0]
        self.visit = key_array[1]
        self.projid = key_array[2]
        self.date = datetime.strptime( "20"+self.datestr,  "%Y%m%d" )

    def __str__(self):
     return self.scan_key


class Bannockburn():
    def __init__(self):
        self.start_dates = ('090211')

    def get_path(self, scanKey):
        start_date = get_matching_startdate(self.start_dates, scanKey)
        if start_date is None:
            print('Could not find BNK start date for ' + scanKey)
        return MRI_RAW_BASE_DIR + 'bannockburn/' + start_date + '/' + scanKey.scan_key

    def __str__(self):
        return 'Bacnnockburn Scan'


class MG():
    def __init__(self):
        self.start_dates = [('120501',), ('150715',), ('160621',), ('160627',)]

    def get_path(self, scanKey):
        start_date = get_matching_startdate(self.start_dates, scanKey)
        if (start_date is None):
            print('Could not find MG start date for ' + scanKey)
        return MRI_RAW_BASE_DIR + 'mg/' + start_date + '/' + scanKey.scan_key

    def __str__(self):
        return 'Morton Grove scan'


class UC():
    def __init__(self):
        self.start_dates = [('120221',), ('140922',), ('150706',), ('151120',), ('160125',), ('180604',)]

    def get_path(self, scanKey):
        start_date = get_matching_startdate(self.start_dates, scanKey)
        if (start_date is None):
            print('Could not find UC start date for ' + scanKey)
        return MRI_RAW_BASE_DIR + 'uc/' + start_date + '/' + scanKey.scan_key

    def __str__(self):
        return 'University of Chicago scan'


class DTI():
    names = ['DIFF_DTI', 'dti', 'HARDI', 'Obl_DTI_36sl']
    def __init__(self):
        pass
    def get_enum_value():
       return 'DTI'

class MPRAGE():
    names = ['t1_mpr', 'mprage', '3D_MPRAGE']
    def __init__(self):
        pass
    def get_enum_value():
       return 'MPRAGE'

class FLAIR():
    names = ['flair', 't2_flair']
    def __init__(self):
        pass
    def get_enum_value():
       return 'FLAIR'

class EPI():
    names = ['ep2d', 'epi', 'SE_EPI' ]
    def __init__(self):
        pass
    def get_enum_value():
       return 'EPI'

class T2_MAP():
    names = ['T2_map', 'T2map']
    def __init__(self):
        pass
    def get_enum_value():
       return 'T2_MAP'

# class SURVEY():
#     names = ['Survey']
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return 'SURVEY'

class FIELD_MAP():
    names = ['gre_field_mapping', 'FieldMap']
    def __init__(self):
        pass
    def get_enum_value():
       return 'FIELD_MAP'

class SWI():
    names = ['SWI']
    def __init__(self):
        pass
    def get_enum_value():
       return 'SWI'

class QSM():
    names = ['QSM']
    def __init__(self):
        pass
    def get_enum_value():
       return 'QSM'

class LOCALIZER():
    names = ['LOCALIZER']
    def __init__(self):
        pass
    def get_enum_value():
       return 'LOCALIZER'

class PHASE_MAP():
    names = ['Obl_2-echo_GRE']
    def __init__(self):
        pass
    def get_enum_value():
       return 'PHASE_MAP'

# class RESTING_FMRI():
#    names = ['']
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return 'RESTING_FMRI'

# class SE_EPI_A():
#     names = ['']
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return 'SE_EPI_A'
#
# class SE_EPI_P():
#     names = ['']
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return 'SE_EPI_P'
#
#
class OTHER:
    names = ['']
    def __init__(self):
        pass
    def get_enum_value():
       return 'OTHER'


def get_matching_startdate(start_dates, scan_key):
    for temp_start_str in start_dates:
        result = temp_start_str
        temp_start_date = parse_6_char_date(temp_start_str)

        if scan_key.date >= temp_start_date:
            result = temp_start_str
        else:
            break
    return result


def parse_6_char_date(date_str):
    if (len(date_str) != 6):
        print('Invalid date length')
    year = '20' + date_str[0:2]
    month = date_str[2:4]
    day = date_str[4:6]

    return datetime.strptime('' + year + month + day, "%Y%m%d")


def find_matching_nifti_for_scantype(scan_type, nifti_entries):
    result = []
    for temp_entry in nifti_entries:
        for temp_match_pattern in scan_type.names:
            if temp_match_pattern in temp_entry.name.lower():
                result.append(temp_entry)
                break
    return result

def find_matching_scantype_for_nifti(nifti_name):
    # OTHER will catch all and must be last in this array
    scan_types = [DTI, MPRAGE, FLAIR, T2_MAP, EPI, FIELD_MAP,  SWI, QSM, LOCALIZER, PHASE_MAP,  REF_SCAN, OTHER]
    for scan_type in scan_types:
        for name in scan_type.names:
            if name.lower() in nifti_name.lower():
                return scan_type
    return Other
