import re
# This class is used to contain meta data of scan that can be parsed from the path
# i.e. date, visit, projid, potocol
class Mri_wrapper(object):

    def __init__(self, path):
        self.path = path
        self.protocol = ""
        date_visit_projid_search = re.search("\d{6}_\d{2}_\d{8}", path)

        if date_visit_projid_search is None:
            print("WARNING: could not find date_visit_projid from " + path)

        if date_visit_projid_search is not None:
            date_visit_projid = date_visit_projid_search.group(0).split("_")
            self.date = date_visit_projid[0]
            self.visit = date_visit_projid[1]
            self.projid = date_visit_projid[2]

        if re.search("bannockburn", path ) is not None:
            self.protocol = "bannockburn"
        if re.search("mg", path) is not None:
            self.protocol = "mg"
        if re.search("uc", path) is not None:
            self.protocol = "uc"
        if re.search("mcw", path) is not None:
            self.protocol = "mcw"
