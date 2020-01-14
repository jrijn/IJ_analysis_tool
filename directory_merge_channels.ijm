c1=getDirectory("Choose a directory for channel 1");
c2=getDirectory("Choose a directory for channel 2");
output=getDirectory("Choose an output directory");

c1list = getFileList(c1);
c2list = getFileList(c2);

if (c1list.length != c2list.length) {
	print("The two directories do not contain an equal number of images")
}

for (i=0; i<c1list.length; i++) {
     if (endsWith(c1list[i], ".tif")){
         print(i + ": " + c1+c1list[i]);
         open(c1+c1list[i]);
         c1name=getTitle();
         open(c2+c2list[i]);
         c2name=getTitle();

         //baseNameStart=indexOf(imgName, "-");
         //baseNameEnd=indexOf(imgName, ".tif");
         //baseName=substring(imgName, baseNameStart+2, baseNameEnd);

         run("Merge Channels...", "c1="+c1name+" c2="+c2name+" create");
		
		 saveAs("Tiff", output + c1name + ".tif");
		 
         run("Close All");
     }
}
