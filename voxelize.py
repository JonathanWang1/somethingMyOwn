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
			vertices,triangles=self.vox.loadmesh(fileName)
			#slices = 101
			#res=float(0.999)
			result=self.vox.voxelize1(vertices,triangles,sliceInt,direction)
			fname=fileName[:-4]+"vox"
			print "...saving voxel data to: "+fname
			f=gzip.open(fname,"wb")
			pickle.dump(result,f)
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
			fname=fileName[:-4]+"vox"
			print "...saving voxel data to: "+fname
			f=gzip.open(fname,"wb")
			pickle.dump(result,f)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
		
	def execution3(self, fileName, pointValue):
		try:
			
			#vertices,triangles=self.vox.loadmesh(fileName)
			result=self.vox.voxelize3(pointValue)
			fname=fileName[:-4]+"vox"
			print "...saving voxel data to: "+fname
			f=gzip.open(fname,"wb")
			pickle.dump(result,f)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False
	
	def execution4(self, fileName, planeOrigin, planeNormal, pointValue, planeWeight, pointWeight):
		try:
			result=self.vox.voxelize4(planeOrigin, planeNormal, pointValue, planeWeight, pointWeight)
			fname=fileName[:-4]+"vox"
			print "...saving voxel data to: "+fname
			f=gzip.open(fname,"wb")
			pickle.dump(result,f)
			return True
		except:
			print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
			return False		
	
if __name__ == "__main__":
	voxelize = Voxelize()
	voxelize.execution("../sphere.mesh")

