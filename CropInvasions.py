import ij.IJ as IJ
import ij.io.Opener as Opener
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
import os


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

    This makes it much easier to iterate through the rows of a ResultsTable object 
    from within ImageJ.

    Args:
        rt (ij.measure.ResultsTable): An Imagej ResultsTable object.

    Returns:
        list: A list of ResultsTable rows, represented as dictionary with column names as keys.
        
        for example:
            [
            {'column1' : 'value', 'column2' : 'value', ...},
            {'column1' : 'value', 'column2' : 'value', ...},
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


def croproi(imp, tracks, outdir, trackindex="TRACK_INDEX",
            trackx="TRACK_X_LOCATION", tracky="TRACK_Y_LOCATION",
            trackstart="TRACK_START", trackstop="TRACK_STOP",
            roi_x=150, roi_y=150, minduration=None):
    """Function cropping ROIs from an ImagePlus stack based on a ResultsTable object.

    This function crops square ROIs from a hyperstack based on locations defined in the ResultsTable.
    The ResultsTable should, however make sense. The following headings are required:

    "TRACK_INDEX", "TRACK_X_LOCATION", "TRACK_Y_LOCATION", "TRACK_START", "TRACK_STOP"

    Args:
        imp: An ImagePlus hyperstack (timelapse).
        tracks: A getresults(ResultsTable) object (from Track statistics.csv) with the proper column names.
        outdir: The primary output directory.
        trackindex: A unique track identifier. Defaults to "TRACK_INDEX"
        trackxlocation: Defaults to "TRACK_X_LOCATION".
        trackylocation: Defaults to "TRACK_Y_LOCATION".
        trackstart: Defaults to "TRACK_START".
        trackstop: Defaults to "TRACK_STOP".
        roi_x: Width of the ROI.
        roi_y: Height of the ROI.
        minduration (int): Set a minimum duration threshold. Defaults to 'None'.
    """

    # Loop through all the tracks, extract the track position, set an ROI and crop the hyperstack.
    for i in tracks:  # This loops through all tracks. Use a custom 'tracks[0:5]' to test and save time!

        # Extract all needed row values.
        i_id = int(i[trackindex])
        i_x = int(i[trackx] * 5.988) # TODO fix for calibration.
        i_y = int(i[tracky] * 5.988) # TODO fix for calibration.
        i_start = int(i[trackstart] / 15)
        i_stop = int(i[trackstop] / 15)

        # Now set an ROI according to the track's xy position in the hyperstack.
        imp.setRoi(i_x - roi_x / 2, i_y - roi_y / 2,  # upper left x, upper left y
                   roi_x, roi_y)  # roi x dimension, roi y dimension

        # Retrieve image dimensions.
        width, height, nChannels, nSlices, nFrames = imp.getDimensions()

        # Optionally set a minimum duration.
        i_duration = i_stop - i_start
        allowCrop = True
        if minduration != None: allowCrop = i_duration > minduration

        # And then crop (duplicate, actually) this ROI for the track's time duration.
        if allowCrop:
            IJ.log("Cropping image with TRACK_INDEX: {}/{}".format(i_id+1, int(len(tracks))))
            # Duplicator().run(firstC, lastC, firstZ, lastZ, firstT, lastT)
            imp2 = Duplicator().run(imp, 1, nChannels, 1, nSlices, i_start, i_stop)  

            # Save the substack in the output directory
            outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(i_id))
            IJ.saveAs(imp2, "Tiff", outfile)
        else: 
            IJ.log("Image with TRACK_INDEX: {}/{} does not meet minimum duration requirement.".format(i_id+1, int(len(tracks))))


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


def _horcombine(imp_collection):
    """Combine a list of stacks with the same dimensions horizontally.

    Args:
        imp_collection: A list of stacks.

    Returns:
        A horizontally combined stack of the input images.
    """
    comb = imp_collection[0]
    comb_channels = ChannelSplitter().split(comb)
    comb_channels = [ i.getImageStack() for i in comb_channels]


    for imp in imp_collection:

        if imp == imp_collection[0]:
            continue

        imp_channels = ChannelSplitter().split(imp)
        imp_channels = [ i.getImageStack() for i in imp_channels]
        comb_channels = [ StackCombiner().combineHorizontally(i, j) for i, j in zip(comb_channels, imp_channels) ]

    comb_channels = [ ImagePlus("C{}".format(i+1), channel) for i, channel in enumerate(comb_channels) ]
    impout = RGBStackMerge().mergeChannels(comb_channels, False)  # boolean keep
    return impout


def _vercombine(imp_collection):
    """Combine a list of stacks with the same dimensions vertically.

    Args:
        imp_collection: A list of stacks.

    Returns:
        A vertically combined stack of the input images.
    """
    comb = imp_collection[0]
    comb_channels = ChannelSplitter().split(comb)
    comb_channels = [ i.getImageStack() for i in comb_channels ]

    for imp in imp_collection:

        if imp == imp_collection[0]:
            continue

        imp_channels = ChannelSplitter().split(imp)
        imp_channels = [ i.getImageStack() for i in imp_channels]
        comb_channels = [ StackCombiner().combineVertically(i, j) for i, j in zip(comb_channels, imp_channels) ]

    comb_channels = [ ImagePlus("C{}".format(i+1), channel) for i, channel in enumerate(comb_channels) ]
    impout = RGBStackMerge().mergeChannels(comb_channels, False)  # boolean keep
    return impout


def combinestacks(directory, height=5):
    """Combine all tiff stacks in a directory to a panel.

    Args:
        directory: Path to a directory containing a collection of .tiff files.
        height: The height of the panel (integer). Defaults to 5. The width is spaces automatically.

    Returns:
        A combined stack of the input images.
    """

    IJ.log("\nCombining stacks...")
    files = [f for f in sorted(os.listdir(directory)) if os.path.isfile(os.path.join(directory, f))]
    IJ.log("Number of files: {}".format(len(files)))
    groups = chunks(files, height)

    horiz = []
    for group in groups:
        h = [ Opener().openImage(directory, imfile) for imfile in group ]
        h = _horcombine(h)
        # h.show()
        horiz.append(h)

    montage = _vercombine(horiz)
    montage.show()


# The main loop, call wanted functions.
def main():
    # Get the wanted output directory and prepare subdirectories for output.
    outdir = IJ.getDirectory("output directory")

    # Open the 'Track statistics.csv' input file and format as getresults() dictionary.
    rt = opencsv()
    rt = getresults(rt)

    # Retrieve the current image as input (source) image.
    imp = WindowManager.getCurrentImage()

    # Run the main crop function on the source image.
    croproi(imp, tracks=rt, outdir=outdir, roi_x=150, roi_y=150, minduration=6)

    # Combine all output stacks into one movie.
    combinestacks(outdir, height=8)


# Execute main()
main()
