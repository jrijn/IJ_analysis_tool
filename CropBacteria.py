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



# TODO: There's a lot going on, might want to try and split this up in separate functions.
# TODO: Clean up the mess.
def croppoints(imp, tracks, outdir, roi_x=150, roi_y=150,
               trackid="TRACK_ID", trackxlocation="POSITION_X", trackylocation="POSITION_Y",
               tracktlocation="FRAME"):
    """Function cropping ROIs from an ImagePlus stack based on a ResultsTable object.

    This function crops square ROIs from a hyperstack based on locations defined in the ResultsTable.
    The results table should be the Spots in 'tracks statistics.csv'.

    Args:
        imp: An ImagePlus hyperstack (timelapse).
        results_table: A ResultsTable object with the proper column names.
        outdir: The primary output directory.
        roi_x: Width of the ROI.
        roi_y: Height of the ROI.
        trackid:
        trackxlocation:
        trackylocation:
        tracktlocation:
    """

    # # Get the calibration of the input image and store the pixel dimensions and frame interval.
    # calibration = imp.getCalibration()
    # frame_interval = 1
    # pixel_width = calibration.pixelWidth
    # pixel_height = calibration.pixelHeight
    # if (calibration.frameInterval > 0):
    #     frame_interval = calibration.frameInterval

    # Store the stack dimensions.
    dims = imp.getDimensions()
    # IJ.log("Original image dimensions:\n"
    #        "width: {}\nheight:{}\nchannels: {}\nslices: {}\nframes: {}".format(width, height, nChannels, nSlices,
                                                                               nFrames))

    # Add a black frame around the stack to ensure the cropped roi's are never out of view.
    expand_x = dims[0] + roi_x
    expand_y = dims[1] + roi_y
    IJ.run(imp, "Canvas Size...", "width={} height={} position=Center zero".format(expand_x, expand_y))

    # # Extract the column index of 'TRACK_ID' from the csv file.
    # # The column name cannot be used directly to extract the column values.
    # # The 'TRACK_ID' column is used to define individual tracks. We'll loop through these.
    # track_id = results_table.getColumnIndex(trackid)
    # track_list = results_table.getColumn(track_id).tolist()
    # tracks = set(track_list)  # Yields a set of the individual TRACK_IDs from the list of points.
    # tracks = list(tracks)  # Since we might want to subset the TRACK_IDs later on, convert it back to a list.
    # nrows = results_table.size()
    # overlay_out = ImageStack()
    track_ids = set([ track[trackid] for track in tracks ])

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
    for i in track_ids:
        # out = ImageStack()
        # out_list = []
        # TODO: Finish here! This can be much easier, as in CropInvasions.py.





        # 2: ----- FIRST SUBLOOP -----
        # Since ImageJ has no sensible data wrangling package, this loop goes through the rows of the results table,
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
                j_t = int(results_table.getValue(tracktlocation, j))
                IJ.log("X: {}, Y: {}, T: {}".format(j_x, j_y, j_t))

                # Now set an ROI according to the track's xy position in the hyperstack.
                imp.setRoi(j_x, j_y,  # upper left x, upper left y
                           roi_x, roi_y)  # roi x dimension, roi y dimension

                # # Create an empty image for the track overlays.
                # overlay = IJ.createHyperStack("track_overlay",
                #                               width + roi_x,  # width
                #                               height + roi_y,  # height
                #                               1,  # channels
                #                               1,  # slices
                #                               1,  # frames
                #                               24)
                # # WindowManager.setTempCurrentImage(overlay)
                # # ij.invert()
                #
                # # Copy to the overlay image.
                imp.setPosition(1, 1, j_t)
                # imp.copy()
                # overlay.setRoi(j_x, j_y,  # upper left x, upper left y
                #                roi_x, roi_y)  # roi x dimension, roi y dimension
                # overlay.paste()
                # # overlay.deleteRoi()
                # # overlay.show()
                # # outfile = os.path.join(output1, "TRACK_ID_{}_{}.tif".format(int(i), j_t))
                # # IJ.saveAs(overlay, "Tiff", outfile)
                # overlay = overlay.getProcessor()
                # overlay_out.addSlice("track_overlay", overlay)

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

        # Save the substack in the output directory
        IJ.log("Save substack {}...".format(int(i)))
        out = ImagePlus('tracked_point', out)
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(int(i)))
        IJ.saveAs(out, "Tiff", outfile)

    # overlay_out = ImagePlus("track_overlay", overlay_out)
    # overlay_out.show()
    return


# The main loop, call wanted functions and change parameters.
def main():
    # Get the wanted output directory.
    outdir = IJ.getDirectory("output directory")

    # Check calibration

    # Open the 'Spots in tracks statistics.csv' input file and run main crop function.
    results_table = opencsv()
    imp = WindowManager.getCurrentImage()

    croppoints(imp, results_table,
               outdir=outdir,
               trackid="TRACK_ID",
               trackxlocation="POSITION_X",
               trackylocation="POSITION_Y",
               tracktlocation="FRAME",
               roi_x=150, roi_y=150)


# Execute main()
main()
