from ij.plugin import Duplicator, Concatenator, ChannelSplitter, RGBStackMerge, StackCombiner, MontageMaker, \
    StackCombiner, HyperStackConverter
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij.measure import ResultsTable as ResultsTable
import math
import os


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
        IJ.log("Oops, the .csv file could not open")


# TODO: There's a lot going on, might want to try and split this up in separate functions.
# TODO: Clean up the mess.
def croppoints(imp, results_table, outdir, subdirs, roi_x=150, roi_y=150,
               trackindex="TRACK_INDEX", trackduration="TRACK_DURATION", trackid="TRACK_ID",
               trackxlocation="TRACK_X_LOCATION", trackylocation="TRACK_Y_LOCATION", trackstart="TRACK_START",
               trackstop="TRACK_STOP", add_empty_before=False, add_empty_after=False, make_montage=False):
    """Function cropping ROIs from an ImagePlus stack based on a ResultsTable object.

    This function crops square ROIs from a hyperstack based on locations defined in the ResultsTable.
    The ResultsTable should, however make sense. The following headings are required:

    "TRACK_INDEX", "TRACK_DURATION", "TRACK_ID", "TRACK_X_LOCATION", "TRACK_Y_LOCATION", "TRACK_START", "TRACK_STOP"

    Args:
        imp: An ImagePlus hyperstack (timelapse).
        results_table: A ResultsTable object with the proper column names.
        outdir: The primary output directory.
        subdirs: A list of two paths for the output of this funcion. ([path_of_output1, path_of_output2])
        roi_x: Width of the ROI.
        roi_y: Height of the ROI.
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
    """

    output1 = subdirs[0]
    output2 = subdirs[1]

    # Get the calibration of the input image and store the pixel dimensions and frame interval.
    calibration = imp.getCalibration()
    frame_interval = 1
    pixel_width = calibration.pixelWidth
    pixel_height = calibration.pixelHeight
    if (calibration.frameInterval > 0):
        frame_interval = calibration.frameInterval

    # Store the stack dimensions.
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()

    # Create an empty image for the track overlays.
    overlay = IJ.createHyperStack("empty_stack",
                                  width + roi_x,  # width
                                  height + roi_y,  # height
                                  1,  # channels
                                  1,  # slices
                                  1,  # frames
                                  24)

    # Add a black frame around the stack to ensure the cropped roi's are never out of view.
    expand_x = width + roi_x
    expand_y = height + roi_y
    IJ.run(imp, "Canvas Size...", "width={} height={} position=Center zero".format(expand_x, expand_y))

    # Extract the column index of 'TRACK_ID' from the csv file.
    # The column name cannot be used directly to extract the column values.
    # The 'TRACK_ID' column is used to define individual tracks. We'll loop through these.
    track_id = results_table.getColumnIndex(trackid)
    track_list = results_table.getColumn(track_id).tolist()
    tracks = set(track_list)  # Yields a set of the individual TRACK_IDs from the list of points.
    tracks = list(tracks)  # Since we might want to subset the TRACK_IDs later on, convert it back to a list.
    nrows = results_table.size()

    # Generate some useful output for debugging
    IJ.log(
        """
        TRACK_ID column: {}
        Individual TRACK_IDs {}
        Calibration X: {}, Y: {}, T:{} 
        """.format(track_id, tracks, pixel_width, pixel_height, frame_interval)
    )

    # 1: ----- MAIN LOOP -----
    # This loop loops through the unique set of TRACK_IDs from the results table.
    for i in tracks[0:4]:
        out = ImageStack()
        out_list = []

        if isinstance(i, int):
            i = int(i)
            IJ.log("iteration: {}, nrows = {}".format(i, nrows))

        # 2: ----- FIRST SUBLOOP -----
        # This loop loops through the rows of the results table,
        # and crops each point location for the current TRACK_ID.
        for j in range(0, nrows):

            j_id = results_table.getValue(trackid, j)
            # If the current point is not part of a track, move on to the next.
            if math.isnan(j_id):
                break
            j_id = int(j_id)

            # IJ.log("Track ID on current row = {}\nTrack ID in current loop = {}".format(j_id, i))
            if j_id == i:
                j_x = int(results_table.getValue(trackxlocation, j) / pixel_width)  # fix for calibration
                j_y = int(results_table.getValue(trackylocation, j) / pixel_height)  # fix for calibration
                j_t = int(results_table.getValue(trackstart, j) / frame_interval)
                # IJ.log("X: {}, Y: {}, T: {}".format(j_x, j_y, j_t))

                # Now set an ROI according to the track's xy position in the hyperstack.
                imp.setRoi(j_x, j_y,  # upper left x, upper left y
                           roi_x, roi_y)  # roi x dimension, roi y dimension

                # Copy to the overlay image.
                imp.setPosition(1, 1, j_t)
                imp.copy()
                overlay.setRoi(j_x, j_y,  # upper left x, upper left y
                               roi_x, roi_y)  # roi x dimension, roi y dimension
                overlay.paste()

                # Crop.
                imp2 = Duplicator().run(imp,
                                        1,  # firstC
                                        nChannels,  # lastC
                                        1,  # firstZ
                                        nSlices,  # lastZ
                                        j_t,  # firstT
                                        j_t)  # lastT
                # imp2.show()
                imp2 = imp2.getProcessor()
                out.addSlice("slice", imp2)

        # 3: ----- SECOND SUBLOOP -----
        # This loop appends some frames at the last location where the point disappeared.
        for k in range(1, 20):

            # If the current last frame is the last frame of the original stack, stop.
            # You can't append frames from the future!
            if j_t >= nFrames:
                break

            # Then add the extra frame to the end of the output stack.
            end = j_t + k
            imp2 = Duplicator().run(imp,
                                    1,  # firstC
                                    nChannels,  # lastC
                                    1,  # firstZ
                                    nSlices,  # lastZ
                                    end,  # firstT
                                    end)  # lastT
            imp2 = imp2.getProcessor()
            out.addSlice("slice", imp2)

        # Save the substack in the output directory
        overlay.show()
        IJ.log("Save substack {}...".format(int(i)))
        out = ImagePlus('tracked_point', out)
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(int(i)))
        IJ.saveAs(out, "Tiff", outfile)

    return


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
    imp_c1, imp_c2 = ChannelSplitter().split(imp)

    # If frames_before is 0, skip this step to prevent creation of an empty image
    # Also, split channels for correct concatenation in following step.
    if frames_before != 0:
        before = _emptystack(imp, frames_before)
        before.setCalibration(cal)
        before_c1, before_c2 = ChannelSplitter().split(before)

    # If frames_after is 0, skip this step to prevent creation of an empty image.
    # Also, split channels for correct concatenation in following step.
    if frames_after != 0:
        after = _emptystack(imp, frames_after)
        after.setCalibration(cal)
        after_c1, after_c2 = ChannelSplitter().split(after)

    # Concatenate existing stacks and merge channels back to one file.
    # Start with the condition when _emptystack() has to be appended before and after imp.
    if frames_before != 0 and frames_after != 0:
        # IJ.log ("In concatenatestack(): reached frames_before != 0 & frames_after != 0")
        concat_c1 = Concatenator().run(before_c1, imp_c1, after_c1)
        concat_c2 = Concatenator().run(before_c2, imp_c2, after_c2)
    # Following the condition when _emptystack() has to be appended after imp alone.
    elif frames_before == 0 and frames_after != 0:
        # IJ.log ("In concatenatestack(): reached frames_before == 0 & frames_after != 0")
        concat_c1 = Concatenator().run(imp_c1, after_c1)
        concat_c2 = Concatenator().run(imp_c2, after_c2)
    # Following the condition when _emptystack() has to be appended before imp alone.
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
    """Makes a montage of the input hyperstack.

    Simple function making a montage of the image hyperstack passed as argument.

    Args:
        imp: ImagePlus hyperstack object.

    Returns:
        An ImagePlus hyperstack object.
    """

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
            # TODO: something weird with input, frames and slices are switched.
            stack = HyperStackConverter().toHyperStack(stack,
                                                       1,  # channels
                                                       1,  # slices
                                                       stack.getNSlices())  # frames
            dirfiles.append(stack)

    return dirfiles


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
    files = _readdirfiles(directory, 1, 1)
    groups = chunks(files, height)
    IJ.log(str(groups))

    horiz = []
    for i in range(0, len(groups)):
        comb = _horcombine(groups[i])
        horiz.append(comb)

    for i in range(0, len(horiz)):
        c1, c2 = _listsplitchannels(horiz)
        comb = _vercombine(horiz)

    comb.show()


# The main loop, call wanted functions.
def main():
    # Get the wanted output directory and prepare subdirectories for output.
    outdir = IJ.getDirectory("output directory")
    subdirs = preparedir(outdir, dir1="with_empty_stacks", dir2="montage")

    # Open the 'Spots in tracks statistics.csv' input file and run main crop function.
    results_table = opencsv()
    imp = WindowManager.getCurrentImage()

    croppoints(imp, results_table,
               outdir=outdir, subdirs=subdirs,
               trackindex="TRACK_INDEX",
               trackduration="TRACK_DURATION",
               trackid="TRACK_ID",
               trackxlocation="POSITION_X",
               trackylocation="POSITION_Y",
               trackstart="POSITION_T",
               trackstop="TRACK_STOP",
               add_empty_before=False, add_empty_after=True,
               make_montage=False, roi_x=30, roi_y=30)

    # Combine all output stacks into one movie.
    # combinestacks(subdirs[0])


# Execute main()
main()
