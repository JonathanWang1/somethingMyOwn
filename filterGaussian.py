from PyQt4 import QtCore, QtGui, Qt
import sys
import gui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Form(QtGui.QWidget):
    
    getValueSignal = QtCore.pyqtSignal()
    
    def __init__(self):
        super(Ui_Form,self).__init__()
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(443, 341)
        self.groupBox = QtGui.QGroupBox(Form)
        self.groupBox.setGeometry(QtCore.QRect(20, 20, 331, 291))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayoutWidget = QtGui.QWidget(self.groupBox)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(20, 20, 281, 131))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalSlider_2 = QtGui.QSlider(self.horizontalLayoutWidget)
        self.verticalSlider_2.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_2.setObjectName(_fromUtf8("verticalSlider_2"))
        self.horizontalLayout.addWidget(self.verticalSlider_2)
        self.verticalSlider = QtGui.QSlider(self.horizontalLayoutWidget)
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setObjectName(_fromUtf8("verticalSlider"))
        self.horizontalLayout.addWidget(self.verticalSlider)

        self.horizontalLayoutWidget_2 = QtGui.QWidget(self.groupBox)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(20, 150, 281, 31))
        self.horizontalLayoutWidget_2.setObjectName(_fromUtf8("horizontalLayoutWidget_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_2 = QtGui.QLabel(self.horizontalLayoutWidget_2)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_2.addWidget(self.label_2)
        self.label = QtGui.QLabel(self.horizontalLayoutWidget_2)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)

        self.horizontalLayoutWidget_3 = QtGui.QWidget(self.groupBox)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(20, 180, 281, 31))
        self.horizontalLayoutWidget_3.setObjectName(_fromUtf8("horizontalLayoutWidget_3"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_3.setMargin(0)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.lineEdit_2 = QtGui.QLineEdit(self.horizontalLayoutWidget_3)
        self.lineEdit_2.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))
        self.horizontalLayout_3.addWidget(self.lineEdit_2)
        self.lineEdit = QtGui.QLineEdit(self.horizontalLayoutWidget_3)
        self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.horizontalLayout_3.addWidget(self.lineEdit)

        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setGeometry(QtCore.QRect(20, 220, 281, 31))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))


        self.retranslateUi(Form)
        
        self.connect(self.verticalSlider_2, QtCore.SIGNAL('valueChanged(int)'), self.setLineEditer1)
        self.connect(self.verticalSlider, QtCore.SIGNAL('valueChanged(int)'), self.setLineEditer2)
        #self.connect(self.verticalSlider_3, QtCore.SIGNAL('valueChanged(int)'), self.setLineEditer3)
        self.connect(self.pushButton, QtCore.SIGNAL('clicked()'), self.getValue)
        
        self.show()

    def setLineEditer1(self,value):
        self.slideValue1 = value
        valueString = Qt.QString(str(value))
        self.lineEdit_2.setText(valueString)
    def setLineEditer2(self,value):
        self.slideValue2 = value
        valueString = Qt.QString(str(value))
        self.lineEdit.setText(valueString)
    def setLineEditer3(self,value):
        self.slideValue3 = value
        valueString = Qt.QString(str(value))
        self.lineEdit_3.setText(valueString)    
    def getValue(self):
        self.getValueSignal.emit()
    def returnValue(self):
        return self.slideValue1, self.slideValue2
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.groupBox.setTitle(_translate("Form", "Material Control", None))
        self.label_2.setText(_translate("Form", "Material lower", None))
        self.label.setText(_translate("Form", "Material upper", None))
        self.lineEdit_2.setText(_translate("Form", "layerPercent", None))
        self.lineEdit.setText(_translate("Form", "layerPercent", None))
        self.pushButton.setText(_translate("Form", "Confirm", None))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = Ui_Form()
    ex.show()
    app.exit(app.exec_())