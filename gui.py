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
        #self.sliceDirection.addButton(directionX)
        #self.sliceDirection.addButton(directionY)
        #self.sliceDirection.addButton(directionZ)
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
        
        vBox2 = QtGui.QVBoxLayout()
        vBox2.addLayout(hBox1)
        vBox2.addLayout(hBox2)
        vBox2.addLayout(hBox3)
        vBox2.addWidget(self.confirmPlane)
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
        #grid = QtGui.QGridLayout()
        #grid.addWidget(self.frame, 0, 0)
        #grid.addWidget(self.sliceGroup, 0, 1)
        #self.setLayout(grid)
 
        self.show()
        self.iren.Initialize()
 
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('voxel')    
        self.show()
        
    def showDialog(self):

        self.fname = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                '/home'))
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
    def convertToVOX(self):
        if(self.directionX.isChecked()):
            direction = 0
        if(self.directionY.isChecked()):
            direction = 1
        if(self.directionZ.isChecked()):
            direction = 2
        if(self.fname != Null):
            if(convert.convert(self.fname)):
                meshFile = self.fname[:-3]+"mesh"
                print meshFile;
                sliceText = self.sliceTextLine.text()
                print sliceText
                print type(sliceText)
                sliceInt = sliceText.toUInt()
                #slcieInt = int(sliceFloat)
                print sliceInt[0]
                print type(sliceInt[0])
                if(execution(meshFile, direction, sliceInt[0])):
                    print "cool, it is done"
                    f=gzip.open(self.fname[:-3]+"vox","rb")
                    data=pickle.load(f)
                    self.data_matrix=numpy.uint8(data) 
                    self.dataImporter = vtk.vtkImageImport()
                    data_string = self.data_matrix.tostring()
                    self.dataImporter.CopyImportVoidPointer(data_string, len(data_string))
                    # The type of the newly imported data is set to unsigned char (uint8)
                    self.dataImporter.SetDataScalarTypeToUnsignedChar()
                    # Because the data that is imported only contains an intensity value (it isnt RGB-coded or someting similar), the importer
                    # must be told this is the case.
                    self.dataImporter.SetNumberOfScalarComponents(1)
                    # The following two functions describe how the data is stored and the dimensions of the array it is stored in. For this
                    # simple case, all axes are of length 75 and begins with the first element. For other data, this is probably not the case.
                    # I have to admit however, that I honestly dont know the difference between SetDataExtent() and SetWholeExtent() although
                    # VTK complains if not both are used.
                    xdim,ydim,zdim=self.data_matrix.shape
                    self.dataImporter.SetDataExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
                    self.dataImporter.SetWholeExtent(0, zdim-1, 0, ydim-1, 0, xdim-1)
                    
                    # The following class is used to store transparencyv-values for later retrival. In our case, we want the value 0 to be
                    # completly opaque whereas the three different cubes are given different transperancy-values to show how it works.
                    
                    alphaChannelFunc = vtk.vtkPiecewiseFunction()
                    alphaChannelFunc.AddPoint(0, 0.0)
                    alphaChannelFunc.AddPoint(1, 1.0)
                    #alphaChannelFunc.AddPoint(100, 1.0)
                    alphaChannelFunc.AddPoint(255, 1.0)
                    
                    # This class stores color data and can create color tables from a few color points. For this demo, we want the three cubes
                    # to be of the colors red green and blue.
                    colorFunc = vtk.vtkColorTransferFunction()
                    if(direction == 0):
                        colorFunc.AddRGBPoint(1, 0.0, 1.0, 1.0)
                        #colorFunc.AddRGBPoint(170, 0.0, 1.0, 0.0)
                        colorFunc.AddRGBPoint(255, 1.0, 1.0, 0.0)
                        #colorFunc.AddRGBPoint(0, 1.0, 1.0, 1.0)
                    if(direction == 1):
                        colorFunc.AddRGBPoint(1, 1.0, 0.0, 1.0)
                        #colorFunc.AddRGBPoint(170, 0.0, 1.0, 0.0)
                        colorFunc.AddRGBPoint(255, 0.0, 1.0, 1.0)
                        #colorFunc.AddRGBPoint(0, 1.0, 1.0, 1.0)
                    if(direction == 2):
                        colorFunc.AddRGBPoint(1, 1.0, 0.0, 0.0)
                        #colorFunc.AddRGBPoint(170, 0.0, 1.0, 0.0)
                        colorFunc.AddRGBPoint(255, 0.0, 0.0, 1.0)
                        #colorFunc.AddRGBPoint(0, 1.0, 1.0, 1.0)
                    
                    # The preavius two classes stored properties. Because we want to apply these properties to the volume we want to render,
                    # we have to store them in a class that stores volume prpoperties.
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
                    
                    # The class vtkVolume is used to pair the preaviusly declared volume as well as the properties to be used when rendering that volume.
                    
                    self.volume.SetMapper(volumeMapper)
                    self.volume.SetProperty(volumeProperty)
                    
                    # With almost everything else ready, its time to initialize the renderer and window, as well as creating a method for exiting the application
                    #renderer = vtk.vtkRenderer()
                    #renderWin = vtk.vtkRenderWindow()
                    #renderWin.AddRenderer(renderer)
                    #renderInteractor = vtk.vtkRenderWindowInteractor()
                    #renderInteractor.SetRenderWindow(renderWin)
                    
                    self.ren.RemoveActor(self.actor);
                    
                    # We add the volume to the renderer ...
                    self.ren.AddVolume(self.volume)
                    # ... set background color to white ...
                    self.ren.SetBackground(1, 1, 1)
                    # ... and set window size.
                    #renderWin.SetSize(800, 800)
                    
                    # A simple function to be called when the user decides to quit the application.
                    def exitCheck(obj, event):
                        if obj.GetEventPending() != 0:
                            obj.SetAbortRender(1)
                    
                    # Create a text mapper and actor to display the results of picking.
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
                    
                    # Create a cell picker.
                    self.picker = vtk.vtkCellPicker()
                    
                    # Create a Python function to create the text for the text mapper used
                    # to display the results of picking.
                    def annotatePick(object, event):
                        print("pick")
                        #global picker, textActor, textMapper
                        if self.picker.GetCellId() < 0:
                            self.textActor.VisibilityOff()
                        else:
                            selPt = self.picker.GetSelectionPoint()
                            pickPos = self.picker.GetPickPosition()
                            pickPosInt = (round(pickPos[0]), round(pickPos[1]),round(pickPos[2]))
                            pickPosIntStr = str(pickPosInt)
                            pickPosIntQStr = Qt.QString(pickPosIntStr)
                            if(self.firstPlanePt.isChecked()):
                                self.firstPlanePtValueRecord = pickPosInt
                                self.firstPlanePtValue.setText(pickPosIntQStr)
                            if(self.secondPlanePt.isChecked()):
                                self.secondPlanePtValueRecord = pickPosInt
                                self.secondPlanePtValue.setText(pickPosIntQStr)
                            if(self.thirdPlanePt.isChecked()):
                                self.thirdPlanePtValueRecord = pickPosInt
                                self.thirdPlanePtValue.setText(pickPosIntQStr)
                            pickValue = self.data_matrix[pickPosInt]
                            self.textMapper.SetInput("(%.3i, %.3i, %.3i)"%pickPosInt)
                            print pickValue
                            self.textActor.SetPosition(selPt[:2])
                            self.textActor.VisibilityOn()
                    
                    # Now at the end of the pick event call the above function.
                    self.picker.AddObserver("EndPickEvent", annotatePick)
                    
                    # Tell the application to use the function as an exit check.
                    renderWin = self.vtkWidget.GetRenderWindow()
                    renderWin.AddObserver("AbortCheckEvent", exitCheck)
                    self.iren.SetPicker(self.picker)
                    
                    # Add the actors to the renderer, set the background and size
                    self.ren.AddActor2D(self.textActor)
                    
                    self.confirmPlane.clicked.connect(self.addPlaneCutter)
                    
                    self.iren.Initialize()
                    # Initially pick the cell at this location.
                    self.picker.Pick(85, 126, 0, self.ren)
                    self.iren.Start()
                    
                    #renderInteractor.Initialize()
                    # Because nothing will be rendered without any input, we order the first render manually before control is handed over to the main-loop.
                    #renderWin.Render()
                    #renderInteractor.Start()    
                else:
                    print "cannot convert to vox"
            else:
                print "cannot convert to mesh"
    
    def addPlaneCutter(self):
        self.ren.RemoveActor(self.planeActor)
        plane=vtk.vtkPlane()
        plane.SetOrigin(float(self.firstPlanePtValueRecord[0]),float(self.firstPlanePtValueRecord[1]), float(self.firstPlanePtValueRecord[2]) )
        a = np.array([self.secondPlanePtValueRecord[0]-self.firstPlanePtValueRecord[0], self.secondPlanePtValueRecord[1]-self.firstPlanePtValueRecord[1], self.secondPlanePtValueRecord[2]-self.firstPlanePtValueRecord[2]])
        b = np.array([self.thirdPlanePtValueRecord[0]-self.firstPlanePtValueRecord[0], self.thirdPlanePtValueRecord[1]-self.firstPlanePtValueRecord[1],self.thirdPlanePtValueRecord[2]-self.firstPlanePtValueRecord[2]])
        c = np.cross(a, b)
        plane.SetNormal(c)
                    
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
        
                    
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()