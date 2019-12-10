// Filename Randomizer
// 
// This macro makes .tif copies of images inside a chosen folder 
// renaming  them with a 'pseudo-mock' random number.
// While running, the macro matches the assigned random filename 
// to the original image title in a printed table. It also saves this
// information in the image header ('Show  Info...' command); 
//
// Use it for unbias/blind analyses that may be sensitive to user 
// interpretation, or to randomize the sequence in which images
// of a folder are analyzed.
//
// It does not process subfolders.
//
// Tiago Ferreira - ferreira at embl dot it
// 04.2009


var extensions=newArray(".tif",".tiff",".stk",".jpeg",".jpg",".png",".zip",".lif",".gif");
var myDir,currentFldr, tbl;

macro " Filename Randomizer [F6]" {
    requires("1.42j");
    setBatchMode(true);
    settings(extensions);
    chosenDir=getDirectory("Choose a Directory ");
    start = getTime();
    makeNewDir(chosenDir);
    makeTable();
    processFiles(chosenDir);
    stop = getTime();
    showStatus("Finished... ("+((stop-start)/1000)+" seconds)");
    beep;
    setBatchMode(false);  
}

// functions 

function settings(extlist) {
  msg1="Choose extension of images to obfuscate\n"+
       "below. The chosen images will then be copied\nto a '*_randomized'"+
       " folder.\n \nRetrieve original names at any time by using\n"+
       "the 'Show  Info...' command.\n \nYou will next be prompted to choose the images\nfolder. "+
       "Subfolders will not be processed.";
  Array.sort(extlist);
  lgth=extlist.length;
  gridSide=sqrt(lgth);
  rows=round(gridSide)-1; cols=round(gridSide)+2;
  defaults = newArray(lgth); defaults= Array.fill(defaults, 1);
  Dialog.create('Settings');
  Dialog.addMessage(msg1);
  Dialog.addCheckboxGroup(rows,cols, extlist, defaults);
  Dialog.show();
  count=0;
  chosenExt=newArray(lgth);
  for (i=0; i< lgth; i++) {
    chosenExt[i]=Dialog.getCheckbox(); 
    if(chosenExt[i]==1) count++;
  }
  finalExt=newArray(count); h=0;
  for (i=0; i<lgth; i++)
    if(chosenExt[i]==1) {finalExt[h]=extlist[i];h++;}
  return  finalExt;
}

function makeNewDir(dir) {
  upDir=File.getParent(dir);
  endCFName=lengthOf(chosenDir)-1; startCFName=lengthOf(upDir)+1;
  currentFldr=substring(chosenDir,startCFName,endCFName);
  myDir=upDir+File.separator+ currentFldr +"_Randomized"+File.separator;
  if(File.exists(myDir)) 
       showMessageWithCancel("A folder named:\n"+myDir+"\nAlready exists...\n \nOverride?");
  File.makeDirectory(myDir);
}
 
function makeTable() {
  tb=currentFldr+"_Obfuscated_List.xls"; tbl="["+tb+"]";
  if(isOpen(tb)) print(tbl, "\\Clear");
  else {
  run("New... ", "name="+tbl+" type=Table");
  print(tbl, "\\Headings:#\tOriginal Title\tRandomized Title\tOriginal Directory\tNew Directory");
  }
}

function processFiles(dir) {
  list = getFileList(dir);
  list3=newArray(list.length);
  randomize(list3);
  for (i=0; i<list.length; i++) {
    if (!endsWith(list[i], "/")) {
        oldname=list[i]; newname=list3[i];
        ext=substring(oldname, lastIndexOf(oldname, "."), lengthOf(oldname));
        processFile(dir, myDir, oldname, newname,ext);
    }
  }
}

function processFile(oldDir, newDir, oldname,newname, xt) {
  nN=0; 
  for (h=0; h<extensions.length; h++) if(endsWith(ext, extensions[h])) {   
  msg= "Original Path: "+ oldDir+ oldname+" \nAssigned Path: "+ newDir+ newname +xt;
  open(oldDir+oldname);
  setMetadata("Info",msg);
  saveAs("tiff",newDir+newname);
  print(tbl, i+1+"\t"+oldname+"\t" +newname+xt+"\t" + oldDir +"\t"+ newDir);
  close();nN++;}
}

function randomize(array) {
  for (i=0; i<array.length; i++) {
    n =round(array.length*random);
    m=toString(n)+"_"+toString(i+1);  
    while(lengthOf(m)<10) m= "0"+m;
    array[i]=m;}
   return array;
}