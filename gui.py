import sys
from PyQt4 import QtGui
from PyQt4 import Qt
import convert as convert
from voxelize import *
from matplotlib.cbook import Null
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import numpy as np
import layerView
import filterGaussian
import openGlTest
from reportlab.lib.colors import white
from PyQt4.uic.Compiler.qtproxies import QtCore
from cvxopt import normal
from PyQt4.Qt import QHBoxLayout
from functools import partial
from time import sleep

#from vtkTest import renderWin

class MaterialControl():
    def __init__(self, materialId, controlSourceType, materialColor, controlWeight):
        self.materialId = materialId
        self.controlSourceType = controlSourceType
        self.materialColor = materialColor
        self.weight = controlWeight
    def setControlPlanePara(self, origin, normal):
        if  self.controlSourceType == "Plane":
            self.origin = origin
            self.normal = normal
        else:
            print "not a plane source"
    def setControlPointPara(self, point):
        if self.controlSourceType == "Point":
            self.point = point
        else:
            print "not a point source"
    def setControlFlexPara(self):
        if self.controlSourceType == "Flex":
            pass
        
class Example(QtGui.QMainWindow):
    
    def __init__(self):
        super(Example, self).__init__()
        self.materialInfo = []
        self.pointWtInt = []
        self.planeWtInt = []
        self.initUI()
        
    def initUI(self, parent = None):   
        
        QtGui.QMainWindow.__init__(self, parent)            
        
        """show dialog to choose the file button"""
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)
        
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openFile)
        
        """Mesh STL button"""
        stlMesh = QtGui.QAction(QtGui.QIcon('mesh.png'), 'Mesh', self)
        stlMesh.setStatusTip('Mesh File')
        stlMesh.triggered.connect(self.stlToMesh)
        
        self.toolbar = self.addToolBar('Mesh')
        self.toolbar.addAction(stlMesh)
        
        """Convert mesh into voxel"""
        conVert = QtGui.QAction(QtGui.QIcon('convert.png'), 'Convert', self)
        conVert.setShortcut('Ctrl+C')
        conVert.setStatusTip('Convert File')
        conVert.triggered.connect(self.convertToVOX)
        
        self.toolbar = self.addToolBar('Convert')
        self.toolbar.addAction(conVert)
        
        """"specify the material"""
        materialType = QtGui.QAction(QtGui.QIcon('materials.png'), 'material type', self)
        materialType.setShortcut('Ctrl + V')
        materialType.setStatusTip('specify material type')
        materialType.triggered.connect(self.MaterialType)
           
        self.toolbar = self.addToolBar('material')
        self.toolbar.addAction(materialType)   
        
        """Select control source"""
        controlSource = QtGui.QAction(QtGui.QIcon('controlSource.png'), 'select control source', self)
        controlSource.setShortcut('Ctrl + V')
        controlSource.setStatusTip('specify  control source')
        controlSource.triggered.connect(self.controlSource)
           
        self.toolbar = self.addToolBar('control source')
        self.toolbar.addAction(controlSource)             
        
        """show each layer specified"""
        view = QtGui.QAction(QtGui.QIcon('layers_example.gif'), 'Layer View', self)
        view.setShortcut('Ctrl + V')
        view.setStatusTip('show layer view')
        view.triggered.connect(self.layerViewFun)
        
        self.toolbar = self.addToolBar('View')
        self.toolbar.addAction(view)
        
        """Apply the Gaussian filter"""
        filterGaussian = QtGui.QAction(QtGui.QIcon('gaussian.png'), 'Gaussian Filter', self)
        filterGaussian.setShortcut('Ctrl + F')
        filterGaussian.setStatusTip("Gausssian Filter")
        filterGaussian.triggered.connect(self.filterGaussian)
        
        self.toolbar = self.addToolBar('filter')
        self.toolbar.addAction(filterGaussian)
        
        """Select a surface to derive material"""
        selectFace = QtGui.QAction(QtGui.QIcon('select_surface.gif'), 'Select Surface', self)
        selectFace.setShortcut('Ctrl + B')
        selectFace.setStatusTip("Select Surface")
        selectFace.triggered.connect(self.selectSurface)
        
        self.toolbar = self.addToolBar('surface')
        self.toolbar.addAction(selectFace)
        
        """specify the depth of the of the material distribution from surface"""
        addMaterial = QtGui.QAction(QtGui.QIcon('add_material.png'), 'Add Material', self)
        addMaterial.triggered.connect(self.addMaterial)
        
        self.toolbar = self.addToolBar('material')
        self.toolbar.addAction(addMaterial)
        
        """specify the forbidden composition"""
        deadPoint = QtGui.QAction(QtGui.QIcon('dead_point.png'), 'Add Dead Point', self)
        deadPoint.triggered.connect(self.addDeadPoint)
        
        self.toolbar = self.addToolBar('deadPoint')
        self.toolbar.addAction(deadPoint)
        
        """show each independent material"""
        materialShow = QtGui.QAction(QtGui.QIcon('independentMaterial.jpg'), 'Show Independent Material', self)
        materialShow.triggered.connect(self.showIndependentMaterial)
        
        self.toolbar = self.addToolBar('materialShow')
        self.toolbar.addAction(materialShow)        
        
        self.frame = QtGui.QFrame()
        self.vl = QtGui.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)
        
        """Direction and accuracy of the slice"""       
        self.sliceGroup = QtGui.QGroupBox("Slice Direction and Accuracy")
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
        #vBox1.addStretch(1)
        self.sliceGroup.setLayout(vBox1)
        self.vl.addWidget(self.sliceGroup)

        self.volume = vtk.vtkVolume()
        self.actor = vtk.vtkActor()
        self.planeActor=vtk.vtkActor()
        self.textActor = vtk.vtkActor2D()
 
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
    
    """Show dialog to open STL file"""    
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
        if self.planeActor != Null:
            self.ren.RemoveActor(self.planeActor)
        if self.textActor != Null:
            self.ren.RemoveActor(self.textActor)
        # Assign actor to the renderer
        self.ren.AddActor(self.actor)
        self.ren.ResetCamera()
        self.iren.Initialize()
        self.iren.Start()
    """mesh STL file"""    
    def stlToMesh(self):
        if(self.fname != Null):
            if(convert.convert(self.fname)):
                self.meshFile = self.fname[:-3]+"mesh"
                print self.meshFile; 
            else:
                print "cannot convert to mesh" 
        else:
            print "have not select a name"
    
    """Render the voxel file"""      
    def renderFig(self, direction):
        print "cool, it is done"
        fr=gzip.open(self.fname[:-3]+"voxr","rb")
        dataRed=pickle.load(fr)
        self.data_matrix_red=numpy.uint8(dataRed) 
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

        """Append the output to VTK"""
        self.append = vtk.vtkImageAppendComponents() 
        self.append.SetInputConnection(self.dataImporterR.GetOutputPort()) 
        self.append.AddInputConnection(self.dataImporterG.GetOutputPort()) 
        self.append.AddInputConnection(self.dataImporterB.GetOutputPort()) 
        self.append.Update() 
        
        """Set the mapper in VTK"""
        # This class describes how the volume is rendered (through ray tracing).
        #compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
        # We can finally create our volume. We also have to specify the data for it, as well as how the data will be rendered.
        #volumeMapper = vtk.vtkVolumeRayCastMapper()
        volumeMapper = vtk.vtkSmartVolumeMapper()
        #volumeMapper.SetVolumeRayCastFunction(compositeFunction)
        #volumeMapper.SetBlendModeToComposite()
        #volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()   
        volumeMapper.SetInputConnection(self.append.GetOutputPort())
        
        """Set the property of the volume"""            
        volumeProperty = vtk.vtkVolumeProperty() 
        volumeProperty.ShadeOff()
        volumeProperty.SetInterpolationTypeToLinear()
        #volumeProperty.SetIndependentComponents(3)
        volumeProperty.IndependentComponentsOn()
        
        """Set the color and opacity of each output"""
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

        #volumeProperty.SetIndependentComponents(4)    
        
        
        #volumeProperty = vtk.vtkVolumeProperty()
        #volprop.SetColor(colourTF)
        #volprop.SetScalarOpacity(alphaChannelFunc)
   
        self.volume.SetMapper(volumeMapper)
        self.volume.SetProperty(volumeProperty)
                    
        self.ren.RemoveActor(self.actor)
                    
        self.ren.AddVolume(self.volume)
        self.ren.SetBackground(1, 1, 1)
            
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
    """Specify control source"""
    def controlSource(self):
        materialNum = len(self.materials)
        #materialItems = []
        #for i in range(materialNum):
        #    materialItems.append("material"+str(i))
        #materialItem, ok = QtGui.QInputDialog.getItem(self, "select material dialog", 
        #"list of material", materialItems, 0, False)
        self.controlTypeTab = [QtGui.QTabWidget() for j in range(materialNum)]
        self.materialControl = QtGui.QTabWidget()
        
        self.planeWidget = [QtGui.QWidget() for j in range(materialNum)]
        self.planeGroup = [QtGui.QGroupBox("Select three points to identify the cut plane") for j in range(materialNum)]
        self.firstPlanePt = [QtGui.QRadioButton("First Point") for j in range(materialNum)]
        self.secondPlanePt = [QtGui.QRadioButton("Second Point") for j in range(materialNum)]
        self.thirdPlanePt = [QtGui.QRadioButton("Third Point") for j in range(materialNum)]
        self.firstPlanePtValue = [QtGui.QLabel("No Value") for j in range(materialNum)]
        self.secondPlanePtValue = [QtGui.QLabel("No Value") for j in range(materialNum)]
        self.thirdPlanePtValue = [QtGui.QLabel("No Value") for j in range(materialNum)]
        self.planeWeight = [QtGui.QLabel("Plane Weight") for j in range(materialNum)]    
        self.planeWeightText = [QtGui.QLineEdit("Type plane weight") for j in range(materialNum)]
        self.confirmPlane = [QtGui.QPushButton("Confirm") for j in range(materialNum)]
        self.voxFromPlane = [QtGui.QPushButton("Voxelize") for j in range(materialNum)]
        
        self.pointWidget = [QtGui.QWidget() for j in range(materialNum)]
        self.controlPt = [QtGui.QRadioButton("Control Point") for j in range(materialNum)]
        self.pointWeight = [QtGui.QLabel("Point Weight") for j in range(materialNum)]
        self.controlPtValue = [QtGui.QLabel("No Value") for j in range(materialNum)]
        self.pointWeightValue = [QtGui.QLineEdit("Type Point Weight") for j in range(materialNum)]
        self.confirmPoint = [QtGui.QPushButton("Confirm") for j in range(materialNum)]
        self.voxFromPoint = [QtGui.QPushButton("Voxelize") for j in range(materialNum)]
        
        self.pointWtInt = [0.0 for j in range(materialNum)]
        self.planeWtInt = [0.0 for j in range(materialNum)]
        
        self.firstPlanePtValueRecord = [(0.0, 0.0, 0.0) for j in range(materialNum)]
        self.secondPlanePtValueRecord = [(0.0, 0.0, 0.0) for j in range(materialNum)]
        self.thirdPlanePtValueRecord = [(0.0, 0.0, 0.0) for j in range(materialNum)]
        self.controlPtValueRecord = [(0.0, 0.0, 0.0) for j in range(materialNum)]
        
        self.planeOrigin = [(0.0, 0.0, 0.0) for j in range(materialNum)]
        self.planeNormal = [(0.0, 0.0, 0.0) for j in range(materialNum)]
        
        
                
        for i in range(materialNum):
            self.firstPlanePt[i].setChecked(True)
            
            hBox1 = QtGui.QHBoxLayout()
            hBox1.addWidget(self.firstPlanePt[i])
            hBox1.addWidget(self.firstPlanePtValue[i])
            hBox2 = QtGui.QHBoxLayout()
            hBox2.addWidget(self.secondPlanePt[i])
            hBox2.addWidget(self.secondPlanePtValue[i])
            hBox3 = QtGui.QHBoxLayout()
            hBox3.addWidget(self.thirdPlanePt[i])
            hBox3.addWidget(self.thirdPlanePtValue[i])
            hBox4 = QtGui.QHBoxLayout()
            hBox4.addWidget(self.planeWeight[i])
            hBox4.addWidget(self.planeWeightText[i])
            

            self.confirmPlane[i].clicked.connect(partial(self.addPlaneCutter, i))
            self.voxFromPlane[i].clicked.connect(partial(self.addNewPlaneControl, i))
            hBox5 = QtGui.QHBoxLayout()
            hBox5.addWidget(self.confirmPlane[i])
            hBox5.addWidget(self.voxFromPlane[i])
            
            vBox2 = QtGui.QVBoxLayout()
            vBox2.addLayout(hBox1)
            vBox2.addLayout(hBox2)
            vBox2.addLayout(hBox3)
            vBox2.addLayout(hBox4)
            vBox2.addLayout(hBox5)
            vBox2.addStretch(1)
            #self.planeGroup.setLayout(vBox2)
            self.planeWidget[i].setLayout(vBox2)
            

            self.controlPt[i].setChecked(True)

            controlPtHBox1 = QtGui.QHBoxLayout()
            controlPtHBox1.addWidget(self.controlPt[i])
            controlPtHBox1.addWidget(self.controlPtValue[i])
            controlPtHBox2 = QtGui.QHBoxLayout()
            controlPtHBox2.addWidget(self.pointWeight[i])
            controlPtHBox2.addWidget(self.pointWeightValue[i])
                

            self.confirmPoint[i].clicked.connect(partial(self.getPointWeight,i))
            self.voxFromPoint[i].clicked.connect(partial(self.addNewPointControl, i))
                #self.confirmPoint.clicked.connect(self.addPlaneCutter)  FIXME
                #self.voxFromPoint.clicked.connect(self.addNewPlaneControl)  FIXME
            controlPtHBox3 = QtGui.QHBoxLayout()
            controlPtHBox3.addWidget(self.confirmPoint[i])
            controlPtHBox3.addWidget(self.voxFromPoint[i])
                
            controlPtVBox = QtGui.QVBoxLayout()
            controlPtVBox.addLayout(controlPtHBox1)
            controlPtVBox.addStretch(8)
            controlPtVBox.addLayout(controlPtHBox2)
            controlPtVBox.addStretch(1)
            controlPtVBox.addLayout(controlPtHBox3)
            #self.pointGroup.setLayout(controlPtVBox)
            self.pointWidget[i].setLayout(controlPtVBox)
                       
            self.controlTypeTab[i].setWindowTitle("Material " + str(i))
            self.controlTypeTab[i].addTab(self.planeWidget[i], "Plane")
            self.controlTypeTab[i].addTab(self.pointWidget[i], "Point")
            self.materialControl.addTab(self.controlTypeTab[i], "Material " + str(i))
            
        self.readyToVoxel = QtGui.QWidget()
        self.readyToVoxelLayout = QHBoxLayout()
        self.readyToVoxelOk = QtGui.QPushButton("Voxelise")
        self.readyToVoxelOk.clicked.connect(self.convertToVOX4)
        self.readyToVoxelCancel = QtGui.QPushButton("Cancel")
        self.readyToVoxelLayout.addWidget(self.readyToVoxelOk)
        self.readyToVoxelLayout.addWidget(self.readyToVoxelCancel)
        self.readyToVoxel.setLayout(self.readyToVoxelLayout)
        self.materialControl.addTab(self.readyToVoxel, "Ok to voxel")
        
        self.materialControl.show()
    
    """Convert the mesh into voxel """    
    def convertToVOX(self):
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if(self.directionX.isChecked()):
            direction = 0
        if(self.directionY.isChecked()):
            direction = 1
        if(self.directionZ.isChecked()):
            direction = 2
        """Take the input of slice layers"""
        sliceText = self.sliceTextLine.text()
        sliceInt = sliceText.toUInt()
        self.guiVox = Voxelize()
        if(self.guiVox.execution(self.meshFile, direction, sliceInt[0])):
            self.renderFig(direction)
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
            
            i = self.materialControl.currentIndex()
            j = self.controlTypeTab[i].currentIndex()
            if j == 0:
                if self.firstPlanePt[i].isChecked():
                    self.firstPlanePtValueRecord[i] = pickPos
                    self.firstPlanePtValue[i].setText(pickPosIntQStr)
                if self.secondPlanePt[i].isChecked():
                    self.secondPlanePtValueRecord[i] = pickPos
                    self.secondPlanePtValue[i].setText(pickPosIntQStr)
                if self.thirdPlanePt[i].isChecked():
                    self.thirdPlanePtValueRecord[i] = pickPos
                    self.thirdPlanePtValue[i].setText(pickPosIntQStr)
            else:
                if self.controlPt[i].isChecked():
                    self.controlPtValueRecord[i] = pickPos
                    self.controlPtValue[i].setText(pickPosIntQStr)
            pickValue = self.data_matrix_red[round(pickPos[2]),round(pickPos[1]),round(pickPos[0])]
            self.textMapper.SetInput("(%.3i, %.3i, %.3i)"%pickPosInt)
            print pickValue
            self.textActor.SetPosition(selPt[:2])
            self.textActor.VisibilityOn()
                    
        # Now at the end of the pick event call the above function.
        self.picker.AddObserver("EndPickEvent", annotatePick)
        self.iren.SetPicker(self.picker)
        # Add the actors to the renderer, set the background and size
        self.ren.AddActor2D(self.textActor)
        
    def getPointWeight(self, i):
        pointWeightText = self.pointWeightValue[i].text()
        self.pointWtInt[i] = pointWeightText.toFloat()      
    
    def addPlaneCutter(self, i):
        #take record of the plane weight 
        planeWeightTextValue = self.planeWeightText[i].text()
        self.planeWtInt[i] = planeWeightTextValue.toFloat()
        self.ren.RemoveActor(self.planeActor)
        plane=vtk.vtkPlane()
        plane.SetOrigin(float(self.firstPlanePtValueRecord[i][0]),float(self.firstPlanePtValueRecord[i][1]), float(self.firstPlanePtValueRecord[i][2]) )
        a = np.array([self.secondPlanePtValueRecord[i][0]-self.firstPlanePtValueRecord[i][0], self.secondPlanePtValueRecord[i][1]-self.firstPlanePtValueRecord[i][1], self.secondPlanePtValueRecord[i][2]-self.firstPlanePtValueRecord[i][2]])
        b = np.array([self.thirdPlanePtValueRecord[i][0]-self.firstPlanePtValueRecord[i][0], self.thirdPlanePtValueRecord[i][1]-self.firstPlanePtValueRecord[i][1],self.thirdPlanePtValueRecord[i][2]-self.firstPlanePtValueRecord[i][2]])
        self.planeOrigin[i] = self.firstPlanePtValueRecord[i]
        self.planeNormal[i] = np.cross(a, b)
        self.planeNormal[i] = self.planeNormal[i] / np.linalg.norm(self.planeNormal[i])
        plane.SetNormal(self.planeNormal[i])
                    
        #create cutter
        cutter=vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputConnection(self.append.GetOutputPort())
        cutter.Update()
        cutterMapper=vtk.vtkPolyDataMapper()
        cutterMapper.SetInputConnection(cutter.GetOutputPort())
                    
        
        self.planeActor.GetProperty().SetColor(1.0,1,0)
        self.planeActor.GetProperty().SetLineWidth(2)
        self.planeActor.SetMapper(cutterMapper)
                    
        self.ren.AddActor(self.planeActor)
        
    def addNewPlaneControl(self, materialId):
        """
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if(self.guiVox.execution2(self.meshFile, self.planeOrigin, self.planeNormal)):
            self.renderFig(2)
        else:
            print "cannot convert to vox"
        """
        planeMaterial = MaterialControl(materialId, "Plane", self.materials[materialId], self.planeWtInt[materialId][0])
        planeMaterial.setControlPlanePara(self.planeOrigin[materialId], self.planeNormal[materialId])
        self.materialSet.append(planeMaterial)
        
    def addNewPointControl(self, materialId):
        #if self.volume != Null:
        #    self.ren.RemoveVolume(self.volume)
        #if(self.guiVox.execution3(self.meshFile, self.controlPtValueRecord)):
        #    self.renderFig(2)
        #else:
        #    print "cannot convert to vox"
        
        pointMaterial = MaterialControl(materialId, "Point", self.materials[materialId], self.pointWtInt[materialId][0])
        pointMaterial.setControlPointPara(self.controlPtValueRecord[materialId])
        self.materialSet.append(pointMaterial)
        
        
    def convertToVOX4(self):
        for i in range(len(self.materialSet)):
            print self.materialSet[i].controlSourceType
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if self.planeActor != Null: 
            self.ren.RemoveActor(self.planeActor)
        if self.guiVox.execution4(self.meshFile, self.materialSet):
            self.renderFig(2)
        else:
            print "cannot convert to vox"
    def convertInsideOut(self):
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if(self.guiVox.execution5(self.meshFile)):
            self.renderFig(2)
        else:
            print "cannot convert to vox"
    
    def layerViewFun(self):
        self.layerView = layerView.layerView(self.fname)
        #self.layerView.showLayer()
    def filterGaussian(self):
        #self.filterGaussian = filterGaussian.Ui_Form()
        #self.filterGaussian.getValueSignal.connect(self.getValue)
        items = ("Gaussian Fileter", "Average Filter")
        
        item, ok = QtGui.QInputDialog.getItem(self, "select input dialog", 
        "list of filters", items, 0, False)
           
        if ok and item:
            filterName = item
            
        if filterName == "Gaussian Fileter":
            num1,ok1 = QtGui.QInputDialog.getInt(self,"integer input dialog","enter a filter size")
            num2,ok2 = QtGui.QInputDialog.getInt(self,"integer input dialog","enter a filter sigma")
                     
            if self.volume != Null:
                self.ren.RemoveVolume(self.volume)
            if self.guiVox.execution6(self.meshFile, num1, num2):
                self.renderFig(2)
            else:
                print "cannot convert to vox"
                
        if filterName == "Average Filter":
            num3,ok3 = QtGui.QInputDialog.getInt(self,"integer input dialog","enter a filter size")
            
            if self.volume != Null:
                self.ren.RemoveVolume(self.volume)
            if self.guiVox.execution8(self.meshFile, num3, self.materials):
                self.renderFig(2)
            else:
                print "cannot convert to vox"
    def MaterialType(self):
        self.materialSet = []
        
        items = ("fixed type", "flexible type")
        item, ok = QtGui.QInputDialog.getItem(self, "select type of control sources", 
        "list of control sources", items, 0, False)
        if item == "fixed type":
            num1,ok1 = QtGui.QInputDialog.getInt(self,"integer input dialog","enter the number of material")
            self.materials = []
            for i in range(num1):
                cp = QtGui.QColorDialog.getColor(QtGui.QColor(255,255,255), self, "select material "+str(i))  
                self.materials.append((cp.red(), cp.green(), cp.blue()))
            print self.materials
        if item == "flexible type":
            num1,ok1 = QtGui.QInputDialog.getInt(self,"integer input dialog","enter the number of material")
            self.materials = []
            cp = QtGui.QColorDialog.getColor(QtGui.QColor(255,255,255), self, "select default material")  
            self.materials.append((cp.red(), cp.green(), cp.blue()))
            self.materialSet.append(MaterialControl(0, "Flex", self.materials[0], 1))
            self.triangleSelected = []            
            for i in range(num1):
                cp = QtGui.QColorDialog.getColor(QtGui.QColor(255,255,255), self, "select material "+str(i))  
                self.materials.append((cp.red(), cp.green(), cp.blue()))
                self.triangleSelected.append(None)
                self.materialSet.append(MaterialControl(i + 1, "Flex", self.materials[i + 1], 1))
            print self.materials
                        
    def getValue(self):
        self.layerBound1, self.layerBound2, self.layerBound3 = self.filterGaussian.returnValue() 
        print self.layerBound1, self.layerBound2, self.layerBound3
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if(self.guiVox.execution6(self.meshFile, self.layerBound1, self.layerBound2, self.layerBound3)):
            self.renderFig(2)
        else:
            print "cannot convert to gaussian prepare"
    def selectSurface(self):
        for i in range(1, len(self.materials)):
        
            app = openGlTest.PyAssimp3DViewer(model = self.fname, index = i - 1, w = 1024 /2 , h = 768 /2 , fov = 90.0)
    
            while app.loop():
                app.render()
                app.controls_3d(0)
                if openGlTest.pygame.K_f in app.keys: openGlTest.pygame.display.toggle_fullscreen()
                if openGlTest.pygame.K_TAB in app.keys: app.cycle_cameras()
                if openGlTest.pygame.K_ESCAPE in app.keys:
                    app.quit_viewer()
                    break
                if openGlTest.pygame.K_s in app.keys: self.triangleSelected[i - 1] = app.triangleSelected
    def addMaterial(self):
        depth = []
        for i in range(len(self.triangleSelected)):        
            num,ok = QtGui.QInputDialog.getInt(self,"Material Depth" + str(i),"enter a number")
            if ok:
                depth.append(num)
        #msg.buttonClicked.connect(msgbtn)
        print type(depth)
        print depth
        
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if self.guiVox.execution7(self.meshFile, self.triangleSelected, depth, self.materials):
            self.renderFig(2)
        else:
            print "cannot convert to vox"
    
    def addDeadPoint(self):
        items = []
        for i in range(len(self.materials) - 1):
            items.append("Material " + str(i + 1))
        item, ok = QtGui.QInputDialog.getItem(self, "select control sources", 
        "list of control sources", items, 0, False)
        
        num1,ok1 = QtGui.QInputDialog.getInt(self,"Forbidden Zone ","enter a forbidden zone number")
        
        materialNumber = int(item[-1])
        print materialNumber
        
        self.ratioArray = []
        
        for i in range(num1):
            if ok:   
                self.deadPointRatio = filterGaussian.Ui_Form()
                self.deadPointRatio.getValueSignal.connect(self.getDeadPoint)
        
        if self.volume != Null:
            self.ren.RemoveVolume(self.volume)
        if(self.guiVox.execution9(self.meshFile, self.materialSet, materialNumber, self.ratioArray)):
            self.renderFig(2)
        else:
            print "cannot convert to vox"
    
    def getDeadPoint(self):
        
        lowRatio = self.deadPointRatio.slideValue1 / 100.0
        upperRatio = self.deadPointRatio.slideValue2 / 100.0
        self.ratioArray.append((lowRatio, upperRatio))
            
    def showIndependentMaterial(self):
        items = []
        for i in range(len(self.materials) - 1):
            items.append("Material " + str(i + 1))
        item, ok = QtGui.QInputDialog.getItem(self, "select control sources", 
        "list of control sources", items, 0, False)
        
        materialNumber = int(item[-1])
        print materialNumber
        if ok:
            if self.volume != Null:
                self.ren.RemoveVolume(self.volume)
            if self.planeActor != Null: 
                self.ren.RemoveActor(self.planeActor)
            if self.guiVox.execution10(self.meshFile, self.materialSet, materialNumber):
                self.renderFig(2)
         
        
         
def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()