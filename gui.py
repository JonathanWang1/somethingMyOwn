import sys
from PyQt4 import QtGui
from PyQt4 import Qt
import convert as convert
from voxelize import *
from matplotlib.cbook import Null
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import numpy as np
#from vtkTest import renderWin


class Example(QtGui.QMainWindow):
    
    def __init__(self):
        super(Example, self).__init__()
        self.initUI()
        
    def initUI(self, parent = None):   
        
        QtGui.QMainWindow.__init__(self, parent)            
        
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)
        
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openFile)
        
        stlMesh = QtGui.QAction(QtGui.QIcon('mesh.png'), 'Mesh', self)
        stlMesh.setStatusTip('Mesh File')
        stlMesh.triggered.connect(self.stlToMesh)
        
        self.toolbar = self.addToolBar('Mesh')
        self.toolbar.addAction(stlMesh)
        
        conVert = QtGui.QAction(QtGui.QIcon('convert.png'), 'Convert', self)
        conVert.setShortcut('Ctrl+C')
        conVert.setStatusTip('Convert File')
        conVert.triggered.connect(self.convertToVOX)
        
        self.toolbar = self.addToolBar('Convert')
        self.toolbar.addAction(conVert)
        
        self.frame = QtGui.QFrame()
        self.vl = QtGui.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)
                
        self.sliceGroup = QtGui.QGroupBox("Slice Direction and Accuracy")
        #self.sliceDirection = QtGui.QButtonGroup()
        self.directionX = QtGui.QRadioButton("X")
        self.directionY = QtGui.QRadioButton("Y")
        self.directionZ = QtGui.QRadioButton("Z")
        self.directionZ.setChecked(True)
        
        accuracyLabel = QtGui.QLabel("Slice Accuracy")
        self.sliceTextLine = QtGui.QLineEdit("how many slices do you want")
        vBox1 = QtGui.QVBoxLayout()
        vBox1.addWidget(self.directionX)
        vBox1.addWidget(self.directionY)
        vBox1.addWidget(self.directionZ)
        vBox1.addWidget(accuracyLabel)
        vBox1.addWidget(self.sliceTextLine)
        vBox1.addStretch(1)
        self.sliceGroup.setLayout(vBox1)
        self.vl.addWidget(self.sliceGroup)
        
        self.planeGroup = QtGui.QGroupBox("Select three points to identify the cut plane")
        self.firstPlanePt = QtGui.QRadioButton("First Point")
        self.secondPlanePt = QtGui.QRadioButton("Second Point")
        self.thirdPlanePt = QtGui.QRadioButton("Third Point")
        self.firstPlanePt.setChecked(True)
        
        self.firstPlanePtValue = QtGui.QLabel("No Value")
        self.secondPlanePtValue = QtGui.QLabel("No Value")
        self.thirdPlanePtValue = QtGui.QLabel("No Value")
        
        hBox1 = QtGui.QHBoxLayout()
        hBox1.addWidget(self.firstPlanePt)
        hBox1.addWidget(self.firstPlanePtValue)
        hBox2 = QtGui.QHBoxLayout()
        hBox2.addWidget(self.secondPlanePt)
        hBox2.addWidget(self.secondPlanePtValue)
        hBox3 = QtGui.QHBoxLayout()
        hBox3.addWidget(self.thirdPlanePt)
        hBox3.addWidget(self.thirdPlanePtValue)
        
        self.confirmPlane = QtGui.QPushButton("Confirm")
        self.voxFromPlane = QtGui.QPushButton("Voxelize")
        self.confirmPlane.clicked.connect(self.addPlaneCutter)
        self.voxFromPlane.clicked.connect(self.convertToVOX2)
        hBox4 = QtGui.QHBoxLayout()
        hBox4.addWidget(self.confirmPlane)
        hBox4.addWidget(self.voxFromPlane)
        
        vBox2 = QtGui.QVBoxLayout()
        vBox2.addLayout(hBox1)
        vBox2.addLayout(hBox2)
        vBox2.addLayout(hBox3)
        vBox2.addLayout(hBox4)
        vBox2.addStretch(1)
        self.planeGroup.setLayout(vBox2)
        self.vl.addWidget(self.planeGroup)
        
        self.volume = vtk.vtkVolume()
        self.actor = vtk.vtkActor()
        self.planeActor=vtk.vtkActor()
 
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
 
        self.show()
        self.iren.Initialize()
 
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('voxel')    
        self.show()
        
    def showDialog(self):
        self.fname = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', '/home'))
        reader = vtk.vtkSTLReader()
        reader.SetFileName(self.fname)
        mapper = vtk.vtkPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(reader.GetOutput())
        else:
            mapper.SetInputConnection(reader.GetOutputPort())
        
        self.actor.SetMapper(mapper)
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        # Assign actor to the renderer
        self.ren.AddActor(self.actor)
        self.ren.ResetCamera()
        self.iren.Initialize()
        self.iren.Start()
        
    def stlToMesh(self):
        if(self.fname != Null):
            if(convert.convert(self.fname)):
                self.meshFile = self.fname[:-3]+"mesh"
                print self.meshFile; 
            else:
                print "cannot convert to mesh" 
        else:
            print "have not select a name"      
    
    def convertToVOX(self):
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if(self.directionX.isChecked()):
            direction = 0
        if(self.directionY.isChecked()):
            direction = 1
        if(self.directionZ.isChecked()):
            direction = 2
        sliceText = self.sliceTextLine.text()
        sliceInt = sliceText.toUInt()

        if(execution(self.meshFile, direction, sliceInt[0])):
            print "cool, it is done"
            f=gzip.open(self.fname[:-3]+"vox","rb")
            data=pickle.load(f)
            self.data_matrix=numpy.uint8(data) 
            self.dataImporter = vtk.vtkImageImport()
            data_string = self.data_matrix.tostring()
            self.dataImporter.CopyImportVoidPointer(data_string, len(data_string))
            self.dataImporter.SetDataScalarTypeToUnsignedChar()
            self.dataImporter.SetNumberOfScalarComponents(1)
            xdim,ydim,zdim=self.data_matrix.shape
            #self.dataImporter.SetDataExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
            self.dataImporter.SetDataExtent(0, xdim-1, 0, ydim-1, 0, zdim-1)
            #self.dataImporter.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
            self.dataImporter.SetWholeExtent(0, xdim-1, 0, ydim-1, 0, zdim-1)

            alphaChannelFunc = vtk.vtkPiecewiseFunction()
            alphaChannelFunc.AddPoint(0, 0.0)
            alphaChannelFunc.AddPoint(1, 1.0)
            alphaChannelFunc.AddPoint(255, 1.0)
                    

            colorFunc = vtk.vtkColorTransferFunction()
            if(direction == 0):
                colorFunc.AddRGBPoint(1, 0.0, 1.0, 1.0)
                colorFunc.AddRGBPoint(255, 1.0, 1.0, 0.0)
            if(direction == 1):
                colorFunc.AddRGBPoint(1, 1.0, 0.0, 1.0)
                colorFunc.AddRGBPoint(255, 0.0, 1.0, 1.0)
            if(direction == 2):
                colorFunc.AddRGBPoint(1, 1.0, 0.0, 0.0)
                colorFunc.AddRGBPoint(255, 0.0, 0.0, 1.0)

            volumeProperty = vtk.vtkVolumeProperty()
            volumeProperty.SetColor(colorFunc)
            volumeProperty.SetScalarOpacity(alphaChannelFunc)
            volumeProperty.ShadeOn()
            volumeProperty.SetInterpolationTypeToNearest()
                    
                    
            # This class describes how the volume is rendered (through ray tracing).
            compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
            # We can finally create our volume. We also have to specify the data for it, as well as how the data will be rendered.
            volumeMapper = vtk.vtkVolumeRayCastMapper()
            volumeMapper.SetVolumeRayCastFunction(compositeFunction)
            volumeMapper.SetInputConnection(self.dataImporter.GetOutputPort())
                    
   
            self.volume.SetMapper(volumeMapper)
            self.volume.SetProperty(volumeProperty)
                    
            self.ren.RemoveActor(self.actor);
                    
            self.ren.AddVolume(self.volume)
            self.ren.SetBackground(1, 1, 1)
            
            axesActor = vtk.vtkAxesActor()
            axesActor.AxisLabelsOn()
            axesActor.SetShaftTypeToCylinder()
            axesActor.SetCylinderRadius(0.05)
            self.ren.AddActor(axesActor)
            
            self.addPicker()
            # A simple function to be called when the user decides to quit the application.
            def exitCheck(obj, event):
                if obj.GetEventPending() != 0:
                    obj.SetAbortRender(1)
                                     
            # Tell the application to use the function as an exit check.
            renderWin = self.vtkWidget.GetRenderWindow()
            renderWin.AddObserver("AbortCheckEvent", exitCheck)
                    
            self.iren.Initialize()
            # Initially pick the cell at this location.
            self.picker.Pick(85, 126, 0, self.ren)
            self.iren.Start()
 
        else:
            print "cannot convert to vox"
     
    def addPicker(self):
        self.textMapper = vtk.vtkTextMapper()
        tprop = self.textMapper.GetTextProperty()
        tprop.SetFontFamilyToArial()
        tprop.SetFontSize(10)
        tprop.BoldOn()
        tprop.ShadowOn()
        tprop.SetColor(1, 0, 0)
        self.textActor = vtk.vtkActor2D()
        self.textActor.VisibilityOff()
        self.textActor.SetMapper(self.textMapper)
                    
        self.picker = vtk.vtkCellPicker()
                    
        def annotatePick(object, event):
            print("pick")
            if self.picker.GetCellId() < 0:
                self.textActor.VisibilityOff()
            else:
                selPt = self.picker.GetSelectionPoint()
                pickPos = self.picker.GetPickPosition()
                pickPosInt = (round(pickPos[0]), round(pickPos[1]),round(pickPos[2]))
                pickPosIntStr = str(pickPosInt)
                pickPosIntQStr = Qt.QString(pickPosIntStr)
            if(self.firstPlanePt.isChecked()):
                self.firstPlanePtValueRecord = pickPos
                self.firstPlanePtValue.setText(pickPosIntQStr)
            if(self.secondPlanePt.isChecked()):
                self.secondPlanePtValueRecord = pickPos
                self.secondPlanePtValue.setText(pickPosIntQStr)
            if(self.thirdPlanePt.isChecked()):
                self.thirdPlanePtValueRecord = pickPos
                self.thirdPlanePtValue.setText(pickPosIntQStr)
            pickValue = self.data_matrix[pickPosInt]
            self.textMapper.SetInput("(%.3i, %.3i, %.3i)"%pickPosInt)
            print pickValue
            self.textActor.SetPosition(selPt[:2])
            self.textActor.VisibilityOn()
                    
        # Now at the end of the pick event call the above function.
        self.picker.AddObserver("EndPickEvent", annotatePick)
        self.iren.SetPicker(self.picker)
        # Add the actors to the renderer, set the background and size
        self.ren.AddActor2D(self.textActor)
        
    
    def addPlaneCutter(self):
        self.ren.RemoveActor(self.planeActor)
        plane=vtk.vtkPlane()
        plane.SetOrigin(float(self.firstPlanePtValueRecord[0]),float(self.firstPlanePtValueRecord[1]), float(self.firstPlanePtValueRecord[2]) )
        a = np.array([self.secondPlanePtValueRecord[0]-self.firstPlanePtValueRecord[0], self.secondPlanePtValueRecord[1]-self.firstPlanePtValueRecord[1], self.secondPlanePtValueRecord[2]-self.firstPlanePtValueRecord[2]])
        b = np.array([self.thirdPlanePtValueRecord[0]-self.firstPlanePtValueRecord[0], self.thirdPlanePtValueRecord[1]-self.firstPlanePtValueRecord[1],self.thirdPlanePtValueRecord[2]-self.firstPlanePtValueRecord[2]])
        self.planeOrigin = self.firstPlanePtValueRecord
        self.planeNormal = np.cross(a, b)
        self.planeNormal = self.planeNormal / np.linalg.norm(self.planeNormal)
        plane.SetNormal(self.planeNormal)
                    
        #create cutter
        cutter=vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputConnection(self.dataImporter.GetOutputPort())
        cutter.Update()
        cutterMapper=vtk.vtkPolyDataMapper()
        cutterMapper.SetInputConnection(cutter.GetOutputPort())
                    
        
        self.planeActor.GetProperty().SetColor(1.0,1,0)
        self.planeActor.GetProperty().SetLineWidth(2)
        self.planeActor.SetMapper(cutterMapper)
                    
        self.ren.AddActor(self.planeActor)
        
    def convertToVOX2(self):
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        sliceText = self.sliceTextLine.text()
        sliceInt = sliceText.toUInt()
        #slcieInt = int(sliceFloat)
        print sliceInt[0]
        print type(sliceInt[0])
        if(execution2(self.meshFile, sliceInt[0], self.planeOrigin, self.planeNormal)):
            print "cool, it is done"
            f=gzip.open(self.fname[:-3]+"vox","rb")
            data=pickle.load(f)
            self.data_matrix=numpy.uint8(data) 
            self.dataImporter = vtk.vtkImageImport()
            data_string = self.data_matrix.tostring()
            self.dataImporter.CopyImportVoidPointer(data_string, len(data_string))
            self.dataImporter.SetDataScalarTypeToUnsignedChar()
            self.dataImporter.SetNumberOfScalarComponents(1)
            xdim,ydim,zdim=self.data_matrix.shape
            #self.dataImporter.SetDataExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
            self.dataImporter.SetDataExtent(0, xdim-1, 0, ydim-1, 0, zdim-1)
            #self.dataImporter.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
            self.dataImporter.SetWholeExtent(0, xdim-1, 0, ydim-1, 0, zdim-1)

            alphaChannelFunc = vtk.vtkPiecewiseFunction()
            alphaChannelFunc.AddPoint(0, 0.0)
            alphaChannelFunc.AddPoint(1, 1.0)
            alphaChannelFunc.AddPoint(100, 1.0)
                    
            colorFunc = vtk.vtkColorTransferFunction()
            colorFunc.AddRGBPoint(1, 1.0, 0.0, 0.0)
            colorFunc.AddRGBPoint(100, 0.0, 0.0, 1.0)

            volumeProperty = vtk.vtkVolumeProperty()
            volumeProperty.SetColor(colorFunc)
            volumeProperty.SetScalarOpacity(alphaChannelFunc)
            volumeProperty.ShadeOn()
            volumeProperty.SetInterpolationTypeToNearest()
                    
                    
            # This class describes how the volume is rendered (through ray tracing).
            compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
            # We can finally create our volume. We also have to specify the data for it, as well as how the data will be rendered.
            volumeMapper = vtk.vtkVolumeRayCastMapper()
            volumeMapper.SetVolumeRayCastFunction(compositeFunction)
            volumeMapper.SetInputConnection(self.dataImporter.GetOutputPort())
                    
   
            self.volume.SetMapper(volumeMapper)
            self.volume.SetProperty(volumeProperty)
                    
            self.ren.RemoveActor(self.actor);
                    
            self.ren.AddVolume(self.volume)
            self.ren.SetBackground(1, 1, 1)
            
            axesActor = vtk.vtkAxesActor()
            axesActor.AxisLabelsOn()
            axesActor.SetShaftTypeToCylinder()
            axesActor.SetCylinderRadius(0.05)
            self.ren.AddActor(axesActor)
            
            self.addPicker()
            # A simple function to be called when the user decides to quit the application.
            def exitCheck(obj, event):
                if obj.GetEventPending() != 0:
                    obj.SetAbortRender(1)
                                     
            # Tell the application to use the function as an exit check.
            renderWin = self.vtkWidget.GetRenderWindow()
            renderWin.AddObserver("AbortCheckEvent", exitCheck)
                    
            self.iren.Initialize()
            # Initially pick the cell at this location.
            self.picker.Pick(85, 126, 0, self.ren)
            self.iren.Start()
 
        else:
            print "cannot convert to vox"
        
                    
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()