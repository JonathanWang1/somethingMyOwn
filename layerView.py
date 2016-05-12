'''
Created on Dec 6, 2015

@author: root
'''
from PyQt4 import QtGui
from PyQt4 import Qt
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import sys
import gzip
import cPickle as pickle
import numpy
from matplotlib.cbook import Null

class layerView(QtGui.QWidget):
    '''
    classdocs
    '''
    def __init__(self, fileName):
        super(layerView, self).__init__()
        self.initUI()
        self.fname = fileName
        
    def initUI(self):
        self.frame = QtGui.QFrame()      
         
        self.widgetLayout = QtGui.QVBoxLayout()
        self.setLayout(self.widgetLayout)
        self.widgetLayout.addWidget(self.frame)
        self.frameLayout = QtGui.QVBoxLayout()
        self.frame.setLayout(self.frameLayout)
        
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.frameLayout.addWidget(self.vtkWidget)
        
        self.sliceNumber = QtGui.QLineEdit("50")
        self.sliceConfirm = QtGui.QPushButton("confirm")
        self.sliceConfirm.clicked.connect(self.showLayer)
        self.sliceButtonLayout = QtGui.QHBoxLayout()
        self.sliceButtonLayout.addWidget(self.sliceNumber)
        self.sliceButtonLayout.addWidget(self.sliceConfirm)
        
        self.frameLayout.addLayout(self.sliceButtonLayout)
        
        self.volume = vtk.vtkVolume()
        
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        self.show()
        self.iren.Initialize()
 
        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Layer View')    
        self.show()
    def showLayer(self):
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        
        sliceNumber = self.sliceNumber.text()
        sliceIntArray = sliceNumber.toUInt()
        sliceInt = sliceIntArray[0]
        
        print "cool, it is done"
        fr=gzip.open(self.fname[:-3]+"voxr","rb")
        dataRed=pickle.load(fr)
        self.data_matrix_red=numpy.uint8(dataRed)
        self.data_matrix_red=self.data_matrix_red[sliceInt-1:sliceInt+1,:,:]
        with file('layerView.txt', 'w') as outfile:
            for data_slice in self.data_matrix_red:

        # The formatting string indicates that I'm writing out
        # the values in left-justified columns 7 characters in width
        # with 2 decimal places.  
                numpy.savetxt(outfile, data_slice,fmt='%-7.1f')

        # Writing out a break to indicate different slices...
                outfile.write('# New slice\n')
        
        
        self.dataImporterR = vtk.vtkImageImport()
        data_string = self.data_matrix_red.tostring()
        self.dataImporterR.CopyImportVoidPointer(data_string, len(data_string))
        self.dataImporterR.SetDataScalarTypeToUnsignedChar()
        self.dataImporterR.SetNumberOfScalarComponents(1)
        xdim,ydim,zdim=self.data_matrix_red.shape
        #self.dataImporter.SetDataExtent(0, zdim-1, 0, vtkPiecewiseFunctionb-1, 0, xdim-1)
        self.dataImporterR.SetDataExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        #self.dataImporter.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        self.dataImporterR.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        
        fg=gzip.open(self.fname[:-3]+"voxg","rb")
        dataGreen=pickle.load(fg)
        self.data_matrix_green=numpy.uint8(dataGreen)
        self.data_matrix_green = self.data_matrix_green[sliceInt-1:sliceInt+1,:,:] 
        self.dataImporterG = vtk.vtkImageImport()
        data_string = self.data_matrix_green.tostring()
        self.dataImporterG.CopyImportVoidPointer(data_string, len(data_string))
        self.dataImporterG.SetDataScalarTypeToUnsignedChar()
        self.dataImporterG.SetNumberOfScalarComponents(1)
        xdim,ydim,zdim=self.data_matrix_green.shape
        #self.dataImporter.SetDataExtent(0, zdim-1, 0, vtkPiecewiseFunctionb-1, 0, xdim-1)
        self.dataImporterG.SetDataExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        #self.dataImporter.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        self.dataImporterG.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        
        
        fb=gzip.open(self.fname[:-3]+"voxb","rb")
        dataBlue=pickle.load(fb)
        self.data_matrix_blue=numpy.uint8(dataBlue)
        self.data_matrix_blue = self.data_matrix_blue[sliceInt-1:sliceInt+1,:,:] 
        self.dataImporterB = vtk.vtkImageImport()
        data_string = self.data_matrix_blue.tostring()
        self.dataImporterB.CopyImportVoidPointer(data_string, len(data_string))
        self.dataImporterB.SetDataScalarTypeToUnsignedChar()
        self.dataImporterB.SetNumberOfScalarComponents(1)
        xdim,ydim,zdim=self.data_matrix_blue.shape
        #self.dataImporter.SetDataExtent(0, zdim-1, 0, vtkPiecewiseFunctionb-1, 0, xdim-1)
        self.dataImporterB.SetDataExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        #self.dataImporter.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
        self.dataImporterB.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)

        
        self.append = vtk.vtkImageAppendComponents() 
        self.append.SetInputConnection(self.dataImporterR.GetOutputPort()) 
        self.append.AddInputConnection(self.dataImporterG.GetOutputPort()) 
        self.append.AddInputConnection(self.dataImporterB.GetOutputPort()) 
        self.append.Update() 
        
        volumeMapper = vtk.vtkSmartVolumeMapper()
        volumeMapper.SetInputConnection(self.append.GetOutputPort())
        
        volumeProperty = vtk.vtkVolumeProperty() 
        volumeProperty.ShadeOff()
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.IndependentComponentsOn()
        
        opacityTF1 = vtk.vtkPiecewiseFunction() 
        opacityTF1.AddPoint(   0.0,  0.0 ) 
        opacityTF1.AddPoint(   1.0,  0.33)
        opacityTF1.AddPoint(   128.0, 0.33) 
        opacityTF1.AddPoint(   255.0,  0.33 ) 
        volumeProperty.SetScalarOpacity(0,opacityTF1) 
        
        colourTF1 = vtk.vtkColorTransferFunction() 
        colourTF1.AddRGBPoint(   0.0,  0.0, 0.0, 0.0 ) 
        colourTF1.AddRGBPoint(   1.0,  0.0, 0.0, 0.1 )
        colourTF1.AddRGBPoint(   128.0, 0.0, 0.0, 0.5 ) 
        colourTF1.AddRGBPoint(   255.0, 0.0, 0.0, 1.0 ) 
        volumeProperty.SetColor(0,colourTF1)
        
        opacityTF2 = vtk.vtkPiecewiseFunction() 
        opacityTF2.AddPoint(   0.0,  0.0 ) 
        opacityTF2.AddPoint(   1.0,  0.33 ) 
        opacityTF2.AddPoint(   128.0, 0.33)
        opacityTF2.AddPoint(   255.0,  0.33 ) 
        volumeProperty.SetScalarOpacity(1,opacityTF2) 
        
        colourTF2 = vtk.vtkColorTransferFunction() 
        colourTF2.AddRGBPoint(   0.0,  0.0, 0.0, 0.0 ) 
        colourTF2.AddRGBPoint(   1.0,  0.0, 0.1, 0.0 )
        colourTF2.AddRGBPoint(   128.0, 0.0, 0.5, 0.0 ) 
        colourTF2.AddRGBPoint(   255.0, 0.0, 1.0, 0.0 ) 
        volumeProperty.SetColor(1,colourTF2)
        
        opacityTF3 = vtk.vtkPiecewiseFunction() 
        opacityTF3.AddPoint(   0.0,  0.0 ) 
        opacityTF3.AddPoint(   1.0,  0.33 ) 
        opacityTF3.AddPoint(   128.0, 0.33)
        opacityTF3.AddPoint(   255.0,  0.33 ) 
        volumeProperty.SetScalarOpacity(2,opacityTF3) 
        
        colourTF3 = vtk.vtkColorTransferFunction() 
        colourTF3.AddRGBPoint(   0.0,  0.0, 0.0, 0.0 ) 
        colourTF3.AddRGBPoint(   1.0,  0.1, 0.0, 0.0 )
        colourTF3.AddRGBPoint(   128.0, 0.5, 0.0, 0.0 ) 
        colourTF3.AddRGBPoint(   255.0, 1.0, 0.0, 0.0 ) 
        volumeProperty.SetColor(2,colourTF3)
   
        self.volume.SetMapper(volumeMapper)
        self.volume.SetProperty(volumeProperty)
                    
        #self.ren.RemoveActor(self.actor)
                    
        self.ren.AddVolume(self.volume)
        self.ren.SetBackground(0, 0, 0)
        # A simple function to be called when the user decides to quit the application.
        def exitCheck(obj, event):
            if obj.GetEventPending() != 0:
                obj.SetAbortRender(1)
                                     
            # Tell the application to use the function as an exit check.
        light = vtk.vtkLight()
        #light.SetColor(1, 1, 1)
        light.SwitchOff()
        self.ren.AddLight(light)
        
        renderWin = self.vtkWidget.GetRenderWindow()
        renderWin.AddObserver("AbortCheckEvent", exitCheck)
                    
        self.iren.Initialize()
        self.iren.Start()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    cube = numpy.ones((50,50,50))
    #layerView = layerView(self.fname)
        
        
        