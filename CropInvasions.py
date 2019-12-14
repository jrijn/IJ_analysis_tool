from ij.plugin import Duplicator, Concatenator, ChannelSplitter, RGBStackMerge, StackCombiner, MontageMaker, \
    StackCombiner, HyperStackConverter
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij.measure import ResultsTable as ResultsTable
# from ij.process import ImageProcessor as ip
# from ij.gui import GenericDialog, ImageWindow
import os

# Declare variables
global outdir
global dir_montage
global dir_empty


# Prepare the directory tree for the output files.
def preparedir():
    global outdir
    global dir_montage
    global dir_empty

    # First ask for an output directory and the location of the 'Track statistics.csv' Trackmate output.
    outdir = IJ.getDirectory("output directory")
    csv = IJ.getFilePath("Choose the Trackmate 'Track Statistics' results file")

    # Also create the output subdirectory paths.
    dir_montage = os.path.join(outdir, "montage")
    dir_empty = os.path.join(outdir, "with_empty_stacks")
    if not os.path.isdir(dir_montage):
        os.mkdir(dir_montage)
    if not os.path.isdir(dir_empty):
        os.mkdir(dir_empty)

    # Open the csv file and return it as ResultsTable object.
    try:
        res = ResultsTable.open(csv)
    except:
        IJ.log("Oops, 'Track statistics' file couldn't open")
    else:
        return res


# The function interpreting a .csv file and looping through the Trackmate tracks to extract cropped hyperstacks.
# There's a lot going on, might want to try and split this up in separate functions.
def croproi(imp, results_table, add_empty_before=False, add_empty_after=False,
            make_montage=False, roi_x=150, roi_y=150):
    global outdir
    global dir_empty
    global dir_montage

    # Extract the column index of 'TRACK_INDEX' from the csv file.
    # The column name cannot be used directly to extract the column values.
    # The 'TRACK_INDEX' is used to refer to the frame's row numbers, we'll loop through these.
    track_idx = results_table.getColumnIndex("TRACK_INDEX")
    tracks = results_table.getColumn(track_idx).tolist()
    duration_idx = results_table.getColumnIndex("TRACK_DURATION")
    duration = results_table.getColumn(duration_idx).tolist()
    IJ.log("[1] {} \n[2] {}\n[3] ".format(track_idx, tracks))

    # Now loop through all the tracks, extract the track position, set an ROI and crop the hyperstack!
    for i in tracks:  # This loops through all tracks. Use a custom 'range(0,1)' to test and save time!
        # Extract all needed row values.
        idx = int(i)
        i_id = int(results_table.getValue("TRACK_ID", idx))
        i_x = int(results_table.getValue("TRACK_X_LOCATION", idx) * 5.988)  # fix for calibration
        i_y = int(results_table.getValue("TRACK_Y_LOCATION", idx) * 5.988)  # fix for calibration
        i_start = int(results_table.getValue("TRACK_START", idx) / 15)
        i_stop = int(results_table.getValue("TRACK_STOP", idx) / 15)
        i_duration = int(results_table.getValue("TRACK_DURATION", idx) / 15)
        i_fill_duration = int(max(duration) / 15 - i_duration)
        width, height, nChannels, nSlices, nFrames = imp.getDimensions()

        # Quick sanity check, and this provides some output to be sure the script is still running.
        # IJ.log("In readcsv(): width: {}, height: {}, nChannels: {}, nSlices: {}, nFrames: {}"
        #        "x: {}, y {}, start {}, stop {}"
        #        "Cropping image...".format(width, height, nChannels, nSlices, nFrames, i_x, i_y, i_start, i_stop))

        # Now set an ROI according to the track's xy position in the hyperstack.
        imp.setRoi(i_x - roi_x / 2, i_y - roi_y / 2,  # upper left x, upper left y
                   roi_x, roi_y)  # roi x dimension, roi y dimension

        # And then crop (duplicate, actually) this ROI for the track's time duration.
        IJ.log("\nCropping image with TRACK_ID: {}".format(i_id))
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
                outfile3 = os.path.join(dir_empty, "TRACK_ID_{}.tif".format(i_id))
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
                outfile3 = os.path.join(dir_empty, "TRACK_ID_{}.tif".format(i_id))
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
                outfile3 = os.path.join(dir_empty, "TRACK_ID_{}.tif".format(i_id))
                IJ.saveAs(imp_empty, "Tiff", outfile3)
            else:
                # Let's us know if this concatenation fails.
                IJ.log("Concatenation failed at TRACK_ID: {}".format(i_id))

        # Save the stack montage
        if make_montage:
            IJ.log("Making montage...")
            mont = montage(imp_empty)
            outfile2 = os.path.join(dir_montage, "TRACK_ID_{}.tif".format(i_id))
            IJ.saveAs(mont, "Tiff", outfile2)


# This function creates an empty stack with black images, with the same dimensions of input image 'imp'.
# The argument inframes allows one to set the number of frames the stack should have. This defaults to the
# input frame depth through an if statement.
def emptystack(imp, inframes=0):
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
        IJ.log(str(stack))
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
    imp = WindowManager.getCurrentImage()
    # results = preparedir()
    # croproi(imp, results, add_empty_before=False, add_empty_after=True,
    #         make_montage=True, roi_x=150, roi_y=150)
    testdir = IJ.getDirectory("output directory")
    combinestacks(testdir)


# Excecute main()
main()
