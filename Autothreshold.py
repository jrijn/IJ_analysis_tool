from ij import IJ, WindowManager

def autoIncrement(start=1, interval=1, iterations=5):
    rec = []
    value = start - interval
    i = 0
    while i < iterations:
        value = value + interval
        rec.append(value)
        #print(rec)
        i = i + 1
    return rec

def main():
    imp = WindowManager.getCurrentImage()
    for j in autoIncrement(5,5,20):
	    IJ.run(imp, "Auto Local Threshold", "method=[Try all] radius={} parameter_1=0 parameter_2=0 white".format(j))

main()