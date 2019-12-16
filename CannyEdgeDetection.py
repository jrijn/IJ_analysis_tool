# This Imagej script requires that the plugin "Canny_Edge_Detector" is installed!
# This plugin is available at: http://www.tomgibara.com/computer-vision/canny-edge-detector

from ij import IJ, ImagePlus, ImageStack, WindowManager
from ij.plugin import Duplicator
import Canny_Edge_Detector
import traceback


# Declare variables

# Declare functions

def stackcannyedge(stack):
    return


def readdir():
    return


def main():
    imp = WindowManager.getCurrentImage()
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()

    canny_stack = ImageStack()
    for i in range(nFrames):
        slice = Duplicator().run(imp,
                                 1,  # firstC
                                 1,  # lastC
                                 1,  # firstZ
                                 1,  # lastZ
                                 i,  # firstT
                                 i)  # lastT
        proc = i / nFrames
        IJ.log("Processing slice {}/{}...".format(i, nFrames))
        canny_slice = _singleCanny(slice)
        ip = canny_slice.getProcessor()
        canny_stack.addSlice(ip)

    canny_stack = ImagePlus("canny_stack", canny_stack)
    canny_stack.show()
    IJ.log("Canny edge detection finished.")

    return


def _singleCanny(imp):
    # imp = WindowManager.getCurrentImage()

    # Initiate canny edges detector plugin
    detector = Canny_Edge_Detector()

    # adjust its parameters as desired
    detector.setLowThreshold(2.5)
    detector.setHighThreshold(7.5)
    detector.setGaussianKernelWidth(16)
    detector.setGaussianKernelRadius(2)
    detector.setContrastNormalized(False)

    # apply it to an image
    # detector.setSourceImage(frame)
    canny = detector.process(imp)

    return canny


# Run main
try:
    imp = WindowManager.getCurrentImage()
    main()
    # out = _singleCanny(imp)
    # out.show()
except Exception:
    IJ.log("main() returned an error.")
    traceback.print_exc()
