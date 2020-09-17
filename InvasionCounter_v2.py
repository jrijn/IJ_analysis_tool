import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
import ij.measure.ResultsTable as ResultsTable
import ij.measure.Measurements as Measurements
import ij.io.Opener as Opener
import ij.plugin.ChannelSplitter as ChannelSplitter
import ij.plugin.HyperStackConverter as HyperStackConverter
import ij.plugin.ZProjector as ZProjector
import ij.plugin.filter.ParticleAnalyzer as ParticleAnalyzer

import os
import math


def readdirfiles(directory):
    """Import tiff files from a directory.
    This function reads all .tiff files from a directory and it's subdirectories and returns them as a list of
    hyperstacks.

    Args:
        directory: The path to a directory containing the tiff files.

    Returns:
        A list of filepaths.
    """
    # Get the list of all files in directory tree at given path
    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(directory):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    return listOfFiles


def saveresults(dir, name):
    outfile = os.path.join(dir, "{}.csv".format(name))
    
    res = ResultsTable.getResultsTable()
    ResultsTable.save(res, outfile)
    ResultsTable.reset(res)


def stackprocessor(path, nChannels=4, nSlices=1, nFrames=1):
    imp = ImagePlus(path)
    imp = HyperStackConverter().toHyperStack(imp,
                                               nChannels,  # channels
                                               nSlices,  # slices
                                               nFrames)  # frames
    imp = ZProjector.run(imp, "max")
    return imp


def countobjects(imp, rt,
                 subtractBackground=False, watershed=False, dilate=False,
                 threshMethod="Otsu", physicalUnits=True,
                 minSize=0.00, maxSize=float("inf"),
                 minCirc=0.00, maxCirc=1.00):
    """Threshold and count objects in channel 'channelNumber'.
        This function splits an image in the separate channels, and counts the number of objects in the thresholded
        channel.

        Args:
            imp: An ImagePlus with 1 frame, 1 slice.

        Returns:
            A list of filepaths.
        """
    cal = imp.getCalibration()

    if subtractBackground:
        IJ.run(imp, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(imp, "{} dark".format(threshMethod))
    IJ.run(imp, "Convert to Mask", "")
    if dilate:
        IJ.run(imp, "Dilate", "")
    if watershed:
        IJ.run(imp, "Watershed", "")
    if physicalUnits: # Convert physical units to pixels for the current calibration.
        minSize = cal.getRawX(math.sqrt(minSize)) ** 2
        maxSize = cal.getRawX(math.sqrt(maxSize)) ** 2

    pa = ParticleAnalyzer(
            ParticleAnalyzer.SHOW_OVERLAY_OUTLINES|ParticleAnalyzer.DISPLAY_SUMMARY, #int options
            Measurements.AREA|Measurements.SHAPE_DESCRIPTORS|Measurements.MEAN|Measurements.CENTROID|Measurements.LABELS, #int measurements
            rt, #ResultsTable
            minSize, #double
            maxSize, #double
            minCirc, #double
            maxCirc) #double
    pa.analyze(imp)
    return imp


def main():
    # Prepare directory tree for output.
    indir = IJ.getDirectory("input directory")
    outdir = IJ.getDirectory(".csv output directory")
    c1dir = os.path.join(outdir, "Channel1")
    c2dir = os.path.join(outdir, "Channel2")
    c3dir = os.path.join(outdir, "Channel3")
    c4dir = os.path.join(outdir, "Channel4")
    channelsdir = os.path.join(outdir, "Channels")
    if not os.path.isdir(c1dir):
        os.mkdir(c1dir)
    if not os.path.isdir(c2dir):
        os.mkdir(c2dir)
    if not os.path.isdir(c3dir):
        os.mkdir(c3dir)
    if not os.path.isdir(c4dir):
        os.mkdir(c4dir)
    if not os.path.isdir(channelsdir):
        os.mkdir(channelsdir)

    # Collect all file paths in the input directory
    files = readdirfiles(indir)

    # Initialize the results tables.
    c1Results = ResultsTable()
    c2Results = ResultsTable()
    c3Results = ResultsTable()
    c4Results = ResultsTable()

    for file in files:

        IJ.log("File: {}/{}".format(files.index(file)+1, len(files)))

        if file.endswith('.tif'):

            # Open .tiff file as ImagePlus.
            imp = stackprocessor(file,
                                   nChannels=4,
                                   nSlices=7,
                                   nFrames=1)
            channels = ChannelSplitter.split(imp)
            name = imp.getTitle()
            
            # For every channel, save the inverted channel in grayscale as .jpg.
            for channel in channels:
                IJ.run(channel, "Grays", "")
                IJ.run(channel, "Invert", "")
                jpgname = channel.getShortTitle()
                jpgoutfile = os.path.join(channelsdir, "{}.jpg".format(jpgname))
                IJ.saveAs(channel.flatten(), "Jpeg", jpgoutfile)
                IJ.run(channel, "Invert", "")

            # Settings for channel1 threshold.
            c1 = countobjects(channels[0], c1Results,
                               threshMethod="Triangle",
                               subtractBackground=True,
                               watershed=True,
                               minSize=0.00,
                               maxSize=100,
                               minCirc=0.00,
                               maxCirc=1.00)

            # Settings for channel2 threshold.
            c2 = countobjects(channels[1], c2Results,
                               threshMethod="RenyiEntropy",
                               subtractBackground=False,
                               watershed=False,
                               minSize=0.00,
                               maxSize=30.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            # Settings for channel3 threshold.
            c3 = countobjects(channels[2], c3Results,
                               threshMethod="RenyiEntropy",
                               subtractBackground=False,
                               watershed=False,
                               minSize=0.00,
                               maxSize=30.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            # Settings for channel4 threshold.
            c4 = countobjects(channels[3], c4Results,
                               threshMethod="RenyiEntropy",
                               subtractBackground=True,
                               watershed=False,
                               minSize=0.20,
                               maxSize=100.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            # Format filenames for thresholded .tiff files.
            outfileC1 = os.path.join(c1dir, "threshold_c1_{}".format(name))
            outfileC2 = os.path.join(c2dir, "threshold_c2_{}".format(name))
            outfileC3 = os.path.join(c3dir, "threshold_c3_{}".format(name))
            outfileC4 = os.path.join(c4dir, "threshold_c4_{}".format(name))

            # Save thresholded .tiff files.
            IJ.saveAs(c1.flatten(), "Tiff", outfileC1)
            IJ.saveAs(c2.flatten(), "Tiff", outfileC2)
            IJ.saveAs(c3.flatten(), "Tiff", outfileC3)
            IJ.saveAs(c4.flatten(), "Tiff", outfileC4)

    # Show results tables.
#    c1Results.show("channel1")
#    c2Results.show("channel2")
#    c3Results.show("channel3")
#    c4Results.show("channel4")

    # Prepare results table filenames.
    c1out = os.path.join(outdir, "channel1.csv")
    c2out = os.path.join(outdir, "channel2.csv")
    c3out = os.path.join(outdir, "channel3.csv")
    c4out = os.path.join(outdir, "channel4.csv")

    # Save results tables.
    ResultsTable.save(c1Results, c1out)
    ResultsTable.save(c2Results, c2out)
    ResultsTable.save(c3Results, c3out)
    ResultsTable.save(c4Results, c4out)


main()
