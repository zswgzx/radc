class Scan_proc_summary(object):
    def __init__(self, record):

        record_array = record.split("|")
        # Todo: add regex validation?

        self.record = record
        self.scan_key = record_array[1]
        self.projid = record_array[2]
        self.visit = record_array[3]
        self.scandatetime = record_array[4]
        self.protocol = record_array[5]
        self.startdate = record_array[6]
        self.scanexists = record_array[7]
        self.processed = record_array[8]
        self.pre_check = record_array[9]
        self.post_qa = record_array[10]

    def expected_path(self):
        protocol_path = ""

        if self.protocol == 'BNK':
            protocol_path = "bannockburn"
        elif self.protocol == 'MG':
            protocol_path = "mg"
        elif self.protocol == 'UC':
            protocol_path = 'uc'

        return "/mri/invivo/raw/" + protocol_path + "/" + self.startdate + "/" + self.scan_key;
