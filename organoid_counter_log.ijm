//This macro automatically detects, counts and measures cells and colonies in a folder of images.
//It requires the user to specify input folder (with images only) and output folder( where 
//results are stored). In addition the macro writes new images displaying outlines of measured 
//particles in the output folder.  Parameters such as minimum and maximum particle size etc are 
//determined manually by the user and entered at the prompts provided by the macro.
//Use the Analyze>Set Measurements command to specify the measurements 
//that are recorded for each cell/colony/object. 
//
//01-08-2017: 	Added the function to save a log file in a directory of choice. 
//				The .txt will store all variable user input for later reference.

macro Cell_Colony_Edge{

Dialog.create("Log file");
Dialog.addMessage("First choose a location and name for a log file. It will save your chosen settings.");
Dialog.show;
f = File.open("");

//Displays prompt for setting scale to values determined from calibration slide. Default value is 0 and pixel, which leave the scale in pixels as is. 	
Dialog.create("Type and Set Scale")
	Dialog.addNumber("Number of pixels/unit", 0);
	Dialog.addChoice("Unit:", newArray("pixel", "um"));
	Dialog.show();
	n = Dialog.getNumber();
	u = Dialog.getChoice();
	print(f, "Number of pixels/unit: "+"\t" + n);
	print(f, "Unit: " + u);

		
//Displays prompt for entering predetermined parameter values
Dialog.create("Parameters")
	Dialog.addCheckbox("Subtract Background", true);
	Dialog.addNumber("Rolling Ball Radius:", 50);
	Dialog.addNumber("Remove Outliers 1-radius:", 0.25);
	Dialog.addChoice("Remove Outliers 1 color:", newArray("Bright", "Dark"));
	Dialog.addNumber("Gaussian Blur-sigma:", 2);
	Dialog.addNumber("Remove Outliers 2-radius:", 8);
	Dialog.addNumber("Pixel Maximum:", 2);
	Dialog.addNumber("Pixel Minimum:", 3);
	Dialog.addCheckbox("Watershed", true);
	Dialog.addNumber("Remove Outliers 3-radius:", 12);
	Dialog.addNumber("Analyze Particles - Min size:", 800);
	Dialog.addNumber("Analyze Particles - Min circ:", 0.75);
	Dialog.addCheckbox("Measure Intensity from original image", false);
	Dialog.show();
//Assigns the entered values to variables
sub = Dialog.getCheckbox();
print(f, "Subtract Background: "+sub);
br = Dialog.getNumber();
print(f, "Rolling Ball Radius: "+br);
or1 = Dialog.getNumber();
print(f, "Remove Outliers 1-radius: "+or1);
col = Dialog.getChoice();
print(f, "Remove Outliers 1 color: "+col);
s = Dialog.getNumber();
print(f, "Gaussian Blur-sigma: "+s);
or2 = Dialog.getNumber();
print(f, "Remove Outliers 2-radius: "+or2);
mxr = Dialog.getNumber();
print(f, "Pixel Maximum: "+mxr);
mnr = Dialog.getNumber();
print(f, "Pixel Minimum: "+mnr);
wtr = Dialog.getCheckbox();
print(f, "Watershed: "+wtr);
or3 = Dialog.getNumber();
print(f, "Remove Outliers 3-radius: "+or3);
mnsz = Dialog.getNumber();
print(f, "Analyze Particles - Min size: "+mnsz);
mncr = Dialog.getNumber();
print(f, "Analyze Particles - Min circ: "+mncr);
orig = Dialog.getCheckbox();		
print(f, "Measure Intensity from original image: "+orig);

//Displays Prompt for selection of Input & Output Directory
Idir = getDirectory("Choose Input Directory ");	
Odir = getDirectory("Choose Output Directory");


list = getFileList(Idir);
if (getVersion>="1.40e")
        setOption("display labels", true);
setBatchMode(true);
for (i=0; i<list.length; i++) {
        showProgress(i, list.length);
	processFile(Idir, Odir, list[i]);
    		}
	
selectWindow("Results");
saveAs("Measurements", ""+Odir+"Results.txt");
selectWindow("Summary");
saveAs("Text", ""+Odir+"Summary.txt");



function processFile(Idir, Odir, filename)
	{
	open(Idir + filename);
	run("Set Scale...", "distance=n known=1 pixel=1 unit=u global");

	//Subtracts Backgound. To skip this step, deselect option in prompt. 
	if (sub==true){
		run("Subtract Background...", "rolling=50 light");
		}

	//Sharpens, enhances and finds edges in image	
	run("Sharpen");
	run("Enhance Contrast...", "saturated=0.3");

		
	
	//Smoothens and makes the image Black and white
	run("Gaussian Blur...", "sigma=4");
	run("Make Binary");



	//Closes and Fills Holes. Remove outliers step is for denoising and eliminating 	
	//debris particles. Can set size 0 in prompt if step is unnecessary. 
	run("Close-");
	run("Fill Holes");
	run("Remove Outliers...", "radius=3 threshold=100 which=Dark");



	//Expand pixels to fill holes, and shrink back to normal size
	run("Maximum...", "radius=2");
	run("Close-");
	run("Fill Holes");
	run("Minimum...", "radius=2"); 


	
	//Denoising to eliminate debris and unwanted particles. Size of outliers 
	//is set in prompt. Watershed command separates fused cells/colonies
	run("Despeckle");
	if (wtr==true){
		run("Watershed");
		}
	run("Remove Outliers...", "radius=2 threshold=100 which=Dark");
	makeRectangle(744, 794, 518, 92);
    run("Fill", "slice");
    makeRectangle(6, 5, 1268, 951);

		

	//Analyze particles to measure highlighted objects. Minimum and Maximum sizes,
	//and circularities can be chosen in the prompt.
	roiManager("Reset");
	roiManager("Show All with labels");
	roiManager("Show All");
	if (orig==true)
		run("Analyze Particles...", "size=mnsz-Infinity circularity=mncr-1.00 show=[Overlay Outlines]  exclude summarize add");
	 else 
	run("Analyze Particles...", "size=mnsz-Infinity circularity=mncr-1.00 show=[Overlay Outlines] display exclude summarize add");
	
		
	//Sends outlines from processed binary image to the original image via the ROI manager. Saves the original image displaying outlines in the output directory. 
	run("From ROI Manager");
	close();
	open(Idir + filename);
	run("From ROI Manager");
	roiManager("Show All with labels");
	roiManager("Show All");
	if (orig==true)
		roiManager("Measure");  
	Opath = Odir + filename;
	saveAs("JPEG", Opath);
	close();
	
	}

}



