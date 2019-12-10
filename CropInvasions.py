#from ij.plugin import ZProjector, Duplicator, HyperStackConverter, ImageCalculator
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij.measure import ResultsTable as ResultsTable
#from ij.gui import GenericDialog, ImageWindow
import os

# Read the CSV file into an

def imgCalibration():

def readCSV():
    csv = IJ.getFilePath("Choose the Trackmate 'Track Statistics' results file")
    res = ResultsTable.open(csv)
    track_idx = res.getColumnIndex("TRACK_INDEX")
    tracks = res.getColumn(track_idx).tolist()
    IJ.log("[1] {} \n[2] {}\n[3] ".format(track_idx, tracks))
    for i in tracks:
    	idx = int(i)
        i_id = int(res.getValue("TRACK_ID", idx))
    	i_x = int(res.getValue("TRACK_X_LOCATION", idx) * 5.988)
        i_y = int(res.getValue("TRACK_Y_LOCATION", idx) * 5.988)
        i_start = int(res.getValue("TRACK_START", idx) / 15)
        i_stop = int(res.getValue("TRACK_STOP", idx) / 15)
    	IJ.log("x: {}, y {}, start {}, stop {}\nCropping image...".format(i_x, i_y, i_start, i_stop))
        imp.setRoi(i_x - 75,
        		   i_y - 75,
        		   150, 
        		   150)
        imp2 = imp.crop("{}-{}".format(i_start, i_stop))
        #imp2.show()
        IJ.log("Save substack with TRACK_ID: {}\n".format(i_id))
        outfile = os.path.join(outdir, "TRACK_ID_{}.tif".format(i_id)
)
        IJ.saveAs(imp2, "Tiff", outfile)

def cropRoi(trackidxs):
	return 

def main():
    global outdir
    outdir = IJ.getDirectory("output directory")
    global imp 
    imp = WindowManager.getCurrentImage()
    readCSV()

main()