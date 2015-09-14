import sys
import time
import visvis as vv
import numpy as np
import cPickle as pickle
import gzip

f=gzip.open(sys.argv[1],"rb")
data=pickle.load(f)
#!/usr/bin/env python

app = vv.use()
vv.clf()

# set labels
vv.xlabel('x axis')
vv.ylabel('y axis')
vv.zlabel('z axis')

# show
print np.sum(data) 
t = vv.volshow(data,renderStyle='iso',axesAdjust=True)
#t.isoThreshold = 0.5
# try the differtent render styles, for examample 
# "t.renderStyle='iso'" or "t.renderStyle='ray'"
# If the drawing hangs, your video drived decided to render in software mode.
# This is unfortunately (as far as I know) not possible to detect. 
# It might help if your data is shaped a power of 2.

# Get axes and set camera to orthographic mode (with a field of view of 70)
a = vv.gcf()
f = vv.gca()#fqwang

#a.camera.fov = 45

# Create colormap editor wibject.
vv.ColormapEditor(a)

rec = vv.record(f)

# Rotate camera
#fqwang
Nangles = 36
for i in range(Nangles):
    f.camera.azimuth = 360 * float(i) / Nangles
    if f.camera.azimuth>180:
        f.camera.azimuth -= 360
    f.Draw() # Tell the axes to redraw 
    a.DrawNow() # Draw the figure NOW, instead of waiting for GUI event loop


# Export
rec.Stop()
rec.Export('plot.swf')

# Start app
app.Run()