# Coded version of DICOM file 'data\1.dcm'
# Produced by pydicom codify utility script
from __future__ import unicode_literals  # Only for python2.7 and save_as unicode filename

from datetime import datetime
import os

import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid




class DicomWriter:

    def __init__(self):
        self.ds = self.generateHeader()
        self.frameNumber = 0
        self.folderName = 'data'
        self.newFolder = 'data'
        self.count = 1
        self.index = 0

    def initialize(self, folderName, idx):
        self.folderName = folderName
        if not os.path.exists(self.folderName):
            os.makedirs(self.folderName)
        self.index = idx


    def write(self, writeFolder, pixelData, primAngle, secAngle, long, lat, height, SID, SPD, FD, pxlSpacing):        ##not forget spacing!!!

        if writeFolder:
            if int(primAngle) >= 0:
                angle = 'LAO'
                angleToWrite = int(primAngle)
            else:
                angle = 'RAO'
                angleToWrite = -int(primAngle)
            if self.index == 0:
                self.newFolder = self.folderName + '/' + str(self.count) + '_' + angle + str(angleToWrite)
            if self.index == 1:
                self.newFolder = self.folderName + '/' + str(self.count) + '_' + angle + str(angleToWrite) + '_frontal'
            if self.index == 2:
                self.newFolder = self.folderName + '/' + str(self.count) + '_' + angle + str(angleToWrite) + '_lateral'

            if not os.path.exists(self.newFolder):
                os.makedirs(self.newFolder)
                #self.ds.SeriesInstanceUID = generate_uid()
                self.ds.SeriesNumber = self.count
                self.count += 1
                self.frameNumber = 0

        # File meta info data elements
        datetimeNow = datetime.now()
        #self.ds.InstanceCreationDate = datetimeNow.strftime("%Y%m%d")   #grabbing date
        #self.ds.InstanceCreationTime = datetimeNow.strftime("%H%M%S.%f")  #grabbing time

        self.ds.AcquisitionDate = datetimeNow.strftime("%Y%m%d")  # grabbing date
        self.ds.AcquisitionTime = datetimeNow.strftime("%H%M%S.%f")[:-3]  # grabbing time

        self.ds.ContentDate = datetimeNow.strftime("%Y%m%d")  # grabbing date
        self.ds.ContentTime = datetimeNow.strftime("%H%M%S.%f")[:-3]  # grabbing time

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
        #self.ds.SeriesNumber = long        # longitudinal table pos
        self.ds.AccessionNumber = str(long)  # longitudinal table pos
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
        self.ds.save_as(self.newFolder + '/' + str(self.frameNumber) + '.dcm', write_like_original=False) # "False" in order to write file signature!!!

    def generateHeader(self):
        file_meta = Dataset()
        file_meta.FileMetaInformationGroupLength = 204
        file_meta.FileMetaInformationVersion = b'\x00\x01'
        SOPClassUID = '1.2.840.10008.5.1.4.1.1.12.1'    # SOP Class Name: X-Ray Angiographic Image Storage
        file_meta.MediaStorageSOPClassUID = SOPClassUID
        SOPInstanceUID = generate_uid()
        file_meta.MediaStorageSOPInstanceUID = SOPInstanceUID

        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
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

        ds.Modality = 'XA'
        ds.Manufacturer = ''
        ds.ReferringPhysicianName = ''
        ds.PatientName = ''
        ds.PatientID = ''
        ds.PatientBirthDate = ''
        ds.PatientSex = ''
        ds.KVP = "810.0"
        ds.DistanceSourceToPatient = "810.0"  # original
        ds.DistanceSourceToDetector = "1200.0"  #own + original
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SeriesNumber = "1"
        ds.StudyID = '0'
        ds.AccessionNumber = '-760'
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
