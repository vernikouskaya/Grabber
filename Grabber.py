import time
from datetime import datetime

import cv2
import numpy as np

from DicomWriter import DicomWriter


class Grabber:

    def __init__(self, input=0):
        self.input = input
        self.numFrames = 0
        self.statDelay = 30 # print statistics every '''statDelay''' frames
        self.capture = None
        self.initialized = False
        self.imageHeight = 1024
        self.imageWidth = 1280
        self.geometrySize = 255

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
        threshold = 10
        x_shift = None
        y_shift = None
        x_start = 0
        x_end = x_start + self.geometrySize
        # y_start = 169
        y_start = 145  # calculating after cutting of upper 24 pixels
        y_end = y_start + self.geometrySize
        y_cut = 24

        image_cutY = image[y_cut:self.imageHeight, x_start:self.imageWidth]
        indices = np.nonzero(image_cutY > threshold)
        x_shift = indices[1][0]
        y_shift = indices[0][0]

        image_cut = image[y_cut:self.imageHeight, (x_start + x_shift):self.imageWidth]
        geometry = image_cut[y_start:y_end, x_start:x_end]
        #cv2.imwrite('geometry.png', geometry)

        #cv2.imshow('gray', image)
        #cv2.imshow('gray_cut', image_cut)
        #cv2.imshow('geometry', geometry)

        return image_cut, geometry

    def convertToBinary(self, geometry, row):
        min = np.amin(row)
        max = np.amax(row)
        threshold = 115 # larger than light gray and smaller than white

        if max < threshold:
            thresh, binary_image_out = cv2.threshold(row, max-1, 255, cv2.THRESH_BINARY)
            #binary_image_out = np.invert(binary_image)

        else:
            thresh, binary_image = cv2.threshold(row, max-1, 255, cv2.THRESH_BINARY)
            binary_image_out = np.invert(binary_image)


        #cv2.imshow("binary", binary_image_out)
        return binary_image_out


    def extract_values_from_row(self, geometry, number, yCoord):
        rect_width = 19
        rect_height = 31
        if number == 3:
            FirstRect = geometry[yCoord: yCoord + rect_height, 180:(180 + rect_width)]
            FirstRect = self.convertToBinary(geometry, FirstRect)
        SecRect = geometry[yCoord: yCoord + rect_height, 200:(200 + rect_width)]
        SecRect = self.convertToBinary(geometry, SecRect)
        ThirdRect = geometry[yCoord: yCoord + rect_height, 220:(220 + rect_width)]
        ThirdRect = self.convertToBinary(geometry, ThirdRect)

        #cv2.imshow('LAO', LAORAO_ThirdRect)
        #geometry_new = geometry
        #geometry_new = np.copy(geometry)
        #geometry_new = cv2.rectangle(geometry_new, (180, yCoord), (180 + rect_width, yCoord + rect_height), (255, 0, 0), 1)
        #geometry_new = cv2.rectangle(geometry_new, (220, yCoord), (220 + rect_width, yCoord + rect_height), (255, 0, 0), 1)
        #geometry_new = cv2.rectangle(geometry_new, (200, yCoord), (200 + rect_width, yCoord + rect_height), (255, 0, 0), 1)
        #cv2.imshow("Row" + str(yCoord), geometry_new)
        #cv2.imwrite('geometryWithTemplate.png', geometry_new)


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
                self.extract_values_from_row(geometry, 2, init_template)  # first row (LAO/RAO)
                self.extract_values_from_row(geometry, 3, init_template + template_shift)  # first row (KAUD/CRAN)
                self.extract_values_from_row(geometry, 3, init_template + 2*template_shift)  # first row (KAUD/CRAN)
                self.extract_values_from_row(geometry, 3, init_template + 3*template_shift)  # first row (TableHigh)
                self.extract_values_from_row(geometry, 2, init_template + 4*template_shift)  # first row (FD)

                writer.write(np.ascontiguousarray(gray_cut))
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

if __name__ == '__main__':
    folder = datetime.now().strftime("%Y%m%d_%H%M%S")
    writer = DicomWriter()
    writer.initialize(folder)
    grabber = Grabber(input=0)
    grabber.initialize()
    grabber.grab()