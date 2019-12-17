from ij.plugin import Duplicator, Concatenator, ChannelSplitter, RGBStackMerge, StackCombiner, MontageMaker, \
    StackCombiner, HyperStackConverter
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij.measure import ResultsTable as ResultsTable
import os

# Declare global variables
global outdir
global dir1
global dir2


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

    # First ask for an output directory and the location of the 'Track statistics.csv' Trackmate output.
    # outdir = IJ.getDirectory("output directory")

    # Also create the output subdirectory paths, if they do not exist already.
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
        res = ResultsTable.open(csv)
        return res
    except:
        IJ.log("Oops, 'Track statistics' file couldn't open")


# TODO: There's a lot going on, might want to try and split this up in separate functions.
def croproi(imp, results_table,
            outdir, subdirs,
            trackindex="TRACK_INDEX",
            trackduration="TRACK_DURATION",
            trackid="TRACK_ID",
            trackxlocation="TRACK_X_LOCATION",
            trackylocation="TRACK_Y_LOCATION",
            trackstart="TRACK_START",
            trackstop="TRACK_STOP",
            add_empty_before=False, add_empty_after=False,
            make_montage=False, roi_x=150, roi_y=150):
    """Function cropping ROIs from an ImagePlus stack based on a ResultsTable object.

    This function crops square ROIs from a hyperstack based on locations defined in the ResultsTable.
    The ResultsTable should, however make sense. The following headings are required:

    "TRACK_INDEX", "TRACK_DURATION", "TRACK_ID", "TRACK_X_LOCATION", "TRACK_Y_LOCATION", "TRACK_START", "TRACK_STOP"

    Args:
        imp: An ImagePlus hyperstack (timelapse).
        results_table: A ResultsTable object with the proper column names.
        outdir: The primary output directory.
        subdirs: A list of two paths for the output of this funcion. ([path_of_output1, path_of_output2])
        trackindex:
        trackduration:
        trackid:
        trackxlocation:
        trackylocation:
        trackstart:
        trackstop:
        add_empty_before: Add empty frames before to make all output stacks the same lenght.
        add_empty_after: Add empty frames after to make all output stacks the same lenght.
        make_montage: Make a montage of each substack and save to output1
        roi_x: Width of the ROI.
        roi_y: Height of the ROI.
    """

    output1 = subdirs[0]
    output2 = subdirs[1]

    # Extract the column index of 'TRACK_INDEX' from the csv file.
    # The column name cannot be used directly to extract the column values.
    # The 'TRACK_INDEX' is used to refer to the frame's row numbers, we'll loop through these.
    track_idx = results_table.getColumnIndex(trackindex)
    tracks = results_table.getColumn(track_idx).tolist()
    duration_idx = results_table.getColumnIndex(trackduration)
    duration = results_table.getColumn(duration_idx).tolist()
    IJ.log("[1] {} \n[2] {}\n[3] ".format(track_idx, tracks))

    # Now loop through all the tracks, extract the track position, set an ROI and crop the hyperstack!
    for i in tracks:  # This loops through all tracks. Use a custom 'range(0,1)' to test and save time!
        # Extract all needed row values.
        idx = int(i)
        i_id = int(results_table.getValue(trackid, idx))
        i_x = int(results_table.getValue(trackxlocation, idx) * 5.988)  # fix for calibration
        i_y = int(results_table.getValue(trackylocation, idx) * 5.988)  # fix for calibration
        i_start = int(results_table.getValue(trackstart, idx) / 15)
        i_stop = int(results_table.getValue(trackstop, idx) / 15)
        i_duration = int(results_table.getValue(trackduration, idx) / 15)
        i_fill_duration = int(max(duration) / 15 - i_duration)
        width, height, nChannels, nSlices, nFrames = imp.getDimensions()

        # Now set an ROI according to the track's xy position in the hyperstack.
        imp.setRoi(i_x - roi_x / 2, i_y - roi_y / 2,  # upper left x, upper left y
                   roi_x, roi_y)  # roi x dimension, roi y dimension

        # And then crop (duplicate, actually) this ROI for the track's time duration.
        IJ.log("\nCropping image with TRACK_INDEX: {}/{}".format(idx, max(tracks)))
        imp2 = Duplicator().run(imp,
                                1,  # firstC
                                nChannels,  # lastC
                                1,  # firstZ
                                nSlices,  # lastZ
                                i_start,  # firstT
                                i_stop)  # lastT

        # Save the substack in the output directory
        IJ.log("Save substack...")
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(i_id))
        IJ.saveAs(imp2, "Tiff", outfile)

        # Finally, if the user wants empty frames appended to get equal frame counts throughout:
        if add_empty_before and add_empty_after:
            # Concatenate the stacks with empty stacks before and after.
            IJ.log("Adding empty frames before and after...")
            imp_empty = concatenatestack(imp2, i_start, nFrames - i_stop)
            if imp_empty:
                outfile3 = os.path.join(output1, "TRACK_ID_{}.tif".format(i_id))
                IJ.saveAs(imp_empty, "Tiff", outfile3)
            else:
                # Let's us know if this concatenation fails.
                IJ.log("Concatenation failed at TRACK_ID: {}".format(i_id))

        if not add_empty_before and add_empty_after:
            # Concatenate the stacks with empty stacks after.
            IJ.log("Adding empty frames after...")

            if i_fill_duration != 0:  # Check if the current iteration is not the longest track.
                imp_empty = concatenatestack(imp2, 0, i_fill_duration)
            elif i_fill_duration == 0:  # If it is the longest track, just return the stack as is.
                imp_empty = imp2
            else:
                IJ.log("Track duration error at TRACK_ID: {}".format(i_id))

            if imp_empty:
                outfile3 = os.path.join(output1, "TRACK_ID_{}.tif".format(i_id))
                IJ.saveAs(imp_empty, "Tiff", outfile3)
            else:
                # Let's us know if this concatenation fails.
                IJ.log("Concatenation failed at TRACK_ID: {}".format(i_id))

        if add_empty_before and not add_empty_after:
            # Concatenate the stacks with empty stacks before.
            IJ.log("Adding empty frames before...")

            if i_fill_duration != 0:  # Check if the current iteration is not the longest track.
                imp_empty = concatenatestack(imp2, i_fill_duration)
            elif i_fill_duration == 0:  # If it is the longest track, just return the stack as is.
                imp_empty = imp2
            else:
                IJ.log("Track duration error at TRACK_ID: {}".format(i_id))

            if imp_empty:
                outfile3 = os.path.join(output1, "TRACK_ID_{}.tif".format(i_id))
                IJ.saveAs(imp_empty, "Tiff", outfile3)
            else:
                # Let's us know if this concatenation fails.
                IJ.log("Concatenation failed at TRACK_ID: {}".format(i_id))

        # Save the stack montage
        if make_montage:
            IJ.log("Making montage...")
            mont = montage(imp_empty)
            outfile2 = os.path.join(output2, "TRACK_ID_{}.tif".format(i_id))
            IJ.saveAs(mont, "Tiff", outfile2)


def emptystack(imp, inframes=0):
    """Create an empty stack with the dimensions of imp.

    This function creates an empty stack with black images, with the same dimensions of input image 'imp'.
    The argument inframes allows one to set the number of frames the stack should have. This defaults to the
    input frame depth through an if statement.

    Args:
        imp: ImageStack object.
        inframes: The total framedepth of the returned stack.

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


# This function is used to append a stack of empty frames before and after the input stack.
# imp is the input stack, frames_before determines the number of frames to be appended in front,
# frames_after determines the number of frames to be appended at the end.
def concatenatestack(imp, frames_before, frames_after):
    cal = imp.getCalibration()
    imp_c1, imp_c2 = ChannelSplitter().split(imp)

    # IJ.log("""in concatenatestack(): frames_before: {}, frames_after: {}
    #        """.format(frames_before, frames_after))

    # If frames_before is 0, skip this step to prevent creation of an empty image
    # Also, split channels for correct concatenation in following step.
    if frames_before != 0:
        before = emptystack(imp, frames_before)
        before.setCalibration(cal)
        before_c1, before_c2 = ChannelSplitter().split(before)

    # If frames_after is 0, skip this step to prevent creation of an empty image.
    # Also, split channels for correct concatenation in following step.
    if frames_after != 0:
        after = emptystack(imp, frames_after)
        after.setCalibration(cal)
        after_c1, after_c2 = ChannelSplitter().split(after)

    # Concatenate existing stacks and merge channels back to one file.
    # Start with the condition when emptystack() has to be appended before and after imp.
    if frames_before != 0 and frames_after != 0:
        # IJ.log ("In concatenatestack(): reached frames_before != 0 & frames_after != 0")
        concat_c1 = Concatenator().run(before_c1, imp_c1, after_c1)
        concat_c2 = Concatenator().run(before_c2, imp_c2, after_c2)
    # Following the condition when emptystack() has to be appended after imp alone.
    elif frames_before == 0 and frames_after != 0:
        # IJ.log ("In concatenatestack(): reached frames_before == 0 & frames_after != 0")
        concat_c1 = Concatenator().run(imp_c1, after_c1)
        concat_c2 = Concatenator().run(imp_c2, after_c2)
    # Following the condition when emptystack() has to be appended before imp alone.
    elif frames_before != 0 and frames_after == 0:
        # IJ.log ("In concatenatestack(): reached frames_before != 0 & frames_after == 0")
        concat_c1 = Concatenator().run(before_c1, imp_c1)
        concat_c2 = Concatenator().run(before_c1, imp_c1)
    else:
        IJ.log("In concatenatestack(): reached else")
        return False

    # Now re-merge the channels and return the concatenated hyperstack.
    concat_list = [concat_c1, concat_c2]
    concat = RGBStackMerge().mergeHyperstacks(concat_list, False)  # boolean keep
    return concat


# Simple function making a montage of the image hyperstack passed as argument
def montage(imp):
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()
    ch1, ch2 = ChannelSplitter().split(imp)
    ch1_mont = MontageMaker().makeMontage2(ch1,
                                           nFrames,  # int columns
                                           nSlices,  # int rows
                                           1.00,  # double scale
                                           1,  # int first
                                           nFrames,  # int last
                                           1,  # int inc
                                           0,  # int borderWidth
                                           False)  # boolean labels)
    ch2_mont = MontageMaker().makeMontage2(ch2,
                                           nFrames,  # int columns
                                           nSlices,  # int rows
                                           1.00,  # double scale
                                           1,  # int first
                                           nFrames,  # int last
                                           1,  # int inc
                                           0,  # int borderWidth
                                           False)  # boolean labels)

    # Now re-merge the channels and return the montage.
    mont_list = [ch1_mont, ch2_mont]
    mont = RGBStackMerge().mergeChannels(mont_list, False)  # boolean keep
    return mont


def chunks(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


def _readdirfiles(directory):
    dir = os.listdir(directory)
    dirfiles = []

    for file in dir:
        if file.endswith('.tif') or file.endswith('tiff'):
            path = os.path.join(directory, file)
            stack = ImagePlus(path)
            stack = HyperStackConverter().toHyperStack(stack,
                                                       2,  # channels
                                                       1,  # slices
                                                       stack.getNFrames())  # frames
            dirfiles.append(stack)

    return dirfiles


def _listsplitchannels(collection):
    coll_c1 = []
    coll_c2 = []

    for stack in collection:
        c1, c2 = ChannelSplitter().split(stack)
        coll_c1.append(c1.getImageStack())
        coll_c2.append(c2.getImageStack())

    return coll_c1, coll_c2


def _horcombine(imp_collection):
    comb = imp_collection[0]

    for imp in imp_collection:
        if imp != imp_collection[0]:
            comb = StackCombiner().combineHorizontally(comb, imp)

    return comb


def _vercombine(imp_collection):
    comb = imp_collection[0]

    for imp in imp_collection:
        if imp != imp_collection[0]:
            comb = StackCombiner().combineVertically(comb, imp)

    return comb


# Only handles input files with 2 channels
def combinestacks(directory, x_width=5):
    IJ.log("Combining stacks...")
    files = _readdirfiles(directory)
    groups = chunks(files, x_width)

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
    results_table = opencsv()
    imp = WindowManager.getCurrentImage()

    croproi(imp, results_table,
            outdir=outdir, subdirs=subdirs,
            trackindex="TRACK_INDEX",
            trackduration="TRACK_DURATION",
            trackid="TRACK_ID",
            trackxlocation="TRACK_X_LOCATION",
            trackylocation="TRACK_Y_LOCATION",
            trackstart="TRACK_START",
            trackstop="TRACK_STOP",
            add_empty_before=False, add_empty_after=True,
            make_montage=True, roi_x=150, roi_y=150)

    # Combine all output stacks into one movie.
    IJ.log(subdirs[0])
    combinestacks(subdirs[0])


# Execute main()
main()
