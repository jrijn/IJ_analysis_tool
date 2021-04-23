from ij.plugin import ZProjector, Duplicator, HyperStackConverter, ImageCalculator
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij import IJ
from ij.gui import GenericDialog
import math

def BackgroundFilter(imp, projection_method = "Median"):

    title = imp.getTitle()

    #Make a dict containg method_name:const_fieled_value pairs for the projection methods
    methods_as_strings=['Average Intensity', 'Max Intensity', 'Min Intensity', 'Sum Slices', 'Standard Deviation', 'Median']
    methods_as_const=[ZProjector.AVG_METHOD, ZProjector.MAX_METHOD, ZProjector.MIN_METHOD, ZProjector.SUM_METHOD, ZProjector.SD_METHOD, ZProjector.MEDIAN_METHOD]
    method_dict=dict(zip(methods_as_strings, methods_as_const))

    #The Z-Projection magic happens here through a ZProjector object
    zp = ZProjector(imp)
    zp.setMethod(method_dict[projection_method])
    zp.doProjection()
    outstack = imp.createEmptyStack()
    outstack.addSlice(zp.getProjection().getProcessor())
    imp2 = ImagePlus(title+'_'+projection_method, outstack)
    out = ImageCalculator().run("Subtract create 32-bit stack", imp, imp2)
    return out


def SegmentDIC(imp, thresMethod = "RenyiEntropy"):
    IJ.run(imp, "Square", "stack")
    IJ.run(imp, "Make Binary", "method={} background=Dark calculate".format(thresMethod));   
    return imp


def main():

    imp = WindowManager.getCurrentImage()
    out = BackgroundFilter(imp)
    out.show()
    segment = SegmentDIC(out)
    segment.show()


main()