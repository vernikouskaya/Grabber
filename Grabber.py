import math
import time
from datetime import datetime

import cv2
import numpy as np
import logging
from DicomWriter import DicomWriter

import os.path


filename = './logFile.log'
if os.path.isfile(filename):
    open(filename, "w").close()

logger = logging.getLogger('logFile')
hdlr = logging.FileHandler('./logFile.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARNING)

class Grabber:

    def __init__(self, input=0):
        self.input = input
        self.numFrames = 0
        self.statDelay = 100 # print statistics every '''statDelay''' frames
        self.capture = None
        self.initialized = False
        self.imageHeight = 1024
        self.imageWidth = 1280
        self.imageHeightCut = 1000  # cropped image height
        self.imageWidthCut = 1000 # cropped image width
        self.y_cut = 24 # number of upper pixels with patient name
        self.geometrySize = 256 # number of horizontal pixels with geometry info
        self.threshold = 10     # initial value greater than black
        self.fontSet = self.font = 0           #is set during convertion to binary: to MIN (or black font on the tamplate) or to MAX (or black font on the tamplate)
        self.maxXRsign = 75
        self.primAngle = 0
        self.secAngle = 0
        self.long = 0
        self.lat = 0
        self.height = 0
        self.SID = 1200
        self.FD = 15
        self.pxlSpacing = [0.110726, 0.110726]
        self.frontalORlateral = 1  # [0] - frontal, [1] - lateral
        self.cutImage = True
        self.uncutOnce = False
        self.HKL = '3'
        self.SPD = 765
        # if self.frontalORlateral == 0:
        #     self.SPD = 810  # for frontal C-arm
        # else:
        #     self.SPD = 765  # for lateral C-arm and monoplane system

    def initialize(self):
        self.select_videoPort()
        print("initializing grabber on interface #", self.input)
        self.capture = cv2.VideoCapture(self.input)
        if not(self.capture.isOpened()):
            print("Video capture can't be open")
        else:
            self.initialized = True
            inputHKL = input('in which HKL measurements are performed [3 or 4]: ')
            if inputHKL == '3' or inputHKL == '4':
                self.HKL = inputHKL
            if self.HKL == '3':
                self.SPD = 765  # for lateral C-arm and monoplane system
            else:
                self.SPD = 810  # for frontal C-arm

            print('frame capturing is initialized for HKL', self.HKL)

    def destroy(self):
        cv2.destroyAllWindows()
        self.capture.release()
        self.initialized = False

    def clip(self, image):
        x_shift = None
        y_shift = None
        x_start = 0
        x_end = x_start + self.geometrySize
        # y_start = 169
        y_start = 145  # calculating after cutting of upper 24 pixels
        y_end = y_start + self.geometrySize

        image_cut = image[self.y_cut:self.imageHeight, x_start:self.imageWidth]  #first cut upper panel with patient name
        indices = np.nonzero(image_cut > self.threshold)                         # find first non-zero pixel in x and y
        x_shift = indices[1][0]
        y_shift = indices[0][0]

        image_cut = image_cut[0:self.imageHeightCut, (x_start + x_shift):self.imageWidth]  #now cut the horizontal shift
        geometry = image_cut[y_start:y_end, x_start:x_end]
        #cv2.imwrite('geometry.png', geometry)


        x_start_XR = 62 + x_shift
        x_end_XR = 118 + x_shift

        y_start_XR = 28 - self.y_cut
        y_end_XR = 98 - self.y_cut

        live = image_cut[y_start_XR:y_end_XR, x_start_XR:x_end_XR]
        self.maxXRsign = np.amax(live) # 246 - for white, 75 - for gray
        #cv2.imwrite('XRsign.png', live)


        cv2.imshow('gray', image)
        #cv2.imshow('gray_cut', image_cut)
        #cv2.imshow('geometry', geometry)

        return image_cut, geometry

    def convertToBinary(self, geometry, row):
        min = np.amin(row)
        max = np.amax(row)
        thresh = 50 # larger than light gray and smaller than white

        if min < thresh:
            # black font on dark gray BG - > convert to: gray = 1, black = 0
            thresh, binary_image_out = cv2.threshold(row, max-5, 255, cv2.THRESH_BINARY)
            self.font = min

        else:
            # white font on light gray BG - > invert and convert to: gray = 1, white = 0
            thresh, binary_image_out = cv2.threshold(row, min, 255, cv2.THRESH_BINARY_INV)
            self.font = max

        #cv2.imshow("binary", binary_image_out)
        #cv2.imwrite('row.png', row)
        #cv2.imwrite('binary.png, binary_image_out)
        return binary_image_out

    # HKL3
    def normReco(self, number):
        if self.HKL == '3':  # HKL3
            switcher = {
                4476: 1,
                4260: 2,
                4320: 3,
                3992: 4,
                4267: 5,
                4065: 6,
                4730: 7,
                3589: 8,
                4048: 9,
                3748: 0,
                5975: -1,  # "-" #
                5380: 0,  # "+" #       ???
                6189: 0,  # empty   #
            }
        else:                   # HKL4
            switcher = {
                4939: 1,
                4497: 2,
                4483: 3,
                4417: 4,
                4454: 5,
                4290: 6,
                4892: 7,
                3851: 8,
                4245: 9,
                4080: 0,
                5975: -1,  # "-" #
                5570: 0,  # "+" #
                6189: 0,  # empty
            }
        return switcher.get(number, -999)


    def getPxlSpacing(self, FD):
        switcher = {
            15: 0.110726,
            19: 0.132902,
            20: 0.1323,
            22: 0.15631,
            25: 0.17498,
            27: 0.187775,
            31: 0.22025,
            37: 0.259644,
            42: 0.292908,
            48: 0.3795,
            }
        return switcher.get(FD, -999)

    def invalid_character(self, description, third = None, second = None, first = None):
        if first == -999 or second == -999 or third == -999:
            print("invalid character: ", description)
            self.uncutOnce = True
            logger.error('character ' + description + ' is not recognized')

            return 0

    def extract_values_from_row(self, geometry, number, yCoord):
        rect_width = 19
        rect_height = 31

        if number == 3:
            FirstRect = geometry[yCoord: yCoord + rect_height, 180:(180 + rect_width)]
            FirstRect_bin = self.convertToBinary(geometry, FirstRect)
            FirstRect_norm = int(math.ceil(cv2.norm(FirstRect_bin, normType=cv2.NORM_L2)))
            n = self.normReco(FirstRect_norm)
            #print(FirstRect_norm, " ", n)
        SecRect = geometry[yCoord: yCoord + rect_height, 200:(200 + rect_width)]
        SecRect_bin = self.convertToBinary(geometry, SecRect)
        SecRect_norm = int(math.ceil(cv2.norm(SecRect_bin, normType=cv2.NORM_L2)))
        m = self.normReco(SecRect_norm)
        #print(SecRect_norm, " ", m)
        ThirdRect = geometry[yCoord: yCoord + rect_height, 220:(220 + rect_width)]
        ThirdRect_bin = self.convertToBinary(geometry, ThirdRect)
        ThirdRect_norm = int(math.ceil(cv2.norm(ThirdRect_bin, normType=cv2.NORM_L2)))
        p = self.normReco(ThirdRect_norm)
        #print(ThirdRect_norm, " ", p)


        #geometry_new = geometry
        #geometry_new = np.copy(geometry)
        #geometry_new = cv2.rectangle(geometry_new, (180, yCoord), (180 + rect_width, yCoord + rect_height), (255, 0, 0), 1)
        #geometry_new = cv2.rectangle(geometry_new, (220, yCoord), (220 + rect_width, yCoord + rect_height), (255, 0, 0), 1)
        #geometry_new = cv2.rectangle(geometry_new, (200, yCoord), (200 + rect_width, yCoord + rect_height), (255, 0, 0), 1)
        #cv2.imshow("Row" + str(yCoord), geometry_new)
        #cv2.imwrite('geometryWithTemplate.png', geometry_new)

        if number == 3:
            return n, m, p
        else:
            return m, p

    def recognize_characters(self, geometry, firstRowFirst, firstRowSec, firstRowThird, secondRowFirst, secondRowSec, secondRowThird,thirdRowFirst, thirdRowSec, thirdRowThird, forthRowFirst, forthRowSec, forthRowThird, fifthRowSec, fifthRowThird):

        # some points for differentiation within geometry template
        # this is working in HKL4, but not HKL3
        #degreeSign = (243, 9)  # angulation or table position
        #LAORAO = (12, 11)  # LAO or RAO
        #CAUDCRAN = (24, 61)  # CAUD or CRAN
        # this is working in both
        degreeSign = (244, 9)  # angulation or table position
        LAORAO = (14, 11)  # LAO or RAO
        CAUDCRAN = (25, 61)  # CAUD or CRAN

        if geometry[degreeSign[1], degreeSign[0]] == self.fontSet:  # angulation
            # primary angulation
            if self.invalid_character('primAngle', firstRowThird, firstRowSec):
                self.primAngle = -999
            if geometry[LAORAO[1], LAORAO[0]] == self.fontSet:  # RAO
                self.primAngle = -(firstRowSec * 10 + firstRowThird)
            else:
                self.primAngle = firstRowSec * 10 + firstRowThird  # LAO
            # secondary angulation
            if self.invalid_character('secAngle', secondRowThird, secondRowSec):
                self.secAngle = -999
            if geometry[CAUDCRAN[1], CAUDCRAN[0]] == self.fontSet:  # KRAN
                self.secAngle = secondRowSec * 10 + secondRowThird
            else:
                self.secAngle = -(secondRowSec * 10 + secondRowThird)  # CAUD

        else:
            if self.invalid_character('longTable', firstRowThird, firstRowSec, firstRowFirst):
                self.long = -999
            if firstRowFirst == 0:
                if firstRowSec >= 0:
                    self.long = firstRowSec * 10 + firstRowThird
                else:
                    self.long = -firstRowThird
            else:
                self.long = -(firstRowSec * 10 + firstRowThird)
            self.long = 10 * self.long
            # elif firstRowSec == -1:  # table
            #     self.long = -firstRowThird
            # else:
            #     self.long = -(firstRowSec * 10 + firstRowThird)
            # self.long = 10 * self.long
            if self.invalid_character('latTable', secondRowThird, secondRowSec, secondRowFirst):
                self.lat = -999
            if secondRowFirst == 0:
                if secondRowSec >= 0:
                    self.lat = secondRowSec * 10 + secondRowThird
                else:
                    self.lat = -secondRowThird
            else:
                self.lat = -(secondRowSec * 10 + secondRowThird)
            self.lat = 10 * self.lat
        #print("primAngle = ", primAngle)
        #print("longTable", long)
        #print("secAngle = ", secAngle)
        #print("latTable", lat)

        if self.invalid_character('height', thirdRowThird, thirdRowSec, thirdRowFirst):
            self.height = -999
        elif thirdRowFirst >= 0:
            if thirdRowSec >= 0:
                self.height = thirdRowSec * 10 + thirdRowThird
            else:
                self.height = -thirdRowThird
        else:
             self.height = -(thirdRowSec * 10 + thirdRowThird)
        self.height = 10 * self.height
        #print("heightTable = ", height)

        if self.invalid_character('SID', forthRowThird, forthRowSec, forthRowFirst):
            self.SID = -999
        self.SID = forthRowFirst * 100 + forthRowSec * 10 + forthRowThird
        self.SID = 10 * self.SID
        if self.invalid_character('FD', fifthRowThird, fifthRowSec):
            self.FD = -999
        self.FD = fifthRowSec * 10 + fifthRowThird
        #print("SID = ", SID)
        #print("FD = ", FD)

        spacing = self.getPxlSpacing(self.FD)
        if self.invalid_character(spacing):
            self.pxlSpacing[0] = self.pxlSpacing[1] = -999
        else:
            self.pxlSpacing[0] = self.pxlSpacing[1] = spacing
            #print("pxlSpacing = ", pxlSpacing)

        return

    def grab(self):

        XRsign_now = False
        XRsign_prev = False
        gray_DICOM_now = np.zeros((1000, 1000)) # for cut image

        if not (self.initialized):
            print("grabber is not initialized!")
            return
        print("Grab image from input #", self.input)
        print("geometry is cut away when storing images, please press 'c' within the image window to store whole images")
        #print("geometry is cut away when storing images")
        timeStart = time.time()
        timeLast = timeStart

        while (True):
            ret, read = self.capture.read()
            if not (ret):
                print("frame not grabbed")
            else:
                gray = cv2.cvtColor(read, cv2.COLOR_BGR2GRAY)
                gray_cut, geometry = self.clip(gray)

                init_template = 10
                template_shift = 49

                # geometry_new = np.copy(geometry)
                # geometry_new = cv2.circle(geometry_new, (243, 9), 1, [255, 0, 0], -1)
                # cv2.imwrite("LAOTable.png", geometry_new)

                firstRowFirst, firstRowSec, firstRowThird = self.extract_values_from_row(geometry, 3, init_template)                     # (LAO/RAO)
                self.fontSet = self.font
                secondRowFirst, secondRowSec, secondRowThird = self.extract_values_from_row(geometry, 3, init_template + template_shift)  # (KAUD/CRAN)
                thirdRowFirst, thirdRowSec, thirdRowThird = self.extract_values_from_row(geometry, 3, init_template + 2*template_shift)  # (TableHigh)
                forthRowFirst, forthRowSec, forthRowThird = self.extract_values_from_row(geometry, 3, init_template + 3*template_shift)  # (SID)
                fifthRowSec, fifthRowThird = self.extract_values_from_row(geometry, 2, init_template + 4*template_shift)  # (FD)

                # distinguish and calculate geometry parameters
                self.recognize_characters(geometry, firstRowFirst, firstRowSec, firstRowThird, secondRowFirst, secondRowSec, secondRowThird,thirdRowFirst, thirdRowSec, thirdRowThird, forthRowFirst, forthRowSec, forthRowThird, fifthRowSec, fifthRowThird)

                if self.maxXRsign >= 200:
                    XRsign_now = True
                    if XRsign_now and XRsign_prev == False:
                        writeNewFolder = True
                    else:
                        writeNewFolder = False

                    if self.cutImage:
                        if not self.uncutOnce:
                            gray_DICOM = gray_cut[0:self.imageHeightCut, self.geometrySize:(self.geometrySize + self.imageWidthCut)] # cut geometry panel before saving
                        else:
                            gray_DICOM = gray_cut
                            self.uncutOnce = False

                    else:
                        gray_DICOM = gray_cut
                    # timeBefore = time.time()

                    # if not self.compare_images(gray_DICOM_now, gray_DICOM):
                    #     gray_DICOM_now = gray_DICOM
                    #     writer.write(writeNewFolder, np.ascontiguousarray(gray_DICOM_now), str(self.primAngle),
                    #                  str(self.secAngle), self.long, self.lat, self.height, str(self.SID), self.SPD,
                    #                  str(self.FD), self.pxlSpacing)
                    # else:
                    #     gray_DICOM_now = gray_DICOM_now
                    #timeAfter = time.time()
                    #print('comparison_time: ', timeAfter - timeBefore) #takes 10 to 15ms
                    writer.write(writeNewFolder, np.ascontiguousarray(gray_DICOM), str(self.primAngle),
                                 str(self.secAngle), self.long, self.lat, self.height, str(self.SID), self.SPD,
                                 str(self.FD), self.pxlSpacing)
                else:
                    XRsign_now = False

                XRsign_prev = XRsign_now

                self.numFrames += 1

            if (self.numFrames % self.statDelay == 0):
                timeNow = time.time()
                timeDiff = timeNow - timeLast
                timeLast = timeNow
                print("FPS: ", self.statDelay/timeDiff)
            key = cv2.waitKey(1)
            if (key == ord('q')):
                break
            if (key == ord('c')):
                self.cutImage = not self.cutImage
                print("switched image clipping mode to ", self.cutImage)
        timeEnd = time.time()
        timeDiff = timeEnd - timeStart
        print("total time: ", timeDiff)
        print("total frames: ", self.numFrames)
        print("average FPS: ", self.numFrames / timeDiff)

    def mse(self, imageA, imageB):
        # the 'Mean Squared Error' between the two images is the
        # sum of the squared difference between the two images;
        # NOTE: the two images must have the same dimension
        if imageA.shape[0] > 0 & imageA.shape[0] == imageB.shape[0] & imageA.shape[1] > 0 & imageA.shape[1] == imageB.shape[1]:
            err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
            err /= float(imageA.shape[0] * imageA.shape[1])
            # return the MSE, the lower the error, the more "similar"
            # the two images are
        else:
            # two images have diff dimensions, return high mse value
            err = 1

        return err


    def compare_images(self, imageA, imageB):
        # compute the mean squared error and structural similarity
        # index for the images
        m = self.mse(imageA, imageB)
        if m == 0.0:
            return 1
        else:
            return 0
        # If image is identical to itself, MSE = 0.0 and SSIM = 1.0.
        # if MSE increases the images are less similar, as opposed to the SSIM where smaller values indicate less similarity

    def select_videoPort(self):
        index = 0
        cap = cv2.VideoCapture(index)
        if not (cap.isOpened()):
            print("Video capture can't be open")
            return
        while True:
            _, frame = cap.read()
            cv2.imshow('frame', frame)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('n'):
                cap.release()
                index += 1
                cap = cv2.VideoCapture(index)
                if not (cap.isOpened()):
                    print("Video capture can't be open")
            if key & 0xFF == ord('y'):
                self.input = index
                cap.release()
                break

if __name__ == '__main__':
    folder = datetime.now().strftime("%Y%m%d_%H%M%S")
    writer = DicomWriter()
    writer.initialize(folder)
    grabber = Grabber(input=0)
    grabber.initialize()
    grabber.grab()