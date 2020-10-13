import ij.IJ as IJ
import ij.io.Opener as Opener
import ij.ImagePlus as ImagePlus
import ij.plugin.StackWriter as StackWriter
import ij.plugin.ChannelSplitter as ChannelSplitter
import os


def main():
    indir = IJ.getDirectory("input directory")
    outdir = IJ.getDirectory("output directory")
    files = sorted(os.listdir(indir))
    # IJ.log("files: {}".format(files))

    # montages = []
    for imfile in files:

    	IJ.log("File: {}/{}".format(files.index(imfile)+1, len(files)))

        if imfile.endswith(".tif"):
            imp = Opener().openImage(indir, imfile)
            channels = ChannelSplitter().split(imp)
            name = outdir + imfile + "_t001_c001.tif"
            IJ.run(channels[0], "Image Sequence... ", "format=TIFF save={}".format(name))

	
main()
IJ.log("--- Finished ---")