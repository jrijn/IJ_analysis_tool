n = getNumber("How many divisions (e.g., 2 means quarters)?", 2);
id = getImageID;
title = getTitle;
height = getHeight;
width = getWidth;

for (y = 0; y < n; y++){
	offsetY = y * height / n;
	for (x = 0; x < n; x++) {
		offsetX = x * width / n;
		selectImage(id);
		makeRectangle(offsetX, offsetY, width / n, height / n);
		tileTitle = title + " [" + x + "," + y + "]";
		run("Duplicate...", "title=" + tileTitle + " duplicate");
	} 
}
