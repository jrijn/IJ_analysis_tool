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
import math


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


# TODO: finish this idea.
def checkcal(imp):
    def setupDialog(imp):

        gd = GenericDialog("Collective migration buddy options")
        gd.addMessage("Collective migration buddy 2.0, you are analyzing: " + imp.getTitle())
        calibration = imp.getCalibration()

        if (calibration.frameInterval > 0):
            default_interval = calibration.frameInterval
            default_timeunit = calibration.getTimeUnit()

        else:
            default_interval = 8
            default_timeunit = "min"

        gd.addNumericField("Frame interval:", default_interval, 2)  # show 2 decimals
        gd.addCheckbox("Do you want to use a gliding window?", True)
        gd.addCheckbox("Project hyperStack? (defaluts to projecting current channel only)", False)
        gd.addStringField("time unit", default_timeunit, 3)
        gd.addSlider("Start compacting at frame:", 1, imp.getNFrames(), 1)
        gd.addSlider("Stop compacting at frame:", 1, imp.getNFrames(), imp.getNFrames())
        gd.addNumericField("Number of frames to project in to one:", 3, 0)  # show 0 decimals

        gd.addChoice('Method to use for frame projection:', methods_as_strings, methods_as_strings[5])

        gd.showDialog()

        if gd.wasCanceled():
            IJ.log("User canceled dialog!")
            return

        return gd

    calibration = imp.getCalibration()
    frame_interval = 1
    pixel_width = calibration.pixelWidth
    pixel_height = calibration.pixelHeight
    if (calibration.frameInterval > 0):
        frame_interval = calibration.frameInterval


def croproi(imp, tracks, outdir, trackindex="TRACK_INDEX",
            trackx="TRACK_X_LOCATION", tracky="TRACK_Y_LOCATION",
            trackstart="TRACK_START", trackstop="TRACK_STOP",
            roi_x=150, roi_y=150):
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

        # And then crop (duplicate, actually) this ROI for the track's time duration.
        IJ.log("Cropping image with TRACK_INDEX: {}/{}".format(i_id+1, int(len(tracks))))
        # Duplicator().run(firstC, lastC, firstZ, lastZ, firstT, lastT)
        imp2 = Duplicator().run(imp, 1, nChannels, 1, nSlices, i_start, i_stop)  

        # Save the substack in the output directory
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(i_id))
        IJ.saveAs(imp2, "Tiff", outfile)


def croppoints(imp, spots, outdir, roi_x=150, roi_y=150,
               trackid="TRACK_ID", trackxlocation="POSITION_X", trackylocation="POSITION_Y", tracktlocation="FRAME"):
    """Function to follow and crop the individual spots within a trackmate "Spots statistics.csv" file.

    Args:
        imp (ImagePlus()): An ImagePlus() stack.
        spots (getresults()): The output of the getresults() function.
        outdir (path): The output directory path.
        roi_x (int, optional): ROI width (pixels). Defaults to 150.
        roi_y (int, optional): ROI height (pixels). Defaults to 150.
        trackid (str, optional): Column name of Track identifiers. Defaults to "TRACK_ID".
        trackxlocation (str, optional): Column name of spot x location. Defaults to "POSITION_X".
        trackylocation (str, optional): Column name of spot y location. Defaults to "POSITION_Y".
        tracktlocation (str, optional): Column name of spot time location. Defaults to "FRAME".
    """

    def _cropSingleTrack(ispots):
        outstack = ImageStack()

        for j in ispots:

            # Extract all needed row values.
            j_id = int(j[trackid])
            j_x = int(j[trackxlocation] * 5.988) # TODO fix for calibration.
            j_y = int(j[trackylocation] * 5.988) # TODO fix for calibration.
            j_t = int(j[tracktlocation]) # TODO fix for calibration.

            # Now set an ROI according to the track's xy position in the hyperstack.
            imp.setRoi(j_x, j_y, roi_x, roi_y)  # upper left x, upper left y, roi x dimension, roi y dimension

            # Set the correct time position in the stack.
            imp.setPosition(1, 1, j_t)

            # And crop the ROI on the corresponding timepoint.
            imp2 = Duplicator().run(imp, 1, dims[2], 1, dims[3], j_t, j_t)  # firstC, lastC, firstZ, lastZ, firstT, lastT

            # Append this frame to the tracks output stack.
            imp2 = imp2.getProcessor()
            out.addSlice("slice", imp2)
        
        return outstack


    # START OF MAIN FUNCTION.
    # Store the stack dimensions.
    dims = imp.getDimensions() # width, height, nChannels, nSlices, nFrames

    # Add a black frame around the stack to ensure the cropped roi's are never out of view.
    expand_x = dims[0] + roi_x
    expand_y = dims[1] + roi_y
    IJ.run(imp, "Canvas Size...", "width={} height={} position=Center zero".format(expand_x, expand_y))

    # Retrieve all unique track ids. This is what we loop through.
    track_ids = set([ track[trackid] for track in spots ])

    # 1: ----- MAIN LOOP -----
    # This loop loops through the unique set of TRACK_IDs from the results table.
    for i in track_ids:
        
        # Extract all spots (rows) with TRACK_ID == i.
        trackspots = [ spot for spot in spots if spot[trackid] == i ]
        IJ.log ("TRACK_ID: {}/{}".format(i, len(trackspots))) # Some feedback

        # Crop the spots of the current TRACK_ID.
        out = _cropSingleTrack(trackspots)

        # Save the substack in the output directory
        out = ImagePlus('tracked_point', out)
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(int(i)))
        IJ.saveAs(out, "Tiff", outfile)


# The main loop, call wanted functions and change parameters.
def main():

    # Get the wanted output directory and prepare subdirectories for output.
    outdir = IJ.getDirectory("output directory")

    # Open the 'Track statistics.csv' input file and format as getresults() dictionary.
    rt = opencsv()
    rt = getresults(rt)

    # Retrieve the current image as input (source) image.
    imp = WindowManager.getCurrentImage()

    # Run the main crop function on the source image.
    croppoints(imp, spots=rt, outdir=outdir, roi_x=150, roi_y=150)

    # Combine all output stacks into one movie.
    # combinestacks(outdir, height=8)


# Execute main()
main()
