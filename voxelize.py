from meshLib import *
import numpy
import cPickle as pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def execution(fileName,direction):
	try:
		vertices,triangles=loadmesh(fileName)
		res=float(0.999)
		result=voxelize(vertices,triangles,res,direction)
		fname=fileName[:-4]+"vox"
		print "...saving voxel data to: "+fname
		f=gzip.open(fname,"wb")
		pickle.dump(result,f)
		return True
	except:
		print "Something wasn't right....\n\tcorrect usage: python voxelize.py <mesh file> <resolution>"
		return False
	
if __name__ == "__main__":
	execution("../sphere.mesh")

