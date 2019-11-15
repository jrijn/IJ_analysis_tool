##Honestly "borrowed" some of the code framework from Jens Eriksson's Collective Migration Buddy v2.0 (https://github.com/Oftatkofta/ImageJ-plugins)
##Jorik van Rijn, 2019, Uppsala University

from ij.plugin import ZProjector, Duplicator, HyperStackConverter, ImageCalculator
from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij import IJ as IJ
from ij.gui import GenericDialog
import math

def ColMigBud():

    def setupDialog(imp):

        gd = GenericDialog("Collective migration buddy options")
        gd.addMessage("Collective migration buddy 2.0, you are analyzing: "+imp.getTitle())
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
        gd.addStringField("time unit",default_timeunit, 3)
        gd.addSlider("Start compacting at frame:", 1, imp.getNFrames(), 1)
        gd.addSlider("Stop compacting at frame:", 1, imp.getNFrames(), imp.getNFrames())
        gd.addNumericField("Number of frames to project in to one:", 3, 0)  # show 0 decimals
        
        
        gd.addChoice('Method to use for frame projection:', methods_as_strings, methods_as_strings[5])
        
        gd.showDialog()  
          
        if gd.wasCanceled():  
            IJ.log("User canceled dialog!")  
            return

        return gd

    #Start by getting the active image window and get the current active channel and other stats
    imp = WindowManager.getCurrentImage()
    cal = imp.getCalibration()
    nSlices = 1 #TODO fix this in case you want to do Z-stacks
    title = imp.getTitle()
    current_channel = imp.getChannel()
    #zp = ZProjector(imp)

    #Make a dict containg method_name:const_fieled_value pairs for the projection methods
    methods_as_strings=['Average Intensity', 'Max Intensity', 'Min Intensity', 'Sum Slices', 'Standard Deviation', 'Median']
    methods_as_const=[ZProjector.AVG_METHOD, ZProjector.MAX_METHOD, ZProjector.MIN_METHOD, ZProjector.SUM_METHOD, ZProjector.SD_METHOD, ZProjector.MEDIAN_METHOD]
    medthod_dict=dict(zip(methods_as_strings, methods_as_const))

    # Run the setupDialog, read out and store the options
    gd=setupDialog(imp)
    frame_interval = gd.getNextNumber()
    time_unit = gd.getNextString()
    glidingFlag = gd.getNextBoolean()
    hyperstackFlag = gd.getNextBoolean()

    #Set the frame interval and unit, and store it in the ImagePlus calibration
    cal.frameInterval = frame_interval
    cal.setTimeUnit(time_unit)
    imp.setCalibration(cal)


    start_frame = int(gd.getNextNumber())
    stop_frame = int(gd.getNextNumber())

    #If a subset of the image is to be projected, these lines of code handle that
    if (start_frame > stop_frame):
        IJ.showMessage("Start frame > Stop frame, can't go backwards in time!")
        raise RuntimeException("Start frame > Stop frame!")

    if ((start_frame != 1) or (stop_frame != imp.getNFrames())):
        imp = Duplicator().run(imp, 1, nChannels, 1, nSlices, start_frame, stop_frame)
        
     
    no_frames_per_integral = int(gd.getNextNumber())

    #the doHyperstackProjection method can't project past the end of the stack
    if hyperstackFlag: 
        total_no_frames_to_project=imp.getNFrames()-no_frames_per_integral
    #the doProjection method can project past the end, it just adds black frames at the end
    #When not projecting hyperstacks, just copy the current active channel from the active image
    else:
        total_no_frames_to_project=imp.getNFrames()
        imp = Duplicator().run(imp, current_channel, current_channel, 1, nSlices, start_frame, stop_frame)

    #The Z-Projection magic happens here through a ZProjector object
    zp = ZProjector(imp)
    projection_method=gd.getNextChoice()
    chosen_method=medthod_dict[projection_method]
    zp.setMethod(chosen_method)
    outstack=imp.createEmptyStack()

    if glidingFlag:
        frames_to_advance_per_step = 1
    else:
        frames_to_advance_per_step = no_frames_per_integral

    for frame in range(1, total_no_frames_to_project, frames_to_advance_per_step):
        zp.setStartSlice(frame)
        zp.setStopSlice(frame+no_frames_per_integral)
        if hyperstackFlag:
            zp.doHyperStackProjection(False)
            projected_stack = zp.getProjection().getStack()
            for channel in range(projected_stack.getSize()):
                outstack.addSlice(projected_stack.getProcessor(channel+1))
        else:
            zp.doProjection()
            outstack.addSlice(zp.getProjection().getProcessor())

    #Create an image processor from the newly created Z-projection stack
    nChannels = imp.getNChannels()
    nFrames = outstack.getSize()/nChannels
    imp2=ImagePlus(title+'_'+projection_method+'_'+str(no_frames_per_integral)+'_frames', outstack)
    imp2 = HyperStackConverter.toHyperStack(imp2, nChannels, nSlices, nFrames)
    imp2.show()
    
    Startmenu()

def BackgroundFilter():

    def setupDialog(imp):

        gd = GenericDialog("Toolbox options")
        gd.addMessage("Imagej toolbox, you are analyzing: "+imp.getTitle())
        calibration = imp.getCalibration()

        if (calibration.frameInterval > 0):
            default_interval = calibration.frameInterval
            default_timeunit = calibration.getTimeUnit()
        
        else:
            default_interval = 10
            default_timeunit = "sec"
            
        gd.addNumericField("Frame interval:", default_interval, 2)  # show 2 decimals    
    #    gd.addCheckbox("Do you want to use a gliding window?", True)
    #    gd.addCheckbox("Project hyperStack? (defaluts to projecting current channel only)", False)
    #    gd.addStringField("time unit",default_timeunit, 3)
    #    gd.addSlider("Start compacting at frame:", 1, imp.getNFrames(), 1)
    #    gd.addSlider("Stop compacting at frame:", 1, imp.getNFrames(), imp.getNFrames())
    #    gd.addNumericField("Number of frames to project in to one:", 3, 0)  # show 0 decimals
        
        gd.addChoice('Method to use for stack background filtering:', methods_as_strings, methods_as_strings[5])
        
        gd.showDialog()  
          
        if gd.wasCanceled():  
            IJ.log("User canceled dialog!")  
            return

        return gd
        

    #Start by getting the active image window and get the current active channel and other stats
    imp = WindowManager.getCurrentImage()
    cal = imp.getCalibration()
    nSlices = 1 #TODO fix this in case you want to do Z-stacks
    title = imp.getTitle()
    current_channel = imp.getChannel()
    #zp = ZProjector(imp)

    #Make a dict containg method_name:const_fieled_value pairs for the projection methods
    methods_as_strings=['Average Intensity', 'Max Intensity', 'Min Intensity', 'Sum Slices', 'Standard Deviation', 'Median']
    methods_as_const=[ZProjector.AVG_METHOD, ZProjector.MAX_METHOD, ZProjector.MIN_METHOD, ZProjector.SUM_METHOD, ZProjector.SD_METHOD, ZProjector.MEDIAN_METHOD]
    method_dict=dict(zip(methods_as_strings, methods_as_const))

    gd = setupDialog(imp)

    #The Z-Projection magic happens here through a ZProjector object
    zp = ZProjector(imp)
    projection_method=gd.getNextChoice()
    chosen_method=method_dict[projection_method]
    zp.setMethod(chosen_method)
    outstack=imp.createEmptyStack()

    zp.doProjection()
    outstack.addSlice(zp.getProjection().getProcessor())
    imp2=ImagePlus(title+'_'+projection_method, outstack)
    # imp2.show()
    imp3=ImageCalculator().run("Subtract create 32-bit stack", imp, imp2)
    imp3.show()
    
    Startmenu()

def Startmenu():

    def setupDialog():

        gd = GenericDialog("Toolbox options")
        gd.addMessage("Imagej toolbox, choose an image: ")
            
    #    gd.addNumericField("Frame interval:", default_interval, 2)  # show 2 decimals    
    #    gd.addCheckbox("Do you want to use a gliding window?", True)
    #    gd.addCheckbox("Project hyperStack? (defaluts to projecting current channel only)", False)
    #    gd.addStringField("time unit",default_timeunit, 3)
    #    gd.addSlider("Start compacting at frame:", 1, imp.getNFrames(), 1)
    #    gd.addSlider("Stop compacting at frame:", 1, imp.getNFrames(), imp.getNFrames())
    #    gd.addNumericField("Number of frames to project in to one:", 3, 0)  # show 0 decimals
        
        gd.addChoice("Choose image:", image_titles, imp.getTitle())
        gd.addChoice('Choose pipeline:', pipelines_as_strings, pipelines_as_strings[0])
        
        gd.showDialog()  
          
        if gd.wasCanceled():  
            IJ.log("User canceled dialog!")  
            return

        return gd
    
    #define menu items
    pipelines_as_strings=['Background filter', 'Collective migration buddy']
    imp = WindowManager.getCurrentImage()
    image_titles = WindowManager.getImageTitles()
    gd = setupDialog()
    
    imp = gd.getNextChoice()

    choice = gd.getNextChoice()
    if (choice == 'Background filter'):
        BackgroundFilter()
    elif (choice == 'Collective migration buddy'):
        ColMigBud()
    
Startmenu()