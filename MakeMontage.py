import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
import ij.ImageStack as ImageStack
import ij.WindowManager as wm
import ij.io.Opener as Opener
import ij.plugin.ChannelSplitter as ChannelSplitter
import ij.plugin.RGBStackMerge as RGBStackMerge
import ij.plugin.MontageMaker as MontageMaker
import os
import math


def readdirfiles(directory):
    """Import tiff files from a directory.
    This function reads all .tiff files from a directory and it's subdirectories and returns them as a list of
    hyperstacks.

    Args:
        directory: The path to a directory containing the tiff files.

    Returns:
        A list of filepaths.
    """
    # Get the list of all files in directory tree at given path
    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(directory):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    return listOfFiles

def listProduct(inlist):
    """Calculates the product of all elements in a list.

    Args:
        inlist (list): A list of numbers.

    Returns:
        int or double: The product of all list elements.
    """    
    product = 1

    for element in inlist:
        if isinstance(element, (int, float)):
            product = element * product

    return product


def makemontage(imp, hsize=5, vsize=5, increment = 1):
    """Makes a montage of a multichannel ImagePlus object.

    Args:
        imp (ImagePlus): An ImagePlus object.
        hsize (int, optional): Size of the horizontal axis. Defaults to 5.
        vsize (int, optional): Size of the vertical axis. Defaults to 5.
        increment (int, optional): The increment between images. Allows for dropping of e.g. every second frame. Defaults to 1.

    Returns:
        ImagePlus: The montage as ImagePlus object.
    """    
    gridsize = hsize * vsize

    def _channelmontage(_imp):  
        """Makes a montage of a single channel ImagePlus object.

        Args:
            _imp (ImagePlus): A single channel ImagePlus object.

        Returns:
            ImagePlus: A montage of the one input channel.
        """        
        dims = _imp.getDimensions() # width, height, nChannels, nSlices, nFrames
        frames = listProduct(dims[2:])
        if frames > gridsize: frames = gridsize
        _montage = MontageMaker().makeMontage2(_imp, hsize, vsize, 1.00, 1, frames, increment, 0, True)
        return _montage


    name = imp.getTitle()   
    channels = ChannelSplitter().split(imp)
    montages = [ _channelmontage(channel) for channel in channels ]
    montage = RGBStackMerge().mergeChannels(montages, False)
    montage.setTitle(name)
    return montage


def _saveimage(imp, outdir):
    """Saves ImagePlus as .jpg.

    Args:
        imp (ImagePlus): An ImagePlus object.
        outdir (dirpath): The output directory.
    """        
    name = imp.getTitle()
    outfile = os.path.join(outdir, "{}.jpg".format(name))
    IJ.saveAs(imp, "Tiff", outfile)


def main():
    indir = IJ.getDirectory("input directory")
    outdir = IJ.getDirectory("output directory")
    files = sorted(os.listdir(indir))
    IJ.log("files: {}".format(files))

    montages = []
    for imfile in files:

    	IJ.log("File: {}/{}".format(files.index(imfile)+1, len(files)))
        
        if imfile.endswith(".tif"):
            imp = Opener().openImage(indir, imfile)
            montage = makemontage(imp, hsize=6, vsize=6, increment=2)
            _saveimage(montage, outdir)

#	IJ.log("Finished")

main()