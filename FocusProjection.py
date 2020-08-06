import ij.IJ as IJ
import ij.ImagePlus as ImagePlus
import ij.ImageStack as ImageStack
import ij.measure.ResultsTable as ResultsTable
import ij.measure.Measurements as Measurements
import ij.process.FloatProcessor as FloatProcessor
import ij.process.ImageProcessor as ImageProcessor
import ij.plugin.ImageCalculator as ImageCalculator
import ij.plugin.ChannelSplitter as ChannelSplitter
import ij.plugin.HyperStackConverter as HyperStackConverter
import ij.plugin.ZProjector as ZProjector
import ij.plugin.filter.ParticleAnalyzer as ParticleAnalyzer
import os
import ast
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


def maxfilter(floatIm, kernalSize=11):


    def _kernalmax(floatIm, X, Y, kernalX, kernalY):
        
        # Define image dimensions and kernal shape.
        pixels_ = floatIm.getPixels()
        width_ = int(floatIm.getWidth())
        height_ = int(floatIm.getHeight())
        halfX = int(kernalX / 2)
        halfY = int(kernalY / 2)
        startX = int(X-halfX)
        startY = int(Y-halfY)
        if (startX < 0):
            startX = 0
        if (startY < 0):
            startY = 0
        endX = X+halfX
        endY = Y+halfY
        if (endX > width_):
            endX = width_
        if (endY > height_):
            endY = height_
        
        # Loop through y coordinates, shift kernal for every pixel.
        maxPx = 0
        
        for y in range(startY, endY):

            offset_ = width_ * y
        
            for x in range(startX, endX):

                j = offset_ + x
                if pixels_[j] > maxPx:
                    maxPx = pixels_[j]

        return maxPx


    # Define input image dimensions.
    width = floatIm.getWidth()
    height = floatIm.getHeight()
    ndim = width * height
    # pixels = floatIm.getPixels()
    # pixIn = [pixels[i] for i in range(len(pixels))]

    # Initiate output stack with same XY dimensions as input stack.
    pixOut = [0] * ndim

    # Calculate Sobel transform of input image.
    procIm = floatIm.convertToByteProcessor(True)
    
    # procIm = procIm.medianFilter()
    # procIm = procIm.smooth()
    # procIm = procIm.findEdges()

    # Loop through pixels in y dimension.
    for row in range(height-1):

        offset = width * row

        # Within every y dimension, loop through pixels in x dimension.
        for column in range(width-1):

            # Retrieve maximum within kernel around pixel in sobel filtered image.
            # Set pixel value in output to max of kernel in sobel image.
            i = offset + column
            pixOut[i] = _kernalmax(procIm, column, row, kernalSize, kernalSize)

    # Return 
    floatOut = FloatProcessor(width, height, pixOut)
    return floatOut


def imptofloat(imp):
    
    width, height, nChannels, nSlices, nFrames = imp.getDimensions()
    pix = imp.getProcessor().getPixels()
    pixlist = [pix[i] for i in range(len(pix))]
    # IJ.log("{}\n{}\n{}".format(pix, pix[1], pixlist))

    # if min(pixlist) < 0:
    #     pixlist = [pixlist[i] + min(pixlist) for i in range(len(pixlist))]

    # pixlist = [(pixlist[i]/max(pixlist)) for i in range(len(pixlist))]

    fp = FloatProcessor(width, height, pixlist)

    return fp


def depthmap(stack): 
    # Takes a single channel z stack.
    width = stack.getWidth()
    height = stack.getHeight()

    # Loop through slices in stack.
    size = stack.getSize()
    outstack = ImageStack()

    IJ.log("size: {}".format(size))

    for z in range(1, size): 

        # Calculate maxfilter.
        imslice = stack.getPixels(z)
        imslice = [i for i in imslice]
        imslice = FloatProcessor(width, height, imslice)
        imslice = maxfilter(imslice)
        outstack.addSlice(imslice)
        IJ.showProgress(1.0*z/size)

    # Return output stack.
    return outstack


def projectfocus(instack, depthstack):

    # Initialize variables.
    width = instack.getWidth()
    height = instack.getHeight()
    nSlices = instack.getSize()
    dest_pixels = [0] * width * height

    # Loop through y coordinates.
    for y in range(height):

        offset = y*width

        # Loop through x coordinates
        for x in range(width):

            i = offset + x
            maxpx = 0.0
            maxslice = 1

            # Loop through z stack.
            for z in range(1, nSlices):

                # Find maximum pixel value
                current_pixels = depthstack.getPixels(z)
                current_pix = current_pixels[i]
                
                if current_pix > maxpx:
                    maxslice = z
                    maxpx = current_pix
            
            origin_pixels = instack.getPixels(maxslice)
            # origin_pixels = [((i+min(origin_pixels))/max(origin_pixels))*255 for i in origin_pixels]# Need to get rid of negative pixels!
            dest_pixels[i] = origin_pixels[i]

    output = FloatProcessor(width, height, dest_pixels)
    return output


def main():
    # Import files.
    imp = IJ.openImage("http://imagej.nih.gov/ij/images/confocal-series.zip")

    # Retrieve float image.
    fp = imptofloat(imp)
    IJ.log("{}\n{}".format(fp, fp.medianFilter()))

    # Perform focus projection.
    stack = maxfilter(fp, kernalSize=11)

    # Generate some output.
    IJ.log("{}\n{}".format(fp, stack))
    out = ImagePlus("filter", stack)
    out.show()

    channels = ChannelSplitter().split(imp)
    channel1 = channels[0].getImageStack()
    depth = depthmap(channel1)
    test = ImagePlus("test", depth)
    test.show()

    final = projectfocus(channel1, depth)
    final = ImagePlus("final", final)
    final.show()

    # Save file.

    # imp = ImagePlus("my new image", FloatProcessor(512, 512))
    
    
    


main()
