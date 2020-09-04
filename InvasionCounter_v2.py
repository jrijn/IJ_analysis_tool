import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
import ij.measure.ResultsTable as ResultsTable
import ij.measure.Measurements as Measurements
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
    dapidir = os.path.join(outdir, "dapi")
    gfpdir = os.path.join(outdir, "gfp")
    # rufdir = os.path.join(outdir, "ruffles")
    rfpdir = os.path.join(outdir, "rfp")
    channelsdir = os.path.join(outdir, "channels")
    if not os.path.isdir(dapidir):
        os.mkdir(dapidir)
    if not os.path.isdir(gfpdir):
        os.mkdir(gfpdir)
    # if not os.path.isdir(rufdir):
    #     os.mkdir(rufdir)
    if not os.path.isdir(rfpdir):
        os.mkdir(rfpdir)
    if not os.path.isdir(channelsdir):
        os.mkdir(channelsdir)

    # Collect all file paths in the input directory
    files = readdirfiles(indir)

    dapiResults = ResultsTable()
    gfpResults = ResultsTable()
    # rufResults = ResultsTable()
    rfpResults = ResultsTable()

    for file in files:
        if file.endswith('ome.tif') or file.endswith('ome.tiff'):
            imp = stackprocessor(file,
                                   nChannels=3,
                                   nSlices=7,
                                   nFrames=1)
            channels = ChannelSplitter.split(imp)
            name = imp.getTitle()
            IJ.log("Processing image: {}".format(name))
            for c in range(len(channels)):
                IJ.run(channels[c], "Grays", "")
                IJ.run(channels[c], "Invert", "")
                jpgname = channels[c].getShortTitle()
                jpgoutfile = os.path.join(channelsdir, "{}.jpg".format(jpgname))
                IJ.saveAs(channels[c].flatten(), "Jpeg", jpgoutfile)
                IJ.run(channels[c], "Invert", "")

            dapi = countobjects(channels[0], dapiResults,
                               threshMethod="Triangle",
                               subtractBackground=True,
                               # dilate=True,
                               watershed=True,
                               minSize=3.00,
                               maxSize=100,
                               minCirc=0.00,
                               maxCirc=1.00)

            gfp = countobjects(channels[1], gfpResults,
                               threshMethod="RenyiEntropy",
                               subtractBackground=False,
                               watershed=False,
                               minSize=0.20,
                               maxSize=30.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            # ruf = countobjects(channels[2], rufResults,
            #                    threshMethod="RenyiEntropy",
            #                    minSize=2.00,
            #                    maxSize=30.00,
            #                    minCirc=0.20,
            #                    maxCirc=1.00)

            rfp = countobjects(channels[2], rfpResults,
                               threshMethod="RenyiEntropy",
                               subtractBackground=False,
                               watershed=True,
                               minSize=0.20,
                               maxSize=30.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            outfilenuc = os.path.join(dapidir, "threshold_nuc_{}".format(name))
            outfilebac = os.path.join(gfpdir, "threshold_bac_{}".format(name))
            # outfileruf = os.path.join(rufdir, "threshold_ruf_{}".format(name))
            outfilegfp = os.path.join(rfpdir, "threshold_gfp_{}".format(name))

            IJ.saveAs(dapi.flatten(), "Tiff", outfilenuc)
            IJ.saveAs(gfp.flatten(), "Tiff", outfilebac)
            # IJ.saveAs(ruf.flatten(), "Tiff", outfileruf)
            IJ.saveAs(rfp.flatten(), "Tiff", outfilegfp)

    dapiResults.show("dapi")
    gfpResults.show("gfp")
    # rufResults.show("ruffles")
    rfpResults.show("rfp")

    dapiout = os.path.join(outdir, "dapi.csv")
    gfpout = os.path.join(outdir, "gfp.csv")
    # rufout = os.path.join(outdir, "ruffles.csv")
    rfpout = os.path.join(outdir, "rfp.csv")

    ResultsTable.save(dapiResults, dapiout)
    ResultsTable.save(gfpResults, gfpout)
    # ResultsTable.save(rufResults, rufout)
    ResultsTable.save(rfpResults, rfpout)


main()
