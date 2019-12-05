dir=getDirectory("Choose a Directory");
splitDir=dir + "\Split\\";
zprojDir=dir + "\maxProjection\\";
File.makeDirectory(splitDir);
File.makeDirectory(zprojDir);
list = getFileList(dir);

for (i=0; i<list.length; i++) {
     if (endsWith(list[i], ".tif")){
         print(i + ": " + dir+list[i]);
         open(dir+list[i]);
         imgName=getTitle();
         baseNameStart=indexOf(imgName, "-");
         baseNameEnd=indexOf(imgName, ".tif");
         baseName=substring(imgName, baseNameStart+2, baseNameEnd);

         run("Split Channels");
		
         c1="C1-" + imgName;
         c2="C2-" + imgName;
         c3="C3-" + imgName;
         
         selectWindow(c1);
		 run("Cyan");
		 run("Subtract Background...", "rolling=50");
         saveAs("Tiff", splitDir+ baseName + "_DAPI" + ".tif");
         run("Z Project...", "projection=[Max Intensity]");
         cyan=getTitle();
         saveAs("Tiff", zprojDir + cyan);

         selectWindow(c2);
         run("Red");
         run("Subtract Background...", "rolling=50");
         saveAs("Tiff", splitDir+ baseName + "_MITO" + ".tif");
         run("Z Project...", "projection=[Max Intensity]");
         red=getTitle();
         saveAs("Tiff", zprojDir + red);

         selectWindow(c3);
         run("Yellow");
         run("Subtract Background...", "rolling=50");
         saveAs("Tiff", splitDir+ baseName + "_NILERED" + ".tif");
         run("Z Project...", "projection=[Max Intensity]");
         yellow=getTitle();
         saveAs("Tiff", zprojDir + yellow);

		 //Create composite of DAPI and NILERED
		 run("Merge Channels...", "c5=[" + cyan + "] c7=[" + yellow + "] create keep");
		 run("Scale Bar...", "width=50 height=6 font=30 color=White background=None location=[Lower Right] bold overlay");
		 run("Flatten");
		 saveAs("Tiff", zprojDir + baseName + "_MERGE" + ".tif");
		 
         run("Close All");
     }
}
