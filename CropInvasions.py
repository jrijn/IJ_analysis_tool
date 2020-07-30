import ij.IJ as IJ
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
# import ij.plugin.Thresholder as Thresholder
# import ij.plugin.filter.ParticleAnalyzer as ParticleAnalyzer
# import ij.plugin.filter.BackgroundSubtracter as BackgroundSubtracter
# import ij.plugin.filter.EDM as EDM
import os
# import math


def preparedir(outdir, dir1="output1", dir2="output2"):
    """Prepares input and output directories of this module.

    Simple function which prepares the output directory and input .csv file.
    If the subfolders ./montage and ./with_empty_stacks do not exist its makes them.

    Args:
        outdir: Path of the chosen output directory.
        dir1: Name of the first output subdirectory. Defaults to 'output1'.
        dir2: Name of the first output subdirectory. Defaults to 'output2'.

    Returns:
        A list containing the path strings of both output directories:
        [path_of_output1, path_of_output2]
    """

    # Create the output subdirectory paths, if they do not exist already.
    out1 = os.path.join(outdir, dir1)
    out2 = os.path.join(outdir, dir2)
    if not os.path.isdir(out1):
        os.mkdir(out1)
    if not os.path.isdir(out2):
        os.mkdir(out2)

    out = [out1, out2]
    return out


def opencsv():
    """Simply imports .csv file in ImageJ.

    Ask the user for the location of a .csv file.

    Returns:
        A ResultsTable object from the input file.
    """

    csv = IJ.getFilePath("Choose a .csv file")

    # Open the csv file and return it as ResultsTable object.
    try:
        if csv.endswith(".csv"):
            res = ResultsTable.open(csv)
            return res
        else:
            raise TypeError()
    except TypeError:
        IJ.log("The chosen file was not a .csv file.")
    except Exception as ex:
        IJ.log("Something in opencsv() went wrong: {}".format(type(ex).__name__, ex.args))


def getresults(rt):
    """Retrieve IJ ResultsTable object and return table as list of dictionaries.

    Args:
        rt (ij.measure.ResultsTable): An Imagej ResultsTable object.

    Returns:
        list: A list of ResultsTable rows, represented as dictionary with column names as keys.
        
        for example:
            [
            {'column1' : 'value', 'column2' : 'value'},
            {'column1' : 'value', 'column2' : 'value'},
            ...,
            ]
    """    
    try:
        columns = rt.getHeadings()
        table = [{column: rt.getValue(column, row) for column in columns} for row in range(rt.size())]
        if rt.columnExists("Label"):
            for i in range(len(table)):
                table[i]["Label"] = rt.getStringValue("Label", i)
        # IJ.log("table: {}\nlength: {}".format(table, len(table)))
        return table
    except AttributeError:
        IJ.log("The parameter passed to getresults() was not a resultsTable object.")
    except Exception as ex:
        IJ.log("Something in getresults() went wrong: {}".format(type(ex).__name__, ex.args))


def croproi(imp, tracks, outdir, subdirs, add_empty_after=False,
            trackindex="TRACK_INDEX",
            trackduration="TRACK_DURATION",
            trackid="TRACK_ID",
            trackx="TRACK_X_LOCATION",
            tracky="TRACK_Y_LOCATION",
            trackstart="TRACK_START",
            trackstop="TRACK_STOP",
            roi_x=150, roi_y=150):
    """Function cropping ROIs from an ImagePlus stack based on a ResultsTable object.

    This function crops square ROIs from a hyperstack based on locations defined in the ResultsTable.
    The ResultsTable should, however make sense. The following headings are required:

    "TRACK_INDEX", "TRACK_DURATION", "TRACK_ID", "TRACK_X_LOCATION", "TRACK_Y_LOCATION", "TRACK_START", "TRACK_STOP"

    Args:
        imp: An ImagePlus hyperstack (timelapse).
        results_table: A ResultsTable object with the proper column names.
        outdir: The primary output directory.
        subdirs: A list of two paths for the output of this funcion. ([path_of_output1, path_of_output2])
        add_empty_after: Add empty frames after to make all output stacks the same lenght.
        trackindex: A unique track identifier. Defaults to "TRACK_INDEX"
        trackduration: The tracks duration. Defaults to "TRACK_DURATION".
        trackid: The track ID, will be used in the filename. Defaults to "TRACK_ID".
        trackxlocation: Defaults to "TRACK_X_LOCATION".
        trackylocation: Defaults to "TRACK_Y_LOCATION".
        trackstart: Defaults to "TRACK_START".
        trackstop: Defaults to "TRACK_STOP".
        roi_x: Width of the ROI.
        roi_y: Height of the ROI.
    """

    output1 = subdirs[0]
    output2 = subdirs[1]

    maxduration = int( max([tracks[i][trackduration] for i in tracks]) )

    # Now loop through all the tracks, extract the track position, set an ROI and crop the hyperstack.
    for i in tracks:  # This loops through all tracks. Use a custom 'tracks[0:5]' to test and save time!

        # Extract all needed row values.
        i_x = int(i[trackx] * 5.988)
        i_y = int(i[tracky] * 5.988)
        i_id = int(i[trackid])
        i_duration = int(i[trackduration] / 15)
        i_start = int(i[trackstart] / 15)
        i_stop = int(i[trackstop] / 15)

        # Now set an ROI according to the track's xy position in the hyperstack.
        imp.setRoi(i_x - roi_x / 2, i_y - roi_y / 2,  # upper left x, upper left y
                   roi_x, roi_y)  # roi x dimension, roi y dimension

        # Retrieve image dimensions.
        width, height, nChannels, nSlices, nFrames = imp.getDimensions()

        # And then crop (duplicate, actually) this ROI for the track's time duration.
        IJ.log("Cropping image with TRACK_INDEX: {}/{}".format(i_id, int(len(tracks))))
        imp2 = Duplicator().run(imp,
                                1,  # firstC
                                nChannels,  # lastC
                                1,  # firstZ
                                nSlices,  # lastZ
                                i_start,  # firstT
                                i_stop)  # lastT

        # Save the substack in the output directory
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(i_id))
        IJ.saveAs(imp2, "Tiff", outfile)

        # --- OPTIONS ---
        # Add empty frames to the end of the stack if add_empty_after is True.
        if add_empty_after:

            delta = maxduration - i_duration

            try:

                if delta != 0:
                    imp_empty = concatenatestack(imp2, 0, delta)
                elif delta == 0:
                    imp_empty = imp2
            
                IJ.run(imp_empty, "Label...",
                       "format=Text starting=0 interval=1 x=5 y=20 font=12 text=TRACK_ID:{} range=1-{}".format(i_id, nFrames))
                outfile3 = os.path.join(output1, "TRACK_ID_{}.tif".format(i_id))
                IJ.saveAs(imp_empty, "Tiff", outfile3)

            except Exception as ex:
                IJ.log("Something in opencsv() went wrong: {}".format(type(ex).__name__, ex.args))


def _emptystack(imp, inframes=0):
    """Create an empty stack with the dimensions of imp.

    This function creates an empty stack with black images, with the same dimensions of input image 'imp'.
    The argument inframes allows one to set the number of frames the stack should have. This defaults to the
    input frame depth through an if statement.

    Args:
        imp: ImagePlus hyperstack object.
        inframes: The total framedepth of the returned stack. Default is 0.

    Returns:
        An ImagePlus hyperstack object.
    """

    # Start by reading the calibration and dimensions of the input stack to correspond to the output stack.
    cal = imp.getCalibration()
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()

    # This defaults inframes to the input frame depth.
    if inframes == 0:
        inframes = nFrames

    # Create the new stack according to the desired dimensions.
    outstack = IJ.createHyperStack("empty_stack",
                                   width,  # width
                                   height,  # height
                                   nChannels,  # channels
                                   nSlices,  # slices
                                   inframes,  # frames
                                   16)
    # Re-apply the calibration and return the empty stack.
    outstack.setCalibration(cal)
    return outstack

#TODO only works for 2 channel images.
#TODO tried to fix for multiple channels, not tested!
def concatenatestack(imp, frames_before, frames_after):
    """Append empty frames (timepoints) before and after an input stack.

    This function is used to append a stack of empty frames before and after the input stack.
    imp is the input stack, frames_before determines the number of frames to be appended in front,
    frames_after determines the number of frames to be appended at the end.

    Args:
        imp: ImagePlus hyperstack object.
        frames_before: the number of frames to be appended before.
        frames_after: the number of frames to be appended after.

    Returns:
        An ImagePlus hyperstack object.
    """

    cal = imp.getCalibration()
    channels = ChannelSplitter().split(imp)

    # If frames_before is 0, skip this step to prevent creation of an empty image
    # Also, split channels for correct concatenation in following step.
    if frames_before != 0:
        before = _emptystack(imp, frames_before)
        before.setCalibration(cal)
        befores = ChannelSplitter().split(before)

    # If frames_after is 0, skip this step to prevent creation of an empty image.
    # Also, split channels for correct concatenation in following step.
    if frames_after != 0:
        after = _emptystack(imp, frames_after)
        after.setCalibration(cal)
        # This might not even be needed, Concatenator seems to work with hyperstacks?:
        afters = ChannelSplitter().split(after) 

    # Concatenate existing stacks and merge channels back to one file.
    # Start with the condition when _emptystack() has to be appended before and after imp.
    if frames_before != 0 and frames_after != 0:

        concat = [Concatenator().run(befores[i], channels[i], afters[i]) for i,j in enumerate(channels)]
        # concat_c1 = Concatenator().run(before_c1, imp_c1, after_c1)
        # concat_c2 = Concatenator().run(before_c2, imp_c2, after_c2)

    # Following the condition when _emptystack() has to be appended after imp alone.
    elif frames_before == 0 and frames_after != 0:

        concat = [Concatenator().run(channels[i], afters[i]) for i,j in enumerate(channels)]
        # concat_c1 = Concatenator().run(imp_c1, after_c1)
        # concat_c2 = Concatenator().run(imp_c2, after_c2)

    # Following the condition when _emptystack() has to be appended before imp alone.
    elif frames_before != 0 and frames_after == 0:

        concat = [Concatenator().run(befores[i], channels[i]) for i,j in enumerate(channels)]
        # concat_c1 = Concatenator().run(before_c1, imp_c1)
        # concat_c2 = Concatenator().run(before_c1, imp_c1)

    else:
        # Weird way to catch exception, but ok.
        IJ.log("In concatenatestack(): reached else")
        return False

    # Now re-merge the channels and return the concatenated hyperstack.
    impout = RGBStackMerge().mergeHyperstacks(concat, False)  # boolean keep
    return impout


# Simple function making a montage of the image hyperstack passed as argument
def montage(imp):
    """Makes a montage of the input hyperstack.

    Simple function making a montage of the image hyperstack passed as argument.

    Args:
        imp: ImagePlus hyperstack object.

    Returns:
        An ImagePlus hyperstack object.
    """

    width, height, nChannels, nSlices, nFrames = imp.getDimensions()

    channels = ChannelSplitter().split(imp)
    montages = []
    for channel in channels:
        c = MontageMaker().makeMontage2(channel,
                                               nFrames,  # int columns
                                               nSlices,  # int rows
                                               1.00,  # double scale
                                               1,  # int first
                                               nFrames,  # int last
                                               1,  # int inc
                                               0,  # int borderWidth
                                               False)  # boolean labels)
        montages.append(c)

    # Now re-merge the channels and return the montage.
    montage = RGBStackMerge().mergeChannels(montages, False)  # boolean keep
    return montage


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


def _readdirfiles(directory, nChannels=2, nSlices=1):
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

#TODO Only works for 2-channel images.
def _listsplitchannels(collection):
    """Split channels of a list of hyperstacks.

    This function splits a list of 2 channel hyperstacks in two separate lists per channel.

    Args:
        collection: A list of hyperstacks.

    Returns:
        One list of hyperstacks per channel.
    """

    coll_c1 = []
    coll_c2 = []

    for stack in collection:
        c1, c2 = ChannelSplitter().split(stack)
        coll_c1.append(c1.getImageStack())
        coll_c2.append(c2.getImageStack())

    return coll_c1, coll_c2


def _horcombine(imp_collection):
    """Combine a list of stacks with the same dimensions horizontally.

    Args:
        imp_collection: A list of stacks.

    Returns:
        A horizontally combined stack of the input images.
    """

    comb = imp_collection[0]

    for imp in imp_collection:
        if imp != imp_collection[0]:
            comb = StackCombiner().combineHorizontally(comb, imp)

    return comb


def _vercombine(imp_collection):
    """Combine a list of stacks with the same dimensions vertically.

    Args:
        imp_collection: A list of stacks.

    Returns:
        A vertically combined stack of the input images.
    """

    comb = imp_collection[0]

    for imp in imp_collection:
        if imp != imp_collection[0]:
            comb = StackCombiner().combineVertically(comb, imp)

    return comb


# TODO: Currently only handles input files with 2 channels. Fix if broader application is needed.
def combinestacks(directory, height=5):
    """Combine all tiff stacks in a directory to a panel.

    Args:
        directory: Path to a directory containing a collection of .tiff files.
        height: The height of the panel (integer). Defaults to 5. The width is spaces automatically.

    Returns:
        A combined stack of the input images.
    """

    IJ.log("\nCombining stacks...")
    files = _readdirfiles(directory)
    groups = chunks(files, height)

    horiz = []
    for i in range(0, len(groups)):
        c1, c2 = _listsplitchannels(groups[i])
        comb_c1 = _horcombine(c1)
        comb_c2 = _horcombine(c2)
        comb_list = [ImagePlus('c1', comb_c1), ImagePlus('c2', comb_c2)]
        comb = RGBStackMerge().mergeChannels(comb_list, False)  # boolean keep
        horiz.append(comb)

    for i in range(0, len(horiz)):
        c1, c2 = _listsplitchannels(horiz)
        comb_c1 = _vercombine(c1)
        comb_c2 = _vercombine(c2)
        comb_list = [ImagePlus('c1', comb_c1), ImagePlus('c2', comb_c2)]
        comb = RGBStackMerge().mergeChannels(comb_list, False)  # boolean keep

    comb.show()


# The main loop, call wanted functions.
def main():
    # Get the wanted output directory and prepare subdirectories for output.
    outdir = IJ.getDirectory("output directory")
    subdirs = preparedir(outdir, dir1="with_empty_stacks", dir2="montage")

    # Open the 'Track statistics.csv' input file and run main crop function.
    rt = opencsv()
    rt = getresults(rt)
    imp = WindowManager.getCurrentImage()

    croproi(imp, rt,
            outdir=outdir, subdirs=subdirs,
            add_empty_after=False,
            roi_x=150, roi_y=150)

    # Combine all output stacks into one movie.
    # combinestacks(subdirs[0])


# Execute main()
main()
