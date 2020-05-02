import math
import time
from datetime import datetime

import cv2
import numpy as np

from DicomWriter import DicomWriter


class Grabber:

    def __init__(self, input=0):
        self.input = input
        self.numFrames = 0
        self.statDelay = 50 # print statistics every '''statDelay''' frames
        self.capture = None
        self.initialized = False
        self.imageHeight = 1024
        self.imageWidth = 1280
        self.geometrySize = 255
        self.threshold = 10     # initial value greater than black
        self.fontSet = self.font = 0           #is set during convertion to binary: to MIN (or black font on the tamplate) or to MAX (or black font on the tamplate)

    def initialize(self):
        print("initializing grabber on interface #", self.input)
        self.capture = cv2.VideoCapture(self.input)
        if not(self.capture.isOpened()):
            print("Video capture can't be open")
        else:
            self.initialized = True

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
        y_cut = 24

        image_cut = image[y_cut:self.imageHeight, x_start:self.imageWidth]  #first cut upper panel with patient name
        indices = np.nonzero(image_cut > self.threshold)                         # find first non-zero pixel in x and y
        x_shift = indices[1][0]
        y_shift = indices[0][0]

        image_cut = image_cut[0:self.imageHeight, (x_start + x_shift):self.imageWidth]  #now cut the horizontal shift
        geometry = image_cut[y_start:y_end, x_start:x_end]
        #cv2.imwrite('geometry.png', geometry)

        #cv2.imshow('gray', image)
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

    def normReco(self, number):
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
            6189: 0,   # empty
            }
        return switcher.get(number, -999)

    def pxlSpacing(self, FD):
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

    def invalid_character(self, third = None, second = None, first = None):
        if first == -999 or second == -999 or third == -999:
            print("invalid character")
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

    def recognize_characters(self, geometry, firstRowSec, firstRowThird, secondRowFirst, secondRowSec, secondRowThird,thirdRowFirst, thirdRowSec, thirdRowThird, forthRowFirst, forthRowSec, forthRowThird, fifthRowSec, fifthRowThird):

        # some points for differentiation within geometry template
        degreeSign = (243, 9)  # angulation or table position
        LAORAO = (12, 11)  # LAO or RAO
        CAUDCRAN = (24, 61)  # CAUD or CRAN
        primAngle = 0
        secAngle = 0
        long = 0
        lat = 0
        height = 0
        SID = 0
        FD = 0
        pxlSpacing = [0.110726, 0.110726]
        #pxlSpacing = 0.110726

        if geometry[degreeSign[1], degreeSign[0]] == self.fontSet:  # angulation
            # primary angulation
            if geometry[LAORAO[1], LAORAO[0]] == self.fontSet:  # RAO
                primAngle = -(firstRowSec * 10 + firstRowThird)
            else:
                primAngle = firstRowSec * 10 + firstRowThird  # LAO
            # secondary angulation
            if geometry[CAUDCRAN[1], CAUDCRAN[0]] == self.fontSet:  # KRAN
                secAngle = secondRowSec * 10 + secondRowThird
            else:
                secAngle = -(secondRowSec * 10 + secondRowThird)  # CAUD

        else:
            if self.invalid_character(firstRowThird, firstRowSec):
                long = -999
            elif firstRowSec == -1:  # table
                long = -firstRowThird
            else:
                long = -(firstRowSec * 10 + firstRowThird)
            long = 10 * long
            if self.invalid_character(secondRowThird, secondRowSec, secondRowFirst):
                lat = -999
            if secondRowFirst == 0:
                if secondRowSec >= 0:
                    lat = secondRowThird
                else:
                    lat = -secondRowThird
            else:
                if secondRowFirst >= 0:
                    lat = secondRowSec * 10 + secondRowThird
                else:
                    lat = -(secondRowSec * 10 + secondRowThird)
            lat = 10 * lat
        #print("primAngle = ", primAngle)
        #print("longTable", long)
        #print("secAngle = ", secAngle)
        #print("latTable", lat)

        if self.invalid_character(thirdRowThird, thirdRowSec, thirdRowFirst):
            height = -999
        elif thirdRowFirst >= 0:
            if thirdRowSec >= 0:
                height = thirdRowSec * 10 + thirdRowThird
            else:
                height = -thirdRowThird
        else:
             height = -(thirdRowSec * 10 + thirdRowThird)
        height = 10 * height
        #print("heightTable = ", height)

        SID = forthRowFirst * 100 + forthRowSec * 10 + forthRowThird
        SID = 10 * SID
        FD = fifthRowSec * 10 + fifthRowThird
        #print("SID = ", SID)
        #print("FD = ", FD)

        spacing = self.pxlSpacing(FD)
        if self.invalid_character(spacing):
            pxlSpacing[0] = pxlSpacing[1] = -999
        else:
            pxlSpacing[0] = pxlSpacing[1] = spacing
            #print("pxlSpacing = ", pxlSpacing)

        return primAngle, secAngle, long, lat, height, SID, FD, pxlSpacing

    def grab(self):
        if not (self.initialized):
            print("grabber is not initialized!")
            return
        print("Grab image from input #", self.input)
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

                firstRowSec, firstRowThird = self.extract_values_from_row(geometry, 2, init_template)                     # (LAO/RAO)
                self.fontSet = self.font
                secondRowFirst, secondRowSec, secondRowThird = self.extract_values_from_row(geometry, 3, init_template + template_shift)  # (KAUD/CRAN)
                thirdRowFirst, thirdRowSec, thirdRowThird = self.extract_values_from_row(geometry, 3, init_template + 2*template_shift)  # (TableHigh)
                forthRowFirst, forthRowSec, forthRowThird = self.extract_values_from_row(geometry, 3, init_template + 3*template_shift)  # (SID)
                fifthRowSec, fifthRowThird = self.extract_values_from_row(geometry, 2, init_template + 4*template_shift)  # (FD)

                # distinguish and calculate geometry parameters
                primAngle, secAngle, long, lat, height, SID, FD, pxlSpacing = self.recognize_characters(geometry, firstRowSec, firstRowThird, secondRowFirst, secondRowSec, secondRowThird,thirdRowFirst, thirdRowSec, thirdRowThird, forthRowFirst, forthRowSec, forthRowThird, fifthRowSec, fifthRowThird)

                frontalORlateral = 0 # [0] - frontal, [1] - lateral
                if frontalORlateral == 0:
                    SPD = 810   # for frontal C-arm
                else:
                    SPD = 765   # for lateral C-arm and monoplane system

                #self.compare_images(gray_cut, gray_cut)
                writer.write(np.ascontiguousarray(gray_cut), str(primAngle), str(secAngle), long, lat, height, str(SID), SPD, str(FD), pxlSpacing)
                self.numFrames += 1

            if (self.numFrames % self.statDelay == 0):
                timeNow = time.time()
                timeDiff = timeNow - timeLast
                timeLast = timeNow
                print("FPS: ", self.statDelay/timeDiff)
            key = cv2.waitKey(1)
            if (key == ord('q')):
                break

        timeEnd = time.time()
        timeDiff = timeEnd - timeStart
        print("total time: ", timeDiff)
        print("total frames: ", self.numFrames)
        print("average FPS: ", self.numFrames / timeDiff)

    def mse(self, imageA, imageB):
        # the 'Mean Squared Error' between the two images is the
        # sum of the squared difference between the two images;
        # NOTE: the two images must have the same dimension
        #if imageA.rows > 0 & imageA.rows == imageB.rows & imageA.cols > 0 & imageA.cols == imageB.cols:
            err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
            err /= float(imageA.shape[0] * imageA.shape[1])
            # return the MSE, the lower the error, the more "similar"
            # the two images are
            return err
        #else:
            # two images have diff dimensions
            #return 10000.0  #return a bad value

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


if __name__ == '__main__':
    folder = datetime.now().strftime("%Y%m%d_%H%M%S")
    writer = DicomWriter()
    writer.initialize(folder)
    grabber = Grabber(input=0)
    grabber.initialize()
    grabber.grab()