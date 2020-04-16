from ij.plugin import Duplicator, Concatenator, ChannelSplitter, RGBStackMerge, StackCombiner, MontageMaker, \
    StackCombiner, HyperStackConverter, Thresholder, ZProjector
from ij import WindowManager as wm
from ij.plugin.filter import BackgroundSubtracter, EDM
from ij import IJ, ImagePlus, ImageStack
from ij.measure import ResultsTable as ResultsTable
import math
import os


def countnuclei(imp):
    c1, c2, c3 = ChannelSplitter.split(imp)
    IJ.run(c1, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(c1, "Triangle dark")
    IJ.run(c1, "Convert to Mask", "")
    IJ.run(c1, "Dilate", "")
    IJ.run(c1, "Watershed", "")
    IJ.run(c1, "Set Measurements...", "area mean shape display label redirect=None decimal=3")
    IJ.run(c1, "Analyze Particles...", "size=0-infinity display exclude summarize add")
    return c1


def countbacteria(imp):
    c1, c2, c3 = ChannelSplitter.split(imp)
    IJ.run(c2, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(c2, "RenyiEntropy dark")
    IJ.run(c2, "Convert to Mask", "")
    IJ.run(c2, "Set Measurements...", "area mean shape display label redirect=None decimal=3")
    IJ.run(c2, "Analyze Particles...", "size=0.50-10.00 circularity=0.30-1.00 show=Overlay display exclude summarize "
                                       "add")
    return c2


def countruffles(imp):
    c1, c2, c3 = ChannelSplitter.split(imp)
    IJ.run(c3, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(c3, "RenyiEntropy dark")
    IJ.run(c3, "Convert to Mask", "")
    IJ.run(c3, "Set Measurements...", "area mean shape display label redirect=None decimal=3")
    IJ.run(c3, "Analyze Particles...", "size=1-30.00 circularity=0.20-1.00 show=Overlay display exclude summarize "
                                       "add")
    return c3


def readdirfiles(directory, nChannels=2, nSlices=1):
    """Import tiff files from a directory.
    This function reads all .tiff files from a directory and returns them as a list of hyperstacks.
    Args:
        directory: The path to a directory containing the tiff files.
        nChannels: The number of channels sequentially contained in the stack. Defaults to 2.
        nSlices: The number of slices sequentially contained in the stack. Defaults to 1.
    Returns:
        A list of hyperstacks.
    """

    dir = os.listdir(directory)
    dirfiles = []

    for file in dir:
        if file.endswith('.tif') or file.endswith('.tiff'):
            path = os.path.join(directory, file)
            stack = ImagePlus(path)
            stack = HyperStackConverter().toHyperStack(stack,
                                                       nChannels,  # channels
                                                       nSlices,  # slices
                                                       stack.getNFrames())  # frames
            dirfiles.append(stack)

    return dirfiles


def saveresults(dir, name):
    outfile = os.path.join(dir, "{}.csv".format(name))
    res = ResultsTable.getResultsTable()
    ResultsTable.save(res, outfile)
    ResultsTable.reset(res)


def main():
    indir = IJ.getDirectory("input directory")
    outdir = IJ.getDirectory(".csv output directory")
    nucdir = os.path.join(indir, "nuclei")
    bacdir = os.path.join(indir, "bacteria")
    rufdir = os.path.join(indir, "ruffles")
    if not os.path.isdir(nucdir):
        os.mkdir(nucdir)
    if not os.path.isdir(bacdir):
        os.mkdir(bacdir)
    if not os.path.isdir(rufdir):
        os.mkdir(rufdir)

    # Collect all .tif images in the input directory
    images = readdirfiles(indir,
                          nChannels=3,
                          nSlices=1)

    # Count nuclei for every image in the folder
    IJ.log("Counting nuclei...")
    for image in images:
        IJ.log(" - Current image: {}".format(image))
        # image = ZProjector.run(image, "max")
        out = countnuclei(image)
        name = image.getTitle()
        outfile = os.path.join(nucdir, "threshold_{}".format(name))
        IJ.saveAs(out, "Tiff", outfile)

    # Save the ResultsTable object
    idx = name.find("MMStack")
    condition = name[:idx]
    csvname = "nuc_{}".format(condition)
    saveresults(outdir, csvname)

    # Count bacteria for every image in the folder
    IJ.log("Counting bacteria...")
    for image in images:
        IJ.log(" - Current image: {}".format(image))
        # image = ZProjector.run(image, "max")
        out = countbacteria(image)
        name = image.getTitle()
        outfile = os.path.join(bacdir, "threshold_{}".format(name))
        IJ.saveAs(out, "Tiff", outfile)

    # Save the ResultsTable object
    csvname = "bac_{}".format(condition)
    saveresults(outdir, csvname)

    # Count ruffles for every image in the folder
    IJ.log("Counting ruffles...")
    for image in images:
        IJ.log(" - Current image: {}".format(image))
        # image = ZProjector.run(image, "max")
        out = countruffles(image)
        name = image.getTitle()
        outfile = os.path.join(rufdir, "threshold_{}".format(name))
        IJ.saveAs(out, "Tiff", outfile)

    # Save the ResultsTable object
    csvname = "ruf_{}".format(condition)
    saveresults(outdir, csvname)


main()
