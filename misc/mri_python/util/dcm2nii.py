import os
from nipype.interfaces.dcm2nii import Dcm2nii

def convertDicom2Nifti(dicom_dir, output_dir ):
    converted_files = dcm2nii_wrapper(dicom_dir, output_dir)
    # additional logic?
    return converted_files


def dcm2nii_wrapper(input_dir, output_dir):
    converter = Dcm2nii()
    converter.inputs.source_dir = input_dir
    converter.inputs.output_dir = output_dir
    converter.inputs.gzip_output = False
    converter.inputs.reorient_and_crop = False
    converter.inputs.reorient = False
    converter.inputs.events_in_filename = False
    converter.inputs.date_in_filename = False
    converter.inputs.protocol_in_filename = True
    converter.run()
    return converter.output_files
