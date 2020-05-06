class DTI():
    names = [ "DIFF_DTI", "dti", "HARDI", "Obl_DTI_36sl"]
    def __init__(self):
        pass
    def get_enum_value():
       return "DTI"

class MPRAGE():
    names = [ "t1_mpr", "mprage", "Survey_MST", "3D_MPRAGE"]
    def __init__(self):
        pass
    def get_enum_value():
       return "MPRAGE"

class FLAIR():
    names = ["flair", "t2_flair"]
    def __init__(self):
        pass
    def get_enum_value():
       return "FLAIR"

class EPI():
    names = ["ep2d", "epi", "SE_EPI" ]
    def __init__(self):
        pass
    def get_enum_value():
       return "EPI"

class T2_MAP():
    names = ["T2_map", "T2map"]
    def __init__(self):
        pass
    def get_enum_value():
       return "T2_MAP"

# class SURVEY():
#     names = ["Survey"]
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return "SURVEY"

class FIELD_MAP():
    names = ["gre_field_mapping", "FieldMap"]
    def __init__(self):
        pass
    def get_enum_value():
       return "FIELD_MAP"

class SWI():
    names = ["SWI"]
    def __init__(self):
        pass
    def get_enum_value():
       return "SWI"

class QSM():
    names = ["QSM"]
    def __init__(self):
        pass
    def get_enum_value():
       return "QSM"

class LOCALIZER():
    names = ["LOCALIZER"]
    def __init__(self):
        pass
    def get_enum_value():
       return "LOCALIZER"

class PHASE_MAP():
    names = ["Obl_2-echo_GRE"]
    def __init__(self):
        pass
    def get_enum_value():
       return "PHASE_MAP"


class T2_FLAIR():
    names = ["Obl_T2_FLAIR"]
    def __init__(self):
        pass
    def get_enum_value():
       return "T2_FLAIR"


# class RESTING_FMRI():
#    names = [""]
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return "RESTING_FMRI"

class REF_SCAN():
    names = ["WIP_ACR", "Ref_SHC_8"]
    def __init__(self):
        pass
    def get_enum_value():
       return "REF_SCAN"


# class SE_EPI_A():
#     names = [""]
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return "SE_EPI_A"
#
# class SE_EPI_P():
#     names = [""]
#     def __init__(self):
#         pass
#     def get_enum_value():
#        return "SE_EPI_P"
#
#
class OTHER:
    names = [""]
    def __init__(self):
        pass
    def get_enum_value():
       return "OTHER"


def find_matching_nifti_for_scantype( scan_type, nifti_entries ):
    result = []
    for temp_entry in nifti_entries:
        for temp_match_pattern in scan_type.names:
            if(temp_match_pattern in temp_entry.name.lower()):
                result.append( temp_entry )
                break
    return result

def find_matching_scantype_for_nifti( nifti_name ):
    # OTHER will catch all and must be last in this array
    scan_types = [DTI, MPRAGE, FLAIR, T2_MAP, EPI, FIELD_MAP,  SWI, QSM, LOCALIZER, PHASE_MAP,  REF_SCAN, OTHER]
    for scan_type in scan_types:
        for name in scan_type.names:
            if( name.lower() in nifti_name.lower() ):
                return scan_type
    return Other
        
    
    
