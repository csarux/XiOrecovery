"""
Module : dcmcoher

A python module with utilities to correct DICOM files generated by plastimatch from XiO unarchived patients

César Rodríguez
Hospital Universitario de Fuenlabrada

"""

import pydicom as dcm
from pydicom.uid import generate_uid
from glob import glob
from pathlib import Path
from datetime import date, datetime
import csv

def correctImagePositionPatientInCTImages(patientID, studyset, dcmdir='xiodcm', prefct = 'image', deltaframes='deltaframes'):
    """
    A function to correct the ImagePositionPatient in the CT images using the 
    plastimatch produced dose file as a reference
    ...
    Attributes
    ----------
    patientID : str
        The identification of the patient for which the delta has been extracted. The delta is 
        specific of a patientID and stusyset pair. This parameter is required. 

    studyset : str
        The identification of the studyset for which the delta has been extracted. The delta is 
        specific of a patientID and stusyset pair. This parameter is required. 
        
    dcmdir : str
        The name of the directory output-dicom of the plastimatch convert command. 
        Default xiodcm
        
    prefct : str
        The prefix of the DICOM CT image files produced by the output-dicom option of 
        the plastimatch convert command. Default image
        
    deltaframes : str
        The name of the file containing the delta between the reference frames of the CT studyset
        and the structuset. The delta has been produced by deltact perl script. Default deltaframes.

    Returns
    -------
    None 

    """
    
    with open('./patient/' + deltaframes, mode = 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
   
    for row in csv_reader:
        filePatientID, CT, X, Y = row['PatientID'], row['CT'], row['X'], row['Y']
   
    if(filePatientID == PatientID & CT == studyset):
        ctfiles = glob(dcmdir + '/' + prefct + '*')
        
        for ctfile in ctfiles:
            ctdf = dcm.read_file(ctfile)
            ctdf.ImagePositionPatient = ImagePositionPatient
            ctdf.save_as(ctfile)        
        
    return

def correctRTPlan(dcmdir='xiodcm', prefdose='dose', prefct = 'image', prefss = 'rtss', planfile='RTPlan.dcm'):
    """
    A function to referred the generic RTPlan to the patient (demographics and geometry) 
    and to the DICOM-RT dose file
    ...
    Attributes
    ----------
    dcmdir : str
        The name of the directory output-dicom of the plastimatch convert command. 
        Default xiodcm
        
    prefdose : str
        The prefix of the DICOM-RT dose files produced by the output-dicom option of 
        the plastimatch convert command. Default dose
        
    prefct : str
        The prefix of the DICOM CT image files produced by the output-dicom option of 
        the plastimatch convert command. Default image
        
    prefss : str
        The prefix of the DICOM-RT structure set file produced by the output-dicom option of 
        the plastimatch convert command. Default rtss
        
    planfile : str
        The filename of the generic DICOM-RT plan file. Default RTPlan.dcm

    Returns
    -------
    None 

    """
    
    ctfiles = glob(dcmdir + '/' + prefct + '*')
    ctfile = ctfiles[0]
    ctdf = dcm.read_file(ctfile)
    
    PatientName = ctdf.PatientName
    PatientID = ctdf.PatientID
    PatientSex = ctdf.PatientSex
    PatientBirthDate = ctdf.PatientBirthDate
    
    
    doseFiles = glob(dcmdir + '/' + prefdose + '*')
    doseFile = doseFiles[0]
    dosedf = dcm.read_file(doseFile)
    
    rtssFiles = glob(dcmdir + '/' + prefss + '*')
    rtssFile = rtssFiles[0]
    ssdf = dcm.read_file(rtssFile)
    
    plandf = dcm.read_file(dcmdir + '/' + planfile)
    
    plandf.PatientName = PatientName
    plandf.PatientID = PatientID
    plandf.PatientSex = PatientSex
    plandf.PatientBirthDate = PatientBirthDate
    
    # Relate DICOM-RT Plan to DICOM-RT Dose
    # Dose -> Referenced RT Plan Sequence (300c,0002) 1 item(s) -> Referenced SOP Instance UID (0008,1155)
    plandf.SOPInstanceUID = dosedf[0x300c,0x0002][0][0x0008,0x1155].value
#    plandf[0x0002,0x0003].value = plandf.SOPInstanceUID

    # Relate DICOM-RT Plan to DICOM-RT Structure set
    plandf[0x300c,0x060][0][0x0008,0x1155].value = ssdf.SOPInstanceUID
    
    
    # Update other fields
    plandf.RTPlanLabel = 'XiOPlan'
    plandf.RTPlanDate = date.today().strftime('%Y%m%d')
    plandf.RTPlanTime = datetime.now().strftime('%H%M%S.%f')[:-3]
    
    plandf.StudyInstanceUID = generate_uid()
    plandf.SeriesInstanceUID = generate_uid()
    
    for drf in plandf.DoseReferenceSequence:
        drf.DoseReferenceUID = generate_uid()
    
    # Save the modified file
    plandf.save_as(dcmdir + '/' + planfile)
    
    return plandf
