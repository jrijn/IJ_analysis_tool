import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
import ij.ImageStack as ImageStack
import ij.WindowManager as wm

import ij.measure.ResultsTable as ResultsTable
import ij.measure.Measurements as Measurements

import ij.plugin.Duplicator as Duplicator
import ij.plugin.Concatenator as Concatenator
import ij.plugin.ChannelSplitter as ChannelSplitter
import ij.plugin.RGBStackMerge as RGBStackMerge
import ij.plugin.StackCombiner as StackCombiner
import ij.plugin.MontageMaker as MontageMaker
import ij.plugin.StackCombiner as StackCombiner
import ij.plugin.HyperStackConverter as HyperStackConverter
import ij.plugin.Thresholder as Thresholder
import ij.plugin.ZProjector as ZProjector

import ij.plugin.filter.BackgroundSubtracter as BackgroundSubtracter
import ij.plugin.filter.EDM as EDM
import ij.plugin.filter.ParticleAnalyzer as ParticleAnalyzer

import math
import os


def countnuclei(imp):
    c1, c2, c3 = ChannelSplitter.split(imp)
    IJ.run(c1, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(c1, "Triangle dark")
    IJ.run(c1, "Convert to Mask", "")
    IJ.run(c1, "Dilate", "")
    IJ.run(c1, "Watershed", "")
    IJ.run(c1, "Set Measurements...", "area mean shape centroid display label redirect=None decimal=3")
    IJ.run(c1, "Analyze Particles...", "size=0-infinity display exclude summarize add")
    return c1


def countbacteria(imp):
    c1, c2, c3 = ChannelSplitter.split(imp)
    IJ.run(c2, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(c2, "RenyiEntropy dark")
    IJ.run(c2, "Convert to Mask", "")
    IJ.run(c2, "Set Measurements...", "area mean shape centroid display label redirect=None decimal=3")
    IJ.run(c2, "Analyze Particles...", "size=0.50-10.00 circularity=0.30-1.00 show=Overlay display exclude summarize "
                                       "add")
    return c2


def countruffles(imp):
    """Threshold and count ruffles in channel 3.
        This function splits an image in the separate channels, and counts the number of ruffles in the thresholded
        channel 3.

        Args:
            directory: The path to a directory containing the tiff files.

        Returns:
            A list of filepaths.
        """
    c1, c2, c3 = ChannelSplitter.split(imp)
    IJ.run(c3, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(c3, "RenyiEntropy dark")
    IJ.run(c3, "Convert to Mask", "")
    IJ.run(c3, "Set Measurements...", "area mean shape centroid display label redirect=None decimal=3")
    IJ.run(c3, "Analyze Particles...", "size=1-30.00 circularity=0.20-1.00 show=Overlay display exclude summarize "
                                       "add")
    return c3


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

    IJ.log(" - Current image: {}".format(imp))
    imp = ZProjector.run(imp, "max")
    return imp


def countobjects(imp, rt,
                 watershed=False, dilate=False,
                 threshMethod="Otsu",
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
    # channels = ChannelSplitter.split(imp)
    # cn = channels[channelNumber-1]

    IJ.run(imp, "Subtract Background...", "rolling=50")
    IJ.setAutoThreshold(imp, "{} dark".format(threshMethod))
    IJ.run(imp, "Convert to Mask", "")
    if dilate:
        IJ.run(imp, "Dilate", "")
    if watershed:
        IJ.run(imp, "Watershed", "")
    # IJ.run(cn, "Set Measurements...", "area mean shape centroid display label redirect=None decimal=3")
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
    nucdir = os.path.join(outdir, "nuclei")
    bacdir = os.path.join(outdir, "bacteria")
    rufdir = os.path.join(outdir, "ruffles")
    gfpdir = os.path.join(outdir, "gfp")
    if not os.path.isdir(nucdir):
        os.mkdir(nucdir)
    if not os.path.isdir(bacdir):
        os.mkdir(bacdir)
    if not os.path.isdir(rufdir):
        os.mkdir(rufdir)
    if not os.path.isdir(gfpdir):
        os.mkdir(gfpdir)

    # Collect all file paths in the input directory
    files = readdirfiles(indir)

    for file in files:
        if file.endswith('ome.tif') or file.endswith('ome.tiff'):
            imp = stackprocessor(file,
                                   nChannels=4,
                                   nSlices=7,
                                   nFrames=1)
            channels = ChannelSplitter.split(imp)
            name = imp.getTitle()
            cal = imp.getCalibration()
            scale = cal['w']
            IJ.log("calibration: {}".format(scale))

            nucResults = ResultsTable()
            bacResults = ResultsTable()
            rufResults = ResultsTable()
            gfpResults = ResultsTable()

            nuc = countobjects(channels[0], nucResults,
                               threshMethod="Triangle",
                               # dilate=True,
                               watershed=True,
                               minSize=3.00,
                               maxSize=100,
                               minCirc=0.00,
                               maxCirc=1.00)

            bac = countobjects(channels[1], bacResults,
                               threshMethod="RenyiEntropy",
                               watershed=False,
                               minSize=0.00,
                               maxSize=100.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            ruf = countobjects(channels[2], rufResults,
                               threshMethod="RenyiEntropy",
                               minSize=1.00,
                               maxSize=30.00,
                               minCirc=0.20,
                               maxCirc=1.00)

            gfp = countobjects(channels[3], gfpResults,
                               threshMethod="RenyiEntropy",
                               watershed=False,
                               minSize=0.00,
                               maxSize=100.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            outfilenuc = os.path.join(nucdir, "threshold_{}".format(name))
            outfilebac = os.path.join(bacdir, "threshold_{}".format(name))
            outfileruf = os.path.join(rufdir, "threshold_{}".format(name))
            outfilegfp = os.path.join(gfpdir, "threshold_{}".format(name))

            IJ.saveAs(nuc, "Tiff", outfilenuc)
            IJ.saveAs(bac, "Tiff", outfilebac)
            IJ.saveAs(ruf, "Tiff", outfileruf)
            IJ.saveAs(gfp, "Tiff", outfilegfp)

    nucResults.show("nuclei")
    bacResults.show("bacteria")
    rufResults.show("ruffles")
    gfpResults.show("gfp")

    nucout = os.path.join(outdir, "nuclei.csv")
    bacout = os.path.join(outdir, "bacteria.csv")
    rufout = os.path.join(outdir, "ruffles.csv")
    gfpout = os.path.join(outdir, "gfp.csv")

    ResultsTable.save(nucResults, nucout)
    ResultsTable.save(bacResults, bacout)
    ResultsTable.save(rufResults, rufout)
    ResultsTable.save(gfpResults, gfpout)


    # # Count nuclei for every image in the folder
    # IJ.log("Counting nuclei...")
    # for file in files:
    #     if file.endswith('ome.tif') or file.endswith('ome.tiff'):
    #         image = stackprocessor(file,
    #                                nChannels=4,
    #                                nSlices=7,
    #                                nFrames=1)
    #         nuc = countobjects(image,
    #                            channelNumber=1,
    #                            threshMethod="Triangle",
    #                            dilate=True,
    #                            watershed=True)
    #         name = image.getTitle()
    #         outfile = os.path.join(nucdir, "threshold_{}".format(name))
    #         IJ.saveAs(nuc, "Tiff", outfile)
    #
    # # Save the ResultsTable object
    # idx = name.find("MMStack")
    # condition = name[:idx]
    # csvname = "nuc_{}".format(condition)
    # saveresults(outdir, csvname)
    #
    # # Count bacteria for every image in the folder
    # IJ.log("Counting bacteria...")
    # for file in files:
    #     if file.endswith('ome.tif') or file.endswith('ome.tiff'):
    #         image = stackprocessor(file,
    #                                nChannels=4,
    #                                nSlices=7,
    #                                nFrames=1)
    #         bac = countobjects(image,
    #                            channelNumber=2,
    #                            threshMethod="RenyiEntropy",
    #                            size="1-30.00",
    #                            circularity="0.30-1.00",
    #                            )
    #         name = image.getTitle()
    #         outfile = os.path.join(bacdir, "threshold_{}".format(name))
    #         IJ.saveAs(bac, "Tiff", outfile)
    #
    # # Save the ResultsTable object
    # csvname = "bac_{}".format(condition)
    # saveresults(outdir, csvname)
    #
    # # Count ruffles for every image in the folder
    # IJ.log("Counting ruffles...")
    # for file in files:
    #     if file.endswith('ome.tif') or file.endswith('ome.tiff'):
    #         image = stackprocessor(file,
    #                                nChannels=4,
    #                                nSlices=7,
    #                                nFrames=1)
    #         ruf = countobjects(image,
    #                            channelNumber=3,
    #                            threshMethod="RenyiEntropy",
    #                            size="1-30.00",
    #                            circularity="0.20-1.00",
    #                            )
    #         name = image.getTitle()
    #         outfile = os.path.join(rufdir, "threshold_{}".format(name))
    #         IJ.saveAs(ruf, "Tiff", outfile)
    #
    # # Save the ResultsTable object
    # csvname = "ruf_{}".format(condition)
    # saveresults(outdir, csvname)
    #
    # # Count gfp+ objects for every image in the folder
    # IJ.log("Counting ruffles...")
    # for file in files:
    #     if file.endswith('ome.tif') or file.endswith('ome.tiff'):
    #         image = stackprocessor(file,
    #                                nChannels=4,
    #                                nSlices=7,
    #                                nFrames=1)
    #         gfp = countobjects(image,
    #                            channelNumber=4,
    #                            threshMethod="RenyiEntropy",
    #                            size="1-30.00",
    #                            circularity="0.30-1.00"
    #                            )
    #         name = image.getTitle()
    #         outfile = os.path.join(gfpdir, "threshold_{}".format(name))
    #         IJ.saveAs(gfp, "Tiff", outfile)
    #
    # # Save the ResultsTable object
    # csvname = "ruf_{}".format(condition)
    # saveresults(outdir, csvname)


main()
