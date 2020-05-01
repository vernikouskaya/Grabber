# Coded version of DICOM file 'data\1.dcm'
# Produced by pydicom codify utility script
from __future__ import unicode_literals  # Only for python2.7 and save_as unicode filename

from datetime import datetime
import os

import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid
from pydicom.tag import Tag

#https://github.com/ivmartel/dwv/wiki/Error-Messages
#####gdcmconv - -raw - i { in -dcm_file_path} -o {out - dcm_file_path}

class DicomWriter:

    def __init__(self):
        self.ds = self.generateHeader()
        self.frameNumber = 0
        self.folderName = 'data'

    def initialize(self, folderName):
        self.folderName = folderName
        if not os.path.exists(self.folderName):
            os.makedirs(self.folderName)

    def write(self, pixelData, primAngle, secAngle, long, lat, height, SID, SPD, FD, pxlSpacing):        ##not forget spacing!!!
        # File meta info data elements
        datetimeNow = datetime.now()
        self.ds.InstanceCreationDate = datetimeNow.strftime("%Y%m%d")   #grabbing date
        self.ds.InstanceCreationTime = datetimeNow.strftime("%H%M%S")  #grabbing time

        self.ds.SeriesInstanceUID = generate_uid()

        # primary angulation
        self.ds.StudyDate = primAngle                 #demonstrator
        self.ds.PositionerPrimaryAngle = primAngle     #original
        # secondary angulation
        self.ds.StudyTime = secAngle                     #demonstrator
        self.ds.PositionerSecondaryAngle = secAngle    #original

        # distance source to patient
        self.ds.KVP = SPD                       #demonstrator
        self.ds.DistanceSourceToPatient = SPD   #original
        # distance source to detector
        self.ds.DistanceSourceToDetector = SID  # original + demonstrator

        # table position demonstrator
        self.ds.StudyID = str(height)               # vertical table pos
        self.ds.SeriesNumber = long        # longitudinal table pos
        self.ds.AcquisitionNumber = lat   # lateral table pos

        # table position original
        tableSeq = Sequence()
        self.ds.add_new([0x2003, 0x102E], 'SQ', tableSeq)  # original
        tableDataSet = Dataset()
        tableDataSet.add_new([0x300A, 0x0128], 'DS', height)   # vertical table pos
        tableDataSet.add_new([0x300A, 0x0129], 'DS', long)   # longitudinal table pos
        tableDataSet.add_new([0x300A, 0x012A], 'DS', lat)  # lateral table pos
        tableSeq.append(tableDataSet)

        # field distance
        self.ds.PositionReferenceIndicator = FD               #demonstrator
        FDstr = "FD " + FD + " cm"
        self.ds.add_new([0x2003, 0x1003], 'LO', FDstr)     # original
        self.ds.add_new([0x2003, 0x1010], 'LO', FDstr)     #original

        # pixel spacing
        self.ds.PixelSpacing = pxlSpacing        # demonstrator
        self.ds.ImagerPixelSpacing = pxlSpacing   # original

        self.ds.Rows = pixelData.shape[0]                 #image height
        self.ds.Columns = pixelData.shape[1]               #image width

        self.ds.PixelData = pixelData
        self.frameNumber += 1
        self.ds.InstanceNumber = str(self.frameNumber)
        self.ds.save_as(self.folderName + '/' + str(self.frameNumber) + '.dcm', write_like_original=False) # "False" in order to write file signature!!!

    def generateHeader(self):
        file_meta = Dataset()
        file_meta.FileMetaInformationGroupLength = 204
        file_meta.FileMetaInformationVersion = b'\x00\x01'
        #file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        SOPClassUID = generate_uid()
        file_meta.MediaStorageSOPClassUID = SOPClassUID
        #file_meta.MediaStorageSOPInstanceUID = '2.25.64478777239060462373300680991826309705' #actually (prefix=None) in 2.25
        SOPInstanceUID = generate_uid()
        file_meta.MediaStorageSOPInstanceUID = SOPInstanceUID

        #file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        #file_meta.ImplementationClassUID = '2.25.190146791043182537444806132342625375407'
        file_meta.ImplementationClassUID = generate_uid()
        #file_meta.ImplementationVersionName = 'VTK_DICOM_0_8_6'
        # Main data elements
        ds = Dataset()
        ds.ImageType = ['DERIVED', 'SECONDARY', 'OTHER']
        ds.InstanceCreationDate = '20180831'
        ds.InstanceCreationTime = '162416.733400'
        ds.SOPClassUID = SOPClassUID
        ds.SOPInstanceUID = SOPInstanceUID
        # primary angulation
        ds.StudyDate = '0'
        ds.PositionerPrimaryAngle = "0.0"
        # secondary angulation
        ds.StudyTime = '0'
        ds.PositionerSecondaryAngle = "0.0"
        ds.StudyInstanceUID = generate_uid()
        ds.AccessionNumber = ''
        ds.Modality = 'XA'
        ds.Manufacturer = ''
        ds.ReferringPhysicianName = ''
        ds.PatientName = ''
        ds.PatientID = ''
        ds.PatientBirthDate = ''
        ds.PatientSex = ''
        ds.KVP = "810.0"
        ds.DistanceSourceToPatient = "765.0"  # original
        ds.DistanceSourceToDetector = "1200.0"  #own + original

        ds.StudyID = '60'
        ds.SeriesNumber = "-760"
        ds.AcquisitionNumber = "-110"
        #ds.InstanceNumber = "1"
        #ds.ImagePositionPatient = [0, 113.272698, 0]
        #ds.ImageOrientationPatient = [1, 0, 0, 0, -1, 0]
        # ds.FrameOfReferenceUID = '2.25.248301001933451919654598313426997389484'
        ds.PositionReferenceIndicator = '15'
        #ds.SliceLocation = "0.0"
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = 'MONOCHROME2'
        ds.Rows = 1024
        ds.Columns = 1280
        # pixel spacing
        ds.PixelSpacing = [0.110726, 0.110726]          #demonstrator
        ds.ImagerPixelSpacing = [0.110726, 0.110726]    # original
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.SmallestImagePixelValue = 0
        ds.LargestImagePixelValue = 255
        ds.SmallestPixelValueInSeries = 0
        ds.LargestPixelValueInSeries = 255
        ds.RescaleIntercept = "0.0"
        ds.RescaleSlope = "1.0"
        ds.file_meta = file_meta
        ds.is_implicit_VR = False
        ds.is_little_endian = True

        return ds
