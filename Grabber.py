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

    def grab(self):
        if not (self.initialized):
            print("grabber is not initialized!")
            return
        print("Grab image from input #", self.input)
        timeStart = time.time()
        timeLast = timeStart
        threshold = 50
        x_shift = None
        y_shift = None
        x_start = 0
        x_end = x_start + 255
        #y_start = 169
        y_start = 145 # calculating after cutting of upper 24 pixels
        y_end = y_start + 255
        y_cut = 24
        while (True):
            ret, read = self.capture.read()
            if not (ret):
                print("frame not grabbed")
            else:
                gray = cv2.cvtColor(read, cv2.COLOR_BGR2GRAY)
                indices = np.nonzero(gray > threshold)
                x_shift = indices[1][0]
                y_shift = indices[0][0]
                gray_cut = gray[y_cut:1024, (x_start + x_shift):1280]
                geometry = gray_cut[y_start:y_end, x_start:x_end]
                #geometry = gray[168:210, 0:255] #primAngle
                #cv2.imwrite('geometry.png', geometry)
                #text = pytesseract.image_to_string(geometry)
                #print(text)
                #writer.write(gray)
                #cv2.imshow('color', read)
                cv2.imshow('gray', gray_cut)
                cv2.imshow('geometry', geometry)

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