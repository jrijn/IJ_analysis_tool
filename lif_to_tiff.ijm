macro "Break up a lif into individual TIFF" {
// open the file manager to select a lif file to break it into TIFFs
// in this case, only the metadata specific to a series will be written

path = File.openDialog("Select a File");

run("Bio-Formats Macro Extensions");
Ext.setId(path);
Ext.getCurrentFile(file);
Ext.getSeriesCount(seriesCount);

for (s=1; s<=seriesCount; s++) {
// Bio-Formats Importer uses an argument that can be built by concatenate a set of strings
run("Bio-Formats Importer", "open=&path autoscale color_mode=Default view=Hyperstack stack_order=XYCZT series_"+s);
out_path = getDirectory("image") + getTitle() + ".tif";
saveAs("tiff", out_path);
close();
    }
}