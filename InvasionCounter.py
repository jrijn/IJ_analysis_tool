import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
# import ij.ImageStack as ImageStack
# import ij.WindowManager as wm

import ij.measure.ResultsTable as ResultsTable
import ij.measure.Measurements as Measurements

import ij.plugin.ChannelSplitter as ChannelSplitter
import ij.plugin.HyperStackConverter as HyperStackConverter
import ij.plugin.ZProjector as ZProjector
# import ij.plugin.RGBStackMerge as RGBStackMerge
# import ij.plugin.StackCombiner as StackCombiner
# import ij.plugin.MontageMaker as MontageMaker
# import ij.plugin.StackCombiner as StackCombiner
# import ij.plugin.Duplicator as Duplicator
# import ij.plugin.Concatenator as Concatenator

# import ij.plugin.Thresholder as Thresholder

import ij.plugin.filter.ParticleAnalyzer as ParticleAnalyzer
# import ij.plugin.filter.BackgroundSubtracter as BackgroundSubtracter
# import ij.plugin.filter.EDM as EDM

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
    nucdir = os.path.join(outdir, "nuclei")
    bacdir = os.path.join(outdir, "bacteria")
    rufdir = os.path.join(outdir, "ruffles")
    gfpdir = os.path.join(outdir, "gfp")
    channelsdir = os.path.join(outdir, "channels")
    if not os.path.isdir(nucdir):
        os.mkdir(nucdir)
    if not os.path.isdir(bacdir):
        os.mkdir(bacdir)
    if not os.path.isdir(rufdir):
        os.mkdir(rufdir)
    if not os.path.isdir(gfpdir):
        os.mkdir(gfpdir)
    if not os.path.isdir(channelsdir):
        os.mkdir(channelsdir)

    # Collect all file paths in the input directory
    files = readdirfiles(indir)

    nucResults = ResultsTable()
    bacResults = ResultsTable()
    rufResults = ResultsTable()
    gfpResults = ResultsTable()

    for file in files:
        if file.endswith('ome.tif') or file.endswith('ome.tiff'):
            imp = stackprocessor(file,
                                   nChannels=4,
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

            nuc = countobjects(channels[0], nucResults,
                               threshMethod="Triangle",
                               subtractBackground=True,
                               # dilate=True,
                               watershed=True,
                               minSize=3.00,
                               maxSize=100,
                               minCirc=0.00,
                               maxCirc=1.00)

            bac = countobjects(channels[1], bacResults,
                               threshMethod="RenyiEntropy",
                               subtractBackground=False,
                               watershed=False,
                               minSize=0.20,
                               maxSize=30.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            ruf = countobjects(channels[2], rufResults,
                               threshMethod="RenyiEntropy",
                               minSize=2.00,
                               maxSize=30.00,
                               minCirc=0.20,
                               maxCirc=1.00)

            gfp = countobjects(channels[3], gfpResults,
                               threshMethod="RenyiEntropy",
                               subtractBackground=False,
                               watershed=True,
                               minSize=0.20,
                               maxSize=30.00,
                               minCirc=0.00,
                               maxCirc=1.00)

            # binaries = [nuc, bac, ruf, gfp]
            # channels[0].show()
            # binaries[0].show()
            # binMontage = RGBStackMerge().mergeChannels(binaries, False)
            # binMontage.show()
            # chsMontage = RGBStackMerge().mergeChannels(channels, False)
            # binMontage = MontageMaker().makeMontage2(binMontage,
            #                                        4,  # int columns
            #                                        4,  # int rows
            #                                        1.00,  # double scale
            #                                        1,  # int first
            #                                        16,  # int last
            #                                        1,  # int inc
            #                                        0,  # int borderWidth
            #                                        False)  # boolean labels)
            # chsMontage = MontageMaker().makeMontage2(chsMontage,
            #                                          4,  # int columns
            #                                          4,  # int rows
            #                                          1.00,  # double scale
            #                                          1,  # int first
            #                                          16,  # int last
            #                                          1,  # int inc
            #                                          0,  # int borderWidth
            #                                          False)  # boolean labels)
            #
            # binMontage.show()
            # chsMontage.show()

            outfilenuc = os.path.join(nucdir, "threshold_nuc_{}".format(name))
            outfilebac = os.path.join(bacdir, "threshold_bac_{}".format(name))
            outfileruf = os.path.join(rufdir, "threshold_ruf_{}".format(name))
            outfilegfp = os.path.join(gfpdir, "threshold_gfp_{}".format(name))

            IJ.saveAs(nuc.flatten(), "Tiff", outfilenuc)
            IJ.saveAs(bac.flatten(), "Tiff", outfilebac)
            IJ.saveAs(ruf.flatten(), "Tiff", outfileruf)
            IJ.saveAs(gfp.flatten(), "Tiff", outfilegfp)

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


main()
