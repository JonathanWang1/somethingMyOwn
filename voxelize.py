from meshLib import *
import numpy
import cPickle as pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
import os.path
from fileinput import filename
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class Voxelize:
	def execution(self, fileName,direction, sliceInt):
		try:
			self.vox = meshLib()
			vertices,triangles = self.vox.loadmesh(fileName)
			#slices = 101
			#res=float(0.999)
			result=self.vox.voxelize1(vertices,triangles,sliceInt,direction)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
	
	def execution2(self, fileName, planeOrigin, planeNormal):
		try:
			
			vertices,triangles=self.vox.loadmesh(fileName)
			#slices = 101
			#res=float(0.999)
			result=self.vox.voxelize2(vertices,triangles, planeOrigin, planeNormal)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution3(self, fileName, pointValue):
		try:
			
			#vertices,triangles=self.vox.loadmesh(fileName)
			result=self.vox.voxelize3(pointValue)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
	
	def execution4(self, fileName, materials):
		try:
			result=self.vox.voxelize4(materials)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution5(self, fileName):
		try:
			result=self.vox.voxelRadience()
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution6(self, fileName, size, sigma):
		try:
			result=self.vox.voxelfilterPrepare(size, sigma)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution7(self, fileName, triangleSelected, depth, materials):
		try:
			result=self.vox.depthFaceSelect(triangleSelected, depth, materials)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution8(self, fileName, size, materials):
		try:
			result=self.vox.voxelfilterPrepareForAverage(size, materials)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution9(self, fileName, materialSet, materialNumber, ratioArray):
		try:
			result=self.vox.deadPointAdd(materialSet, materialNumber, ratioArray)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
	def execution10(self, fileName, materials, materialNumber):
		try:
			result=self.vox.showIndependent(materials, materialNumber)
			fnameR=fileName[:-4]+"voxr"
			fnameG=fileName[:-4]+"voxg"
			fnameB=fileName[:-4]+"voxb"
			print "...saving voxel data to: "+fnameR
			fr=gzip.open(fnameR,"wb")
			pickle.dump(result[0],fr)
			fg=gzip.open(fnameG,"wb")
			pickle.dump(result[1],fg)
			fb=gzip.open(fnameB,"wb")
			pickle.dump(result[2],fb)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False		
		
if __name__ == "__main__":
	voxelize = Voxelize()
	voxelize.execution("../sphere.mesh")

