import sys
import numpy
import multiprocessing
import cPickle as pickle
import gzip
import itertools
from functools import partial
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
from numpy import uint8
import math
import scipy.ndimage
from scipy.spatial import ConvexHull
import pointTriDistance
from scipy import ndimage
import gaussianOperation
import averageOperation
from sympy.strategies.core import switch

class meshLib:
	def executionTime(self, method):
		'''Decorator function for timing of the input function.'''
		def timed(*args, **kw):
			ts = time.time()
			result = method(*args, **kw)
			total = time.time()-ts
			if total<1:
				report="\"{0:}\" executed in {1:2.6f} ms."
				print report.format(method.__name__, total*1000)
			else:
				report="\"{0:}\" executed in {1:2.2f} seconds."
				print report.format(method.__name__, total)
			return result
		return timed

	def loadmesh(self, fname):
		f=gzip.open(fname,"rb")
		vertices,triangles=loaddata=pickle.load(f)
		f.close()
		return vertices,triangles

	def linesegment_plane_intersection(self, p0,p1,point,normal): # only returns lines...intersections through the segment end points are ignored
		"""linesegment_plane_intersection(p0,p1,point,normal) -- Finds the intersection of the segment p0->p1 and the plane defined by point and normal.'''"""
		p0dot=numpy.dot(p0-point,normal)
		p1dot=numpy.dot(p1-point,normal)
		if (p0dot>0 and p1dot<0) or (p0dot<0 and p1dot>0): 
			# if the dot products have opposing signs, then the line intersects the plane
			return True,p0+(p1-p0)*abs(p0dot)/(abs(p0dot)+abs(p1dot))
		else:
			return False

	def chunks(self, l, n): 
		'''chunks(l, n) -- Divide list l into n equal-ish pieces.'''
		size=int(len(l)/n)+1
		return [l[i:i+size] for i in range(0, len(l), size)]

	def find_boundbox(self, pointcloud):
		"""find_boundbox(pointcloud) -- Finds the bounding box of the list of points in pointcloud."""
		pointcloud=numpy.array(pointcloud) 
		lowerleftcorner=numpy.min(pointcloud,0)
		upperrightcorner=numpy.max(pointcloud,0)
		return lowerleftcorner,upperrightcorner

	def idx(self,P,R):
		'''Returns the index of point P in a voxel system of resolution R.'''
		return numpy.ceil(P/R)

	def triangle_plane_intersection(self,p0,p1,p2,point,normal):
		"""Computes the intersection of a triangle defined by p0, p1, and p2 with a plane defined by point and normal.  Can return 0-3 points, depending on the condition. -- triangle_plane_intersection(p0,p1,p2,point,normal)"""
		tol=0.00001
	
		# handle all of the stupid cases before we do costly math
	
		#basic stuff
		p0dp=numpy.dot(p0-point,normal)
		p1dp=numpy.dot(p1-point,normal)
		p2dp=numpy.dot(p2-point,normal)
		p0ip=numpy.abs(p0dp)<tol # p0 in-plane
		p1ip=numpy.abs(p1dp)<tol # p1 in-plane
		p2ip=numpy.abs(p2dp)<tol # p02in-plane

		# are all vertices of the triangle in the plane?
		if (p0ip)&(p1ip)&(p2ip): # yes, triangle is in the plane
			return [p0,p1,p2]
	
		# are all vertices of the triangle on the same side?
		if (not(p0ip))&(not(p1ip))&(not(p2ip))&(numpy.sign(p0dp)==numpy.sign(p1dp))&(numpy.sign(p0dp)==numpy.sign(p2dp)): # yup, they are all on the same side
			return []
	
		# is one vertex in the plane?
		if (p0ip)&(not(p1ip))&(not(p2ip)): #just p0 in plane
			return [p0]
		elif (not(p0ip))&(p1ip)&(not(p2ip)): #just p1 in plane
			return [p1]
		elif (not(p0ip))&(not(p1ip))&(p2ip): #just p2 in plane
			return [p2]
	
		# is one line of the triangle in the plane?
		if (p0ip)&(p1ip)&(not(p2ip)): #L1 in plane
			return [p0,p1]
		elif (not(p0ip))&(p1ip)&(p2ip): #L2 in plane
			return [p1,p2]
		elif (p0ip)&(not(p1ip))&(p2ip): #L3 in plane
			return [p0,p2]
	
		# if we have gotten this far, we have to actually calculate intersections
		if numpy.sign(p0dp)==numpy.sign(p1dp):
			l2b,l2i=self.linesegment_plane_intersection(p1,p2,point,normal)
			l3b,l3i=self.linesegment_plane_intersection(p0,p2,point,normal)
			if (l2b)&(l3b): #sanity check only, should always be true
				return [l2i,l3i]
		elif numpy.sign(p2dp)==numpy.sign(p1dp):
			l1b,l1i=self.linesegment_plane_intersection(p0,p1,point,normal)
			l3b,l3i=self.linesegment_plane_intersection(p0,p2,point,normal)
			if (l1b)&(l3b): #sanity check only, should always be true
				return [l1i,l3i]
		else:
			l1b,l1i=self.linesegment_plane_intersection(p0,p1,point,normal)
			l2b,l2i=self.linesegment_plane_intersection(p1,p2,point,normal)
			if (l1b)&(l2b): #sanity check only, should always be true
				return [l1i,l2i]
	
		# If the function makes it this far, I have no idea what is going on.
		return "bananna pants"

	def find_intersection_contours(self, vertices,triangles,point,normal,tol=0.0001):
	# first, calculate all the intersections
		intersection_results=[self.triangle_plane_intersection(vertices[V[0]],vertices[V[1]],vertices[V[2]],point,normal) for V in triangles]
	
		# sort the intersections into contours
		
		contours=[] # container of contours
		lines_to_process=[]
		
		
		# next sort out the lines and triangles (which are already contours in the current plane)
		for isect in intersection_results:
			if len(isect)==2: # if it is a line
				lines_to_process.append(isect) # add it to the lines to sequence
			elif len(isect)==3: # if it is a whole triangle
				contours.append(isect) # add it to the contours
		
		# sort the lines into individual contours
		newContourNeeded=True
		while len(lines_to_process)>0:
			if newContourNeeded: # if we need to start a new contour
				contours.append(lines_to_process.pop(0)) # add the first line
				newContourNeeded=False
			lines_left=[]
			foundOne=False
			for line in lines_to_process:
				if numpy.linalg.norm(line[0]-contours[-1][-1])<tol: # line fits end
					contours[-1].append(line[1])
					#print "EF"
					foundOne=True
				elif numpy.linalg.norm(line[1]-contours[-1][-1])<tol: # line fits end backwards
					contours[-1].append(line[0])
					foundOne=True
					#print "ER"
				elif numpy.linalg.norm(line[0]-contours[-1][0])<tol: # line fits front
					contours[-1].insert(0,line[1])
					foundOne=True
					#print "FF"
				elif numpy.linalg.norm(line[1]-contours[-1][0])<tol: # line fits front backwards
					contours[-1].insert(0,line[0])
					foundOne=True
					#print "FR"
				else:
					lines_left.append(line)
			
			lines_to_process=lines_left
			if not(foundOne):
				newContourNeeded=True
		
		return contours
	
	def findSelectedContour(self, vertices,triangleSelected, point, normal):
		intersection_results=[self.triangle_plane_intersection(vertices[V[0]],vertices[V[1]],vertices[V[2]],point,normal) for V in triangleSelected]
		# sort the intersections into contours
		contours=[] # container of contours
		lines_to_process=[]
		# next sort out the lines and triangles (which are already contours in the current plane)
		for isect in intersection_results:
			if len(isect)==2: # if it is a line
				lines_to_process.append(isect) # add it to the lines to sequence
			elif len(isect)==3: # if it is a whole triangle
				#contours.append(isect) # add it to the contours
				lines_to_process.append([isect[0], isect[1]])
				lines_to_process.append([isect[1], isect[2]])
				lines_to_process.append([isect[2], isect[0]])
		return lines_to_process
		
	def prepare_voxel_slice(self,slices,llc,urc,direction):
		"""Builds a single layer container for the voxelizer routine. -- prepare_voxel_slice(size,res)"""
		size=urc-llc
		res = float(size[direction] / slices)
		dims=numpy.ceil(size/res)
		return numpy.zeros((dims[(direction+1) % 3],dims[(direction+2) % 3]),dtype='bool'), res

	def voxelize_single_contour(self, contour,res,llc,voxSlice, direction):
		"""Creates a single voxel slice from the provided contour. -- voxelize_single_contour(contour,res,llc,voxSlice)"""
		# prepare contour for the point check
		verts = [ (P[(direction + 1) % 3],P[(direction + 2) % 3]) for P in contour ]
		verts.append((contour[0][(direction + 1) % 3],contour[0][(direction + 2) % 3]))
		codes = [Path.MOVETO]
		[codes.append(Path.LINETO) for i in range(len(verts)-2)]
		codes.append(Path.CLOSEPOLY)
		path = Path(verts, codes)
		
		# prepare the list of points to check
		indices=numpy.transpose(numpy.array(numpy.nonzero(voxSlice==False)))
		positions=[(p[0],p[1]) for p in list(indices*res+numpy.array([llc[(direction + 1) % 3],llc[(direction + 2) % 3]]))]
		
		# do the check and reshape the result
		result=numpy.array(path.contains_points(positions),dtype='bool').reshape(voxSlice.shape)
		
		return result
	

							
	def voxelize_contours(self, contours,res,llc,voxSlice, direction):
		"""Creates a single voxel slice from the provided set of contours, finding . -- voxelize_contour(contours,res,llc,voxSlice)"""
		# generate each voxel slice
		vslices=[self.voxelize_single_contour(contour,res,llc,voxSlice, direction) for contour in contours]
		if len(vslices)>0:
			result=vslices.pop(0)
			for S in vslices:
				result=numpy.logical_xor(result,S)
			return result
		else:
			return voxSlice

	def voxel_slice(self,slicePoint,points,triangles,res,llc,sliceProto,direction):
		"""Creates contours at the given slicePoint, then converts the slice to a voxel slice. -- voxel_slice(points,triangles,slicePoint,res,llc,urc)"""
		def getDirectionArray(x):
			return {
				0:numpy.array([1,0,0]),
				1:numpy.array([0,1,0]),
				2:numpy.array([0,0,1]),
				}.get(x, numpy.array([0,0,1]))
		
		directionArray = getDirectionArray(direction)

		contours=self.find_intersection_contours(points,triangles,slicePoint, directionArray)
		contours2=self.find_intersection_contours(points,triangles,slicePoint+directionArray*0.001,directionArray)
		contours3=self.find_intersection_contours(points,triangles,slicePoint-directionArray*0.001,directionArray)
		#result=numpy.array(voxelize_contours(contours,res,llc,sliceProto),dtype='int64')
		#result2=numpy.array(voxelize_contours(contours2,res,llc,sliceProto),dtype='int64')
		#result3=numpy.array(voxelize_contours(contours3,res,llc,sliceProto),dtype='int64')
		#print numpy.sum(result),numpy.sum(result2),numpy.sum(result3)
		#fixedResult=numpy.zeros(result.shape,dtype='bool')
		#fixedResult[numpy.nonzero(result+result2+result3>=2)]=True # set to True if the voxel is present in 2 of 3 slices
		result=self.voxelize_contours(contours,res,llc,sliceProto, direction)
		result2=self.voxelize_contours(contours2,res,llc,sliceProto, direction)
		result3=self.voxelize_contours(contours3,res,llc,sliceProto, direction)
		fixedResult=(result&result2)|(result&result3)|(result3&result2)
		return fixedResult

	def point_list(self,res,llc,urc,direction):
		""" prepares a list of points for every XY plane slice, with a distance apart of res in the z direction, though the bound box defined by the corners llc and urc. --  point_list(res,llc,urc)"""
		if direction == 2:
			Zdist=urc[2]-llc[2]
			numPoints=int(numpy.ceil(Zdist/res))
			deltaZ=Zdist/numPoints
			points=[llc+numpy.array([0,0,deltaZ*i]) for i in range(numPoints)]
			return points, points[0], points[-1]
		if direction == 1:
			Zdist=urc[1]-llc[1]
			numPoints=int(numpy.ceil(Zdist/res))
			deltaZ=Zdist/numPoints
			points=[llc+numpy.array([0,deltaZ*i,0]) for i in range(numPoints)]
			return points, points[0], points[-1]
		if direction == 0:
			Zdist=urc[0]-llc[0]
			numPoints=int(numpy.ceil(Zdist/res))
			deltaZ=Zdist/numPoints
			points=[llc+numpy.array([deltaZ*i,0,0]) for i in range(numPoints)]
			return points, points[0], points[-1]		

	def voxelize1(self,points,triangles,slices, direction):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""
		
		self.dirction = direction
		self.vertices = points
		self.triangles = triangles
	
		llc,urc=self.find_boundbox(points) # find the lower left corner (llc) and upper right corner (urc) of the vertices
		self.llc = llc
		self.urc = urc
		
		sliceProto, res=self.prepare_voxel_slice(slices,llc,urc,direction) # create the prototype slice volume for the voxel slicing
		self.res = res
		self.sliceProto = sliceProto
		
		self.slicePoints, minPoints, maxPoints=self.point_list(res,llc,urc,direction) # prepare the list of points to slice at
	
	#partialVoxelSlicer=partial(voxel_slice,points=points,triangles=triangles,res=res,llc=llc,sliceProto=sliceProto) # prepare a single-input version of the voxel slicer for parallelization
	
	#pool=multiprocessing.Pool(processes=max(1,multiprocessing.cpu_count()-1)) 
	
	#layers=pool.map(partialVoxelSlicer,slicePoints) # perform the voxel conversion
	
	#volume=numpy.array(layers,dtype='bool') # create the 3d volume
	
	#return volume
		layersR = list()
		layersG = list()
		layersB = list()
		volumeGeneral = list()
		self.boolLayers = list()
		#self.boolResult = list()
		#maxArray = numpy.amax(slicePoints, axis=0)
		#minArray = numpy.amin(slicePoints, axis=0)
		self.maxValue = maxPoints[direction]
		self.minValue = minPoints[direction]
		self.ratio = 255 / (self.maxValue - self.minValue)
		for i in self.slicePoints:
			boolResult = self.voxel_slice(i, points, triangles, res, llc, sliceProto, direction)
			print boolResult.shape
			tupleResultR = numpy.zeros(boolResult.shape, dtype=uint8)
			tupleResultG = numpy.zeros(boolResult.shape, dtype=uint8)
			tupleResultB = numpy.zeros(boolResult.shape, dtype=uint8)
			#tupleResult.astype(uint8)
			j = numpy.nditer(boolResult, flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
					#tupleResult[j.multi_index] = round((i[direction] - minValue) * self.ratio) + 1
					#tupleResult[j.multi_index] = 78
					tupleResultR[j.multi_index] = 0
					tupleResultG[j.multi_index] = 255
					tupleResultB[j.multi_index] = 255					
				else:
					tupleResultR[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultB[j.multi_index] = 0
				j.iternext()
			self.boolLayers.append(boolResult)
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
		print "i got here"
		volumeR=numpy.array(layersR) # create the 3d volume
		volumeG=numpy.array(layersG) 
		volumeB=numpy.array(layersB)
		volumeGeneral.append(volumeR)
		volumeGeneral.append(volumeG)
		volumeGeneral.append(volumeB)
		
		f1=open('./cube.txt', 'w+')
		print >> f1, self.boolLayers
		return volumeGeneral
	"""
	def voxelize2(self, points,triangles, planeOrigin, planeNormal):
		
		 Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)
		
		#layers = list()
		layersR = list()
		layersG = list()
		layersB = list()
		volumeGeneral = list()
		m = 0
		for i in self.slicePoints:
			#print self.boolResult[m].shape
			#tupleResult = numpy.zeros(self.boolLayers[m].shape, dtype=int)
			tupleResultR = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleResultG = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleResultB = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			
			#tupleResult.astype(uint8)
			j = numpy.nditer(self.boolLayers[m], flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
				#tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio)
				#tupleResult[j.multi_index] = 78
					print type(j.multi_index)
					print j.multi_index
					tupleResultR[j.multi_index] = math.fabs((j.multi_index[1] - planeOrigin[0]) * planeNormal[0] + (j.multi_index[0] - planeOrigin[1]) * planeNormal[1] + (i[2] - planeOrigin[2]) * planeNormal[2]) * 2.0
					tupleResultG[j.multi_index] = 255 - math.fabs((j.multi_index[1] - planeOrigin[0]) * planeNormal[0] + (j.multi_index[0] - planeOrigin[1]) * planeNormal[1] + (i[2] - planeOrigin[2]) * planeNormal[2]) * 2.0
					tupleResultB[j.multi_index] = 255
					#if(tupleResultR[j.multi_index] > 0):
					tupleResultR[j.multi_index] = round(tupleResultR[j.multi_index])+1
					tupleResultG[j.multi_index] = round(tupleResultG[j.multi_index])
					#if(tupleResultR[j.multi_index] == 0):
					#	tupleResultR[j.multi_index] = 1
					#if(tupleResultR[j.multi_index] < 0):
					#	tupleResultR[j.multi_index] = round(0 - tupleResultR[j.multi_index])+1
				else:
					tupleResultR[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultB[j.multi_index] = 0
				j.iternext()
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
			m = m + 1
		print "i got here"
		#volume=numpy.array(layers) # create the 3d volume
		volumeR=numpy.array(layersR) # create the 3d volume
		volumeG=numpy.array(layersG) 
		volumeB=numpy.array(layersB)
		volumeGeneral.append(volumeR)
		volumeGeneral.append(volumeG)
		volumeGeneral.append(volumeB)
		return volumeGeneral
	
	def voxelize3(self, pointValue):
		
		Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)
		
		layersR = list()
		layersG = list()
		layersB = list()
		volumeGeneral = list()
		m = 0
		for i in self.slicePoints:
			#print self.boolResult[m].shape
			tupleResultR = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleResultG = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleResultB = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			#tupleResult = numpy.zeros(self.boolLayers[m].shape, dtype=int)
			#tupleResult.astype(uint8)
			j = numpy.nditer(self.boolLayers[m], flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
				#tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio)
				#tupleResult[j.multi_index] = 78
					print type(j.multi_index)
					print j.multi_index
					tupleResultR[j.multi_index] = 0
					tupleResultG[j.multi_index] = (math.sqrt(math.pow((j.multi_index[1]- pointValue[0]),2) + math.pow((j.multi_index[0] - pointValue[1]), 2)+math.pow((i[2] - pointValue[2]),2))) * 1.5
					tupleResultB[j.multi_index] = 255 - (math.sqrt(math.pow((j.multi_index[1]- pointValue[0]),2) + math.pow((j.multi_index[0] - pointValue[1]), 2)+math.pow((i[2] - pointValue[2]),2))) * 1.5				
					
					tupleResultR[j.multi_index] = round(tupleResultR[j.multi_index])+1
					tupleResultG[j.multi_index] = round(tupleResultG[j.multi_index])					
					#if(tupleResult[j.multi_index] > 0):
					#	tupleResult[j.multi_index] = round(tupleResult[j.multi_index])+1
					#if(tupleResult[j.multi_index] == 0):
					#	tupleResult[j.multi_index] = 1
					#if(tupleResult[j.multi_index] < 0):
					#	tupleResult[j.multi_index] = round(0 - tupleResult[j.multi_index])+1
				else:
					tupleResultR[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultB[j.multi_index] = 0
				j.iternext()
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
			m = m + 1
		print "i got here"
		volumeR=numpy.array(layersR) # create the 3d volume
		volumeG=numpy.array(layersG) 
		volumeB=numpy.array(layersB)
		volumeGeneral.append(volumeR)
		volumeGeneral.append(volumeG)
		volumeGeneral.append(volumeB)
		return volumeGeneral
	"""
	def voxelize4(self, materials):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""
		layers = list()
		layersR = list()
		layersG = list()
		layersB = list()
		
		layerMaterial = list()
		self.volumeComposition = list()
		for l in range(len(materials)):
			layerMaterial.append(list())
			self.volumeComposition.append(list())

		volumeGeneral = list()
		m = 0
		for i in self.slicePoints:
			#print self.boolResult[m].shape
			tupleResultR = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleResultG = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleResultB = numpy.zeros(self.boolLayers[m].shape, dtype=uint8)
			tupleMaterial = list()
			for l in range(len(materials)):
				tupleMaterial.append(numpy.zeros(self.boolLayers[m].shape, dtype=float))
			
			j = numpy.nditer(self.boolLayers[m], flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
				#tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio)
				#tupleResult[j.multi_index] = 78
					print type(j.multi_index)
					print j.multi_index
					#tupleResult[j.multi_index] = planeWeight * math.fabs((j.multi_index[1] - planeOrigin[0]) * planeNormal[0] + (j.multi_index[0] - planeOrigin[1]) * planeNormal[1] + (i[2] - planeOrigin[2]) * planeNormal[2]) + pointWeight * math.sqrt(math.pow((j.multi_index[1]- pointValue[0]),2) + math.pow((j.multi_index[0] - pointValue[1]), 2)+math.pow((i[2] - pointValue[2]),2))
					
					distanceList = []
					totalDistance = 0.0
					for k in range(len(materials)):
						if materials[k].controlSourceType == "Plane":
							Gplane = math.fabs((j.multi_index[1] - materials[k].origin[0]) * materials[k].normal[0] + (j.multi_index[0] - materials[k].origin[1]) * materials[k].normal[1] + (i[2] - materials[k].origin[2]) * materials[k].normal[2])
							distanceList.append(Gplane)
							totalDistance += Gplane
						if materials[k].controlSourceType == "Point":
							Gpoint = (math.sqrt(math.pow((j.multi_index[1]- materials[k].point[0]),2) + math.pow((j.multi_index[0] - materials[k].point[1]), 2)+math.pow((i[2] - materials[k].point[2]),2)))
							distanceList.append(Gpoint)
							totalDistance += Gpoint
					for k in range(len(distanceList)):
						distanceList[k] = distanceList[k] / totalDistance
						distanceList[k] = 1.0 - distanceList[k]
						
						tupleMaterial[k][j.multi_index] = distanceList[k]
						
						tupleResultR[j.multi_index] += materials[k].materialColor[0] * distanceList[k] * materials[k].weight
						tupleResultG[j.multi_index] += materials[k].materialColor[1] * distanceList[k] * materials[k].weight
						tupleResultB[j.multi_index] += materials[k].materialColor[2] * distanceList[k] * materials[k].weight
					#if(tupleResult[j.multi_index] > 0):
					#	tupleResult[j.multi_index] = round(tupleResult[j.multi_index]) 
					#if(tupleResult[j.multi_index] == 0):
					#		tupleResult[j.multi_index] = 1
					#if(tupleResult[j.multi_index] < 0):
					#	tupleResult[j.multi_index] = round(0 - tupleResult[j.multi_index]) 
				else:
					tupleResultR[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultB[j.multi_index] = 0
					for k in range(len(materials)):
						tupleMaterial[k][j.multi_index] = 0.0
				j.iternext()
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
			for k in range(len(materials)):
				layerMaterial[k].append(tupleMaterial[k])
				
			m = m + 1
		print "i got here"
		volumeR=numpy.array(layersR) # create the 3d volume
		volumeG=numpy.array(layersG) 
		volumeB=numpy.array(layersB)
		for k in range(len(materials)):
			self.volumeComposition[k] = numpy.array(layerMaterial[k])
		
		volumeGeneral.append(volumeR)
		volumeGeneral.append(volumeG)
		volumeGeneral.append(volumeB)
		return volumeGeneral
	#get surface, only one layer, inside and outside voxels are all zeros  
	def getSurfaceBool(self, layers):
		erosionBool = scipy.ndimage.binary_erosion(layers).astype(layers.dtype)
		newBool = layers - erosionBool
		return newBool
	
	#get the inner part
	def getInnerBool(self, layers):
		erosionBool = scipy.ndimage.binary_erosion(layers).astype(layers.dtype)
		return erosionBool
		
	def voxelRadience(self):
		layerNumber = 1 #record the layer number
		volumeGeneral = list()#store three RGB numpy array
		
		boolLayersNumpy = numpy.array(self.boolLayers)
		#test
		boolLayersNumpy = numpy.ones((50,50,50))
		with file('cube.txt', 'w') as outfile1:
			for data_slice1 in boolLayersNumpy:

		# The formatting string indicates that I'm writing out
		# the values in left-justified columns 7 characters in width
		# with 2 decimal places.  
				numpy.savetxt(outfile1, data_slice1,fmt='%-7.1f')

		# Writing out a break to indicate different slices...
				outfile1.write('# New slice\n')
		print boolLayersNumpy.shape
		layers = numpy.zeros(boolLayersNumpy.shape, dtype=uint8) #layer information, each layer stores a different layer number
		volumeR = numpy.zeros(boolLayersNumpy.shape, dtype=uint8)#color information
		volumeB = numpy.zeros(boolLayersNumpy.shape, dtype=uint8)
		volumeG = numpy.zeros(boolLayersNumpy.shape, dtype=uint8)
		
		#assign layer number to each specific layer
		newBool = self.getSurfaceBool(boolLayersNumpy)
		newInner = self.getInnerBool(boolLayersNumpy)
		while(1):
			if True in newBool:
				#search the surface thoroughly
				j = numpy.nditer(newBool, flags=['multi_index'], op_flags=['readwrite'])
				while not j.finished:
					if j[0] == True:
						layers[j.multi_index] = layerNumber
					j.iternext()						
				newBool = self.getSurfaceBool(newInner)
				newInner = self.getInnerBool(newInner)
				layerNumber = layerNumber + 1
				print layerNumber
			else:
				break
			
		colorInterval = 255.0 / layerNumber #get the relative interval
		#use the layer and colorInterval informatin, assign RGB value to volume
		k = numpy.nditer(layers, flags=['multi_index'], op_flags=['readwrite'])
		while not k.finished:
			if layers[k.multi_index] != 0:
				volumeR[k.multi_index] = layers[k.multi_index] * colorInterval
				volumeB[k.multi_index] = 255 - layers[k.multi_index] * colorInterval
			k.iternext()
		volumeGeneral.append(volumeR)
		volumeGeneral.append(volumeG)
		volumeGeneral.append(volumeB)
		#f2 = open("./layer.txt","w+")
		#numpy.savetxt('./layer.out', layers)
		with file('layer.txt', 'w') as outfile:
			for data_slice in volumeR:

		# The formatting string indicates that I'm writing out
		# the values in left-justified columns 7 characters in width
		# with 2 decimal places.  
				numpy.savetxt(outfile, data_slice,fmt='%-7.1f')

		# Writing out a break to indicate different slices...
				outfile.write('# New slice\n')
		return volumeGeneral
	
	def voxelfilterPrepare(self, size, sigma):
		volumeGeneral = list()
		
		gaussionClass = gaussianOperation.gaussianOperation()
		boolArray = numpy.array(self.boolLayers)
		
		for l in range(len(materials)):
			self.volumeComposition[l] = gaussionClass.do(size, sigma, self.volumeComposition[l], boolArray)
		
		volumeShape = self.volumeComposition[0].shape	
		for i in range(volumeShape[0]):
			for j in range(volumeShape[1]):
				for k in range(volumeShape[2]):
					sum = 0
					for l in range(len(materials)):
						sum += self.volumeComposition[l][i][j][k]
					if sum > 0.0000000001:
						for l in range(len(materials)):
							self.volumeComposition[l][i][j][k] = self.volumeComposition[l][i][j][k] / sum
			
		self. volumeB = gaussionClass.do(size,sigma,self.volumeB,boolArray)
		self. volumeG = gaussionClass.do(size,sigma,self.volumeG,boolArray)
		self. volumeR = gaussionClass.do(size,sigma,self.volumeR,boolArray)
		
		#ndimage.gaussian_filter(self.volumeB, sigma=3, output = self.volumeB, mode = 'nearest')
		#ndimage.gaussian_filter(self.volumeG, sigma=3, output = self.volumeG, mode = 'nearest')
		#ndimage.gaussian_filter(self.volumeR, sigma=3, output = self.volumeR, mode = 'nearest')
		volumeGeneral.append(self.volumeR)
		volumeGeneral.append(self.volumeG)
		volumeGeneral.append(self.volumeB)
		return volumeGeneral
	
	def voxelfilterPrepareForAverage(self,size, materials):
		volumeGeneral = list()
		
		averageClass = averageOperation.averageOperation()
		boolArray = numpy.array(self.boolLayers)
		
		for l in range(len(materials)):
			self.volumeComposition[l] = averageClass.do(size, self.volumeComposition[l], boolArray)
			
		volumeShape = self.volumeComposition[0].shape	
		for i in range(volumeShape[0]):
			for j in range(volumeShape[1]):
				for k in range(volumeShape[2]):
					sum = 0
					for l in range(len(materials)):
						sum += self.volumeComposition[l][i][j][k]
					if sum > 0.0000000001:
						for l in range(len(materials)):
							self.volumeComposition[l][i][j][k] = self.volumeComposition[l][i][j][k] / sum
					
		self.volumeB = averageClass.do(size,self.volumeB,boolArray)
		self.volumeG = averageClass.do(size,self.volumeG,boolArray)
		self.volumeR = averageClass.do(size,self.volumeR,boolArray)
		
		#ndimage.gaussian_filter(self.volumeB, sigma=3, output = self.volumeB, mode = 'nearest')
		#ndimage.gaussian_filter(self.volumeG, sigma=3, output = self.volumeG, mode = 'nearest')
		#ndimage.gaussian_filter(self.volumeR, sigma=3, output = self.volumeR, mode = 'nearest')
		volumeGeneral.append(self.volumeR)
		volumeGeneral.append(self.volumeG)
		volumeGeneral.append(self.volumeB)
		return volumeGeneral
	
	def lengthSquare(self, startPoint, endPoint):
		value = (startPoint[0] - endPoint[0]) * (startPoint[0] - endPoint[0]) + (startPoint[1] - endPoint[1]) * (startPoint[1] - endPoint[1]) + (startPoint[2] - endPoint[2]) * (startPoint[2] - endPoint[2])
		return value
	def lengthOne(self, startPoint, endPoint):
		value = self.lengthSquare(startPoint, endPoint)
		value = math.sqrt(value)
		return value
	def pointSubtraction(self, startPoint, endPoint):
		value = []
		value.append(endPoint[0] - startPoint[0])
		value.append(endPoint[1] - startPoint[1])
		value.append(endPoint[2] - startPoint[2])
		return value
	
	def pointToSegment(self, startPoint, endPoint, targetPoint):
		l2 = self.lengthSquare(startPoint, endPoint)
  		if abs(l2) < 0.0001:
  			return self.lengthOne(startPoint, targetPoint)
  		t = max(0, min(1, numpy.dot(self.pointSubtraction(startPoint, targetPoint), self.pointSubtraction(startPoint, endPoint)) / l2))
  		projection = startPoint + t * (endPoint - startPoint)
  		return self.lengthOne(projection, targetPoint)
	
	def findVoxelOfSelectedContour(self, slicePoint, vertices, selectedTriangle, res, llc, voxSlice, depth):		
		pointFind = []	
		positions = []	
		indices=numpy.transpose(numpy.array(numpy.nonzero(voxSlice==False)))
		
		for indice in indices:
			p = []
			temp = indice * res + numpy.array([llc[0],llc[1]])
			p.append(temp[0])
			p.append(temp[1])
			p.append(slicePoint[2])
			p.append(indice[0])
			p.append(indice[1])
			positions.append(p)
			
		lengthAC = depth * res
		for V in selectedTriangle:
			triPoint = numpy.array( [vertices[V[0]],vertices[V[1]],vertices[V[2]]] ) 
			
			for pos in positions:
				posLeft = numpy.array([pos[3], pos[4]])
				pos = numpy.array([pos[0],pos[1],pos[2]])
				if lengthAC >= pointTriDistance.pointTriangleDistance(triPoint, pos):
					pointFind.append([posLeft[0], posLeft[1]])
		result = numpy.zeros(voxSlice.shape, dtype=bool)
		for selectPoint in pointFind:
			result[selectPoint[0], selectPoint[1]] = True
		return result
	
	def depthFaceSelect(self, triangleSelected,depth, materials):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""	
		layersR = list()
		layersG = list()
		layersB = list()
		
		layerMaterial = list()
		self.volumeComposition = list()
		for l in range(len(materials)):
			layerMaterial.append(list())
			self.volumeComposition.append(list())
		
		volumeGeneral = list()
		self.boolLayers = []
		
		for i in self.slicePoints:
			boolResult2 = self.voxel_slice(i, self.vertices, self.triangles, self.res, self.llc, self.sliceProto, 2)
			print boolResult2.shape
			tupleResultR = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleResultG = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleResultB = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleMaterial = list()
			for l in range(len(materials)):
				tupleMaterial.append(numpy.zeros(boolResult2.shape, dtype=float))
			#tupleMaterial = numpy.zeros(boolResult2.shape, dtype=f)
			#lines=self.findSelectedContour(self.vertices,triangleSelected,i ,numpy.array([0,0,1]))
			#boolResult1 = self.findVoxelOfSelectedContour(i, lines, self.res, self.llc, self.sliceProto, depth)
			j = numpy.nditer(boolResult2, flags=['multi_index'], op_flags=['readwrite'])

			while not j.finished:	
				print type(j.multi_index)
				print j.multi_index
				if j[0] == True:
					tupleResultB[j.multi_index] = materials[0][0]
					tupleResultG[j.multi_index] = materials[0][1]
					tupleResultR[j.multi_index] = materials[0][2]
					tupleMaterial[0][j.multi_index] = 1.0 
				else:
					tupleResultB[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultR[j.multi_index] = 0
				j.iternext()				
					
			for k in range(len(triangleSelected)):
				boolResult1 = self.findVoxelOfSelectedContour(i, self.vertices, triangleSelected[k], self.res, self.llc, self.sliceProto, depth[k])
				boolResult = numpy.logical_and(boolResult1, boolResult2)
				print boolResult.shape

				j = numpy.nditer(boolResult2, flags=['multi_index'], op_flags=['readwrite'])
				while not j.finished:
					if j[0] == True:
						if boolResult[j.multi_index] == True:
							tupleResultB[j.multi_index] = materials[k + 1][0]
							tupleResultG[j.multi_index] = materials[k + 1][1]
							tupleResultR[j.multi_index] = materials[k + 1][2]
							tupleMaterial[k + 1][j.multi_index] = 1.0 
							tupleMaterial[0][j.multi_index] = 0.0
						#else:
						#	tupleResultB[j.multi_index] = 255
						#	tupleResultG[j.multi_index] = 0
						#	tupleResultR[j.multi_index] = 0					
					j.iternext()
			self.boolLayers.append(boolResult2)
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
			for l in range(len(materials)):
				layerMaterial[l].append(tupleMaterial[l])
				
		print "i got here"
		self.volumeR=numpy.array(layersR) # create the 3d volume
		self.volumeG=numpy.array(layersG) 
		self.volumeB=numpy.array(layersB)
		
		for l in range(len(materials)):
			self.volumeComposition[l] = numpy.array(layerMaterial[l])
		volumeGeneral.append(self.volumeR)
		volumeGeneral.append(self.volumeG)
		volumeGeneral.append(self.volumeB)
		
		return volumeGeneral
	
	def deadPointAdd(self, materials, materialNumber, ratioArray):
		"""calculate the forbidden proportion"""	
		
		"""sort the ratio arry in order"""
		sorted(ratioArray)
		
		"""find the jumpping bound"""
		boundRatio = []
		boundRatio.append(0.0)
		for ratio in ratioArray:
			boundRatio.append((ratio[0] + ratio[1]) / 2.0 / 100.0)
		boundRatio.append(1.0)
		
		"""add the beginning and finishing part in functionRatio, and put ratioArray in it"""
		lowestBound = ratioArray[0][0]
		upperestBound = ratioArray[-1][1]
		
		functionRatio = []
		functionRatio.append((0, lowestBound / 100.0))
		for i in range(len(ratioArray) - 1):
			functionRatio.append((ratioArray[i][1] / 100.0, ratioArray[i + 1][0] / 100.0))
		functionRatio.append((upperestBound, 100))
			
		""""define function for each area, calculate k(gradience) and b"""
		linearGradient = []
		linearOffset = []
		for i in range(len(boundRatio) - 1):
			x1 = boundRatio[i]
			x2 = boundRatio[i + 1]
			y1 = functionRatio[i][0]
			y2 = functionRatio[i][1]
			linearGradient.append((y2 - y1) / (x2 - x1))
			linearOffset.append((y1 * x2 - y2 * x1) / (x2 - x1))
			
		"""calculate the actual composition using the linear map"""
		volumeShape = self.volumeComposition[materialNumber].shape
		for i in range(volumeShape[0]):
			for j in range(volumeShape[1]):
				for k in range(volumeShape[2]):
					for l in range(len(boundRatio) - 1):
						if self.volumeComposition[materialNumber][i][j][k] > 0.00001 + boundRatio[l] and self.volumeComposition[materialNumber][i][j][k] <= + boundRatio[l + 1]:
							""""apply the linear function"""	
							self.volumeComposition[materialNumber][i][j][k] = linearGradient[l] * self.volumeComposition[materialNumber][i][j][k] + linearOffset[l]
							self.volumeComposition[0][i][j][k] = 1.0 - self.volumeComposition[materialNumber][i][j][k]

		"""convert volumeComposition into RGB"""						
		layersR = list()
		layersG = list()
		layersB = list()
		
		volumeGeneral = list()
		
		layNumber = -1
		for i in self.slicePoints:
			layNumber += 1
			boolResult2 = self.voxel_slice(i, self.vertices, self.triangles, self.res, self.llc, self.sliceProto, 2)
			print boolResult2.shape
			tupleResultR = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleResultG = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleResultB = numpy.zeros(boolResult2.shape, dtype=uint8)
			#tupleMaterial = numpy.zeros(boolResult2.shape, dtype=f)
			#lines=self.findSelectedContour(self.vertices,triangleSelected,i ,numpy.array([0,0,1]))
			#boolResult1 = self.findVoxelOfSelectedContour(i, lines, self.res, self.llc, self.sliceProto, depth)
			j = numpy.nditer(boolResult2, flags=['multi_index'], op_flags=['readwrite'])

			while not j.finished:	
				print type(j.multi_index)
				print j.multi_index
				if j[0] == True:
					for l in range(len(self.volumeComposition)):
						tupleResultB[j.multi_index] += materials[l].materialColor[0] * self.volumeComposition[l][layNumber][j.multi_index]
						tupleResultG[j.multi_index] += materials[l].materialColor[1] * self.volumeComposition[l][layNumber][j.multi_index]
						tupleResultR[j.multi_index] += materials[l].materialColor[2] * self.volumeComposition[l][layNumber][j.multi_index]
				else:
					tupleResultB[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultR[j.multi_index] = 0
				j.iternext()				
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
				
		print "i got here"
		self.volumeR=numpy.array(layersR) # create the 3d volume
		self.volumeG=numpy.array(layersG) 
		self.volumeB=numpy.array(layersB)

		volumeGeneral.append(self.volumeR)
		volumeGeneral.append(self.volumeG)
		volumeGeneral.append(self.volumeB)
		
		return volumeGeneral
	def showIndependent(self, materials, materialNumber):		
		layersR = list()
		layersG = list()
		layersB = list()
		
		volumeGeneral = list()
		
		targetMaterial = self.volumeComposition[materialNumber]
		
		layNumber = -1
		for i in self.slicePoints:
			layNumber += 1
			boolResult2 = self.voxel_slice(i, self.vertices, self.triangles, self.res, self.llc, self.sliceProto, 2)
			print boolResult2.shape
			tupleResultR = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleResultG = numpy.zeros(boolResult2.shape, dtype=uint8)
			tupleResultB = numpy.zeros(boolResult2.shape, dtype=uint8)
			targetLayer = targetMaterial[layNumber]
			#tupleMaterial = numpy.zeros(boolResult2.shape, dtype=f)
			#lines=self.findSelectedContour(self.vertices,triangleSelected,i ,numpy.array([0,0,1]))
			#boolResult1 = self.findVoxelOfSelectedContour(i, lines, self.res, self.llc, self.sliceProto, depth)
			j = numpy.nditer(boolResult2, flags=['multi_index'], op_flags=['readwrite'])

			while not j.finished:	
				print type(j.multi_index)
				print j.multi_index
				if j[0] == True:
					tupleResultB[j.multi_index] = 255 * (1.0 - targetLayer[j.multi_index]) + materials[materialNumber].materialColor[0] * targetLayer[j.multi_index]
					tupleResultG[j.multi_index] = 255 * (1.0 - targetLayer[j.multi_index]) + materials[materialNumber].materialColor[1] * targetLayer[j.multi_index]
					tupleResultR[j.multi_index] = 255 * (1.0 - targetLayer[j.multi_index]) + materials[materialNumber].materialColor[2] * targetLayer[j.multi_index]
				else:
					tupleResultB[j.multi_index] = 0
					tupleResultG[j.multi_index] = 0
					tupleResultR[j.multi_index] = 0
				j.iternext()				
			layersR.append(tupleResultR)
			layersG.append(tupleResultG)
			layersB.append(tupleResultB)
				
		print "i got here"
		self.volumeR=numpy.array(layersR) # create the 3d volume
		self.volumeG=numpy.array(layersG) 
		self.volumeB=numpy.array(layersB)

		volumeGeneral.append(self.volumeR)
		volumeGeneral.append(self.volumeG)
		volumeGeneral.append(self.volumeB)
		
		return volumeGeneral
	