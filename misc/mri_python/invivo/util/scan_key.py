from datetime import datetime

#Scankey example 090429_06_75833578

class Scan_key(object):
    def __init__(self, scan_key):
        self.scan_key = scan_key

        key_array = scan_key.split("_")

        self.datestr = key_array[0]
        self.visit = key_array[1]
        self.projid = key_array[2]

        self.date = datetime.strptime( "20"+self.datestr,  "%Y%m%d" )

    def __str__(self):
     return self.scan_key
