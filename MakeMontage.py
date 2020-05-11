import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
import ij.ImageStack as ImageStack
import ij.WindowManager as wm

# import ij.measure.ResultsTable as ResultsTable
# import ij.measure.Measurements as Measurements
#
# import ij.plugin.ChannelSplitter as ChannelSplitter
# import ij.plugin.HyperStackConverter as HyperStackConverter
# import ij.plugin.ZProjector as ZProjector
# import ij.plugin.RGBStackMerge as RGBStackMerge
# import ij.plugin.StackCombiner as StackCombiner
import ij.plugin.MontageMaker as MontageMaker
# import ij.plugin.StackCombiner as StackCombiner
# import ij.plugin.Duplicator as Duplicator
# import ij.plugin.Concatenator as Concatenator

# import ij.plugin.Thresholder as Thresholder

# import ij.plugin.filter.ParticleAnalyzer as ParticleAnalyzer
# import ij.plugin.filter.BackgroundSubtracter as BackgroundSubtracter
# import ij.plugin.filter.EDM as EDM

import os
import math


def chunks(seq, num):
    """Function which splits a list in parts.

    This function takes a list 'seq' and returns it in more or less equal parts of length 'num' as a list of lists.

    Args:
        seq: A list, at least longer than num.
        num: the division factor to create sublists.

    Returns:
        A list of sublists.
    """

    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


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


def main():
    def _makestack(implist):
        stack = ImageStack()
        name = implist[0].getTitle()
        for imp in implist:
            IJ.log("makestack: {}".format(imp))
            stack.addSlice(imp.getProcessor())
        stack = ImagePlus(name, stack)
        return stack


    def _makemontage(imp):
        name = imp.getTitle()
        width, height, nChannels, nSlices, nFrames = imp.getDimensions()
        montage = MontageMaker().makeMontage2(imp,
                                              4,  # int columns
                                              4,  # int rows
                                              1.00,  # double scale
                                              1,  # int first
                                              nSlices,  # int last
                                              1,  # int inc
                                              0,  # int borderWidth
                                              True)  # boolean labels)
        montage.setTitle(name)
        return montage


    def _saveimage(imp):
        name = imp.getTitle()
        outfile = os.path.join(outdir, "{}.jpg".format(name))
        IJ.saveAs(imp, "Jpeg", outfile)

    def _openimp(file):
        path = os.path.join(indir, file)
        imp = ImagePlus(path)
        return imp


    indir = IJ.getDirectory("input directory")
    outdir = IJ.getDirectory("output directory")
    files = sorted(os.listdir(indir))
    IJ.log("files: {}".format(files))
    images = [_openimp(file) for file in files]
    imagechunks = chunks(images, 6)

    stacks = [_makestack(chunk) for chunk in imagechunks]
    montages = [_makemontage(stack) for stack in stacks]

    [_saveimage(montage) for montage in montages]



    # ids = wm.getIDList()
    # name = wm.getImage(ids[0]).getTitle()
    # stack = ImageStack()
    # for id in ids:
    #     image = wm.getImage(id)
    #     stack.addSlice(image.getProcessor())
    #     image.close()

    # imp = ImagePlus(name, stack)
    # imp.show()
    # montage = MontageMaker().makeMontage2(imp,
    #                                        4,  # int columns
    #                                        4,  # int rows
    #                                        1.00,  # double scale
    #                                        1,  # int first
    #                                        16,  # int last
    #                                        1,  # int inc
    #                                        0,  # int borderWidth
    #                                        False)  # boolean labels)
    # montage.show()
    # outdir = IJ.getDirectory("output directory")
    # outfile = os.path.join(outdir, "{}.jpg".format(name))
    # IJ.saveAs(montage, "Jpeg", outfile)

main()