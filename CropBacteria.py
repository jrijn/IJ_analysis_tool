from ij.plugin import Duplicator, Concatenator, ChannelSplitter, RGBStackMerge, StackCombiner, MontageMaker, \
    StackCombiner, HyperStackConverter
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij.measure import ResultsTable as ResultsTable
import math
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
        res = ResultsTable.open(csv)
        return res
    except:
        IJ.log("Oops, the .csv file could not open")


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


# TODO: There's a lot going on, might want to try and split this up in separate functions.
# TODO: Clean up the mess.
def croppoints(imp, results_table, outdir, roi_x=150, roi_y=150,
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

    # Get the calibration of the input image and store the pixel dimensions and frame interval.
    calibration = imp.getCalibration()
    frame_interval = 1
    pixel_width = calibration.pixelWidth
    pixel_height = calibration.pixelHeight
    if (calibration.frameInterval > 0):
        frame_interval = calibration.frameInterval

    # Store the stack dimensions.
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()
    IJ.log("Original image dimensions:\n"
           "width: {}\nheight:{}\nchannels: {}\nslices: {}\nframes: {}".format(width, height, nChannels, nSlices,
                                                                               nFrames))

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
    overlay_out = ImageStack()

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
    for i in tracks:
        out = ImageStack()
        out_list = []

        if isinstance(i, int):
            i = int(i)
            IJ.log("iteration: {}, nrows = {}".format(i, nrows))

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
