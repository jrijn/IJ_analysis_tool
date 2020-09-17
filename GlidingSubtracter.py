import ij.IJ as IJ
import ij.io.Opener as Opener
import ij.ImagePlus as ImagePlus
import ij.ImageStack as ImageStack
import ij.WindowManager as WindowManager
import ij.measure.ResultsTable as ResultsTable
import ij.measure.Measurements as Measurements
import ij.plugin.ChannelSplitter as ChannelSplitter
import ij.plugin.HyperStackConverter as HyperStackConverter
import ij.plugin.ZProjector as ZProjector
import ij.plugin.RGBStackMerge as RGBStackMerge
import ij.plugin.StackCombiner as StackCombiner
import ij.plugin.MontageMaker as MontageMaker
import ij.plugin.StackCombiner as StackCombiner
import ij.plugin.Duplicator as Duplicator
import ij.plugin.Concatenator as Concatenator
import ij.plugin.ImageCalculator as ImageCalculator
import os


def GlidingSubtracter(imp):

    name = imp.getTitle()
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()
    IJ.log("nFrames: {}".format(nFrames))

    # Catch wrong input dimensions.
    if nChannels != 1: 
        IJ.log("GlidingSubtracter only takes single channel images.")
        return None
    if nFrames <= 1:
        IJ.log("Stack has <= 1 frame. Perhaps switch Frames and Slices?")
        return None
    
    instack = imp.getImageStack()
    outstack = ImageStack()
    frame1 = instack.getProcessor(1)
    frame1 = ImagePlus("frame1", frame1)
    for i in range(1, nFrames):
        frame2 = instack.getProcessor(i)
        frame2 = ImagePlus("frame2", frame2)
        subtracted = ImageCalculator().run("subtract create 32-bit", frame1, frame2).getProcessor()
        # ImagePlus("slice", subtracted).show()
        outstack.addSlice(subtracted)

    outname = "subtract-" + name
    outstack = ImagePlus(outname, outstack)
    return outstack


def main():
    imp = WindowManager.getCurrentImage()

    # test = imp.getProcessor()
    # ImagePlus("test", test).show()
    subtracted = GlidingSubtracter(imp)
    subtracted.show()


main()