from datetime import datetime
from .ScanTypes import *

MRI_BASE_DIR = "/mri/invivo/raw/"


class Bannockburn():
    def __init__(self):
        self.start_dates = ["061130", "090211"]

    def get_path(self, scanKey):
        start_date = get_matching_startdate(self.start_dates, scanKey)
        if (start_date is None):
            print("Could not find BNK start date for " + scanKey)
        return MRI_BASE_DIR + "bannockburn/" + start_date + "/" + scanKey.scan_key

    def __str__(self):
        return "Bacnnockburn Scan"


class MG():
    def __init__(self):
        self.start_dates = ["120501", "150715", "160621", "160627"]

    def get_path(self, scanKey):
        start_date = get_matching_startdate(self.start_dates, scanKey)
        if (start_date is None):
            print("Could not find UC start date for " + scanKey)
        return MRI_BASE_DIR + "mg/" + start_date + "/" + scanKey.scan_key


    def __str__(self):
        return "Morton Grove scan"


class UC():
    def __init__(self):
        self.start_dates = ["120221", "140922", "150706", "151120", "160125", "180604"]

    def get_path(self, scanKey):
        start_date = get_matching_startdate(self.start_dates, scanKey)
        if (start_date is None):
            print("Could not find Rush start date for " + scanKey)
        return MRI_BASE_DIR + "uc/" + start_date + "/" + scanKey.scan_key

    def __str__(self):
        return "UC scan"


def get_matching_startdate(start_dates, scan_key):
    result = ""
    for temp_start_str in start_dates:
        if (result == ""):
            result = temp_start_str
        temp_start_date = parse_6_char_date(temp_start_str)

        if (scan_key.date >= temp_start_date):
            result = temp_start_str
        else:
            break
    return result


def parse_6_char_date(date_str):
    if (len(date_str) != 6):
        print("Invalid date length")
        return
    year = "20" + date_str[0:2]
    month = date_str[2:4]
    day = date_str[4:6]

    return datetime.strptime("" + year + month + day, "%Y%m%d")
