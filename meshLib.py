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
		"""Find the contours of the part intersecting the plane defined by point and normal. -- find_intersection_contours(vertices,triangles,point,normal)"""
	
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
					foundOne=True
				elif numpy.linalg.norm(line[1]-contours[-1][-1])<tol: # line fits end backwards
					contours[-1].append(line[0])
					foundOne=True
				else:
					lines_left.append(line)
		
			lines_to_process=lines_left
			if not(foundOne):
				newContourNeeded=True
		return contours

	def prepare_voxel_slice(self,slices,llc,urc,direction):
		"""Builds a single layer container for the voxelizer routine. -- prepare_voxel_slice(size,res)"""
		size=urc-llc
		res = float(size[direction] / slices)
		dims=numpy.ceil(size/res)
		return numpy.zeros((dims[(direction+1) % 3],dims[(direction+2) % 3]),dtype='bool'), res

	def voxelize_single_contour(self, contour,res,llc,voxSlice,direction):
		"""Creates a single voxel slice from the provided contour. -- voxelize_single_contour(contour,res,llc,voxSlice)"""
		# prepare contour for the point check
		verts = [ (P[(direction+1) % 3],P[(direction+2) % 3]) for P in contour ]
		verts.append((contour[0][(direction+1) % 3],contour[0][(direction+2) % 3]))
		codes = [Path.MOVETO]
		[codes.append(Path.LINETO) for i in range(len(verts)-2)]
		codes.append(Path.CLOSEPOLY)
		path = Path(verts, codes)
	
		# prepare the list of points to check
		indices=numpy.transpose(numpy.array(numpy.nonzero(voxSlice==False)))
		positions=[(p[0],p[1]) for p in list(indices*res+numpy.array([llc[(direction+1)%3],llc[(direction+2)%3]]))]
	
		# do the check and reshape the result
		result=numpy.array(path.contains_points(positions),dtype='bool').reshape(voxSlice.shape)
	
		return result

	def voxelize_contours(self, contours,res,llc,voxSlice,direction):
		"""Creates a single voxel slice from the provided set of contours, finding . -- voxelize_contour(contours,res,llc,voxSlice)"""
		# generate each voxel slice
		vslices=[self.voxelize_single_contour(contour,res,llc,voxSlice,direction) for contour in contours]
		if len(vslices)>0:
			result=vslices.pop(0)
			for S in vslices:
				result=numpy.logical_xor(result,S)
			return result
		else:
			return voxSlice

	def voxel_slice(self,slicePoint,points,triangles,res,llc,sliceProto,direction):
		"""Creates contours at the given slicePoint, then converts the slice to a voxel slice. -- voxel_slice(points,triangles,slicePoint,res,llc,urc)"""
		if(direction == 0):
			contours=self.find_intersection_contours(points,triangles,slicePoint,numpy.array([1,0,0]))
			result=self.voxelize_contours(contours,res,llc,sliceProto,direction)
			return result	
	
		if(direction == 1):
			contours=self.find_intersection_contours(points,triangles,slicePoint,numpy.array([0,1,0]))
			result=self.voxelize_contours(contours,res,llc,sliceProto,direction)
			return result
	
		if(direction == 2):
			contours=self.find_intersection_contours(points,triangles,slicePoint,numpy.array([0,0,1]))
			result=self.voxelize_contours(contours,res,llc,sliceProto,direction)
			return result

	def point_list(self,res,llc,urc,direction):
		""" prepares a list of points for every XY plane slice, with a distance apart of res in the z direction, though the bound box defined by the corners llc and urc. --  point_list(res,llc,urc)"""
		if(direction == 0):
			Xdist=urc[0]-llc[0]
			numPoints=int(numpy.ceil(Xdist/res))
			deltaX=Xdist/numPoints
			points=[llc+numpy.array([deltaX*i,0,0]) for i in range(numPoints)]
			return points, points[0], points[-1]
	
		if(direction == 1):
			Ydist=urc[1]-llc[1]
			numPoints=int(numpy.ceil(Ydist/res))
			deltaY=Ydist/numPoints
			points=[llc+numpy.array([0,deltaY*i,0]) for i in range(numPoints)]
			return points, points[0], points[-1]

		if(direction == 2):
			Zdist=urc[2]-llc[2]
			numPoints=int(numpy.ceil(Zdist/res))
			deltaZ=Zdist/numPoints
			points=[llc+numpy.array([0,0,deltaZ*i]) for i in range(numPoints)]
			return points, points[0], points[-1]

	def voxelize1(self,points,triangles,slices, direction):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""
		
		self.dirction = direction
	
		llc,urc=self.find_boundbox(points) # find the lower left corner (llc) and upper right corner (urc) of the vertices
	
		sliceProto, res=self.prepare_voxel_slice(slices,llc,urc,direction) # create the prototype slice volume for the voxel slicing
	
		self.slicePoints, minPoints, maxPoints=self.point_list(res,llc,urc,direction) # prepare the list of points to slice at
	
	#partialVoxelSlicer=partial(voxel_slice,points=points,triangles=triangles,res=res,llc=llc,sliceProto=sliceProto) # prepare a single-input version of the voxel slicer for parallelization
	
	#pool=multiprocessing.Pool(processes=max(1,multiprocessing.cpu_count()-1)) 
	
	#layers=pool.map(partialVoxelSlicer,slicePoints) # perform the voxel conversion
	
	#volume=numpy.array(layers,dtype='bool') # create the 3d volume
	
	#return volume
		layers = list()
		self.boolLayers = list()
		#self.boolResult = list()
		#maxArray = numpy.amax(slicePoints, axis=0)
		#minArray = numpy.amin(slicePoints, axis=0)
		maxValue = maxPoints[direction]
		minValue = minPoints[direction]
		ratio = 255 / (maxValue - minValue)
		for i in self.slicePoints:
			boolResult = self.voxel_slice(i, points, triangles, res, llc, sliceProto, direction)
			print boolResult.shape
			tupleResult = numpy.zeros(boolResult.shape, dtype=int)
			tupleResult.astype(uint8)
			j = numpy.nditer(boolResult, flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
					tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio) + 1
					#tupleResult[j.multi_index] = 78
				else:
					tupleResult[j.multi_index] = 0
				j.iternext()
			self.boolLayers.append(boolResult)
			layers.append(tupleResult)
		print "i got here"
		volume=numpy.array(layers) # create the 3d volume
	
		return volume

	def voxelize2(self, points,triangles, planeOrigin, planeNormal):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""
		layers = list()
		m = 0
		for i in self.slicePoints:
			#print self.boolResult[m].shape
			tupleResult = numpy.zeros(self.boolLayers[m].shape, dtype=int)
			tupleResult.astype(uint8)
			j = numpy.nditer(self.boolLayers[m], flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
				#tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio)
				#tupleResult[j.multi_index] = 78
					print type(j.multi_index)
					print j.multi_index
					tupleResult[j.multi_index] = (j.multi_index[1] - planeOrigin[0]) * planeNormal[0] + (j.multi_index[0] - planeOrigin[1]) * planeNormal[1] + (i[2] - planeOrigin[2]) * planeNormal[2]
					if(tupleResult[j.multi_index] > 0):
						tupleResult[j.multi_index] = round(tupleResult[j.multi_index]) 
					if(tupleResult[j.multi_index] == 0):
						tupleResult[j.multi_index] = 1
					if(tupleResult[j.multi_index] < 0):
						tupleResult[j.multi_index] = round(0 - tupleResult[j.multi_index]) 
				else:
					tupleResult[j.multi_index] = 0
				j.iternext()
			layers.append(tupleResult)
			m = m + 1
		print "i got here"
		volume=numpy.array(layers) # create the 3d volume
	
		return volume
	
	def voxelize3(self, pointValue):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""
		layers = list()
		m = 0
		for i in self.slicePoints:
			#print self.boolResult[m].shape
			tupleResult = numpy.zeros(self.boolLayers[m].shape, dtype=int)
			tupleResult.astype(uint8)
			j = numpy.nditer(self.boolLayers[m], flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
				#tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio)
				#tupleResult[j.multi_index] = 78
					print type(j.multi_index)
					print j.multi_index
					tupleResult[j.multi_index] = math.sqrt(math.pow((j.multi_index[1]- pointValue[0]),2) + math.pow((j.multi_index[0] - pointValue[1]), 2)+math.pow((i[2] - pointValue[2]),2))
					if(tupleResult[j.multi_index] > 0):
						tupleResult[j.multi_index] = round(tupleResult[j.multi_index]) 
					if(tupleResult[j.multi_index] == 0):
						tupleResult[j.multi_index] = 1
					if(tupleResult[j.multi_index] < 0):
						tupleResult[j.multi_index] = round(0 - tupleResult[j.multi_index]) 
				else:
					tupleResult[j.multi_index] = 0
				j.iternext()
			layers.append(tupleResult)
			m = m + 1
		print "i got here"
		volume=numpy.array(layers) # create the 3d volume
	
		return volume

	def voxelize4(self, planeOrigin, planeNormal, pointValue, planeWeight, pointWeight):
		""" Voxelize the volume defined by the points and triangles pointer list with voxels of res side length. -- voxelize(points,triangles,res)"""
		layers = list()
		m = 0
		for i in self.slicePoints:
			#print self.boolResult[m].shape
			tupleResult = numpy.zeros(self.boolLayers[m].shape, dtype=int)
			tupleResult.astype(uint8)
			j = numpy.nditer(self.boolLayers[m], flags=['multi_index'], op_flags=['readwrite'])
			while not j.finished:
				if j[0] == True:
				#tupleResult[j.multi_index] = round((i[direction] - minValue) * ratio)
				#tupleResult[j.multi_index] = 78
					print type(j.multi_index)
					print j.multi_index
					tupleResult[j.multi_index] = planeWeight * math.fabs((j.multi_index[1] - planeOrigin[0]) * planeNormal[0] + (j.multi_index[0] - planeOrigin[1]) * planeNormal[1] + (i[2] - planeOrigin[2]) * planeNormal[2]) + pointWeight * math.sqrt(math.pow((j.multi_index[1]- pointValue[0]),2) + math.pow((j.multi_index[0] - pointValue[1]), 2)+math.pow((i[2] - pointValue[2]),2))
					if(tupleResult[j.multi_index] > 0):
						tupleResult[j.multi_index] = round(tupleResult[j.multi_index]) 
					if(tupleResult[j.multi_index] == 0):
						tupleResult[j.multi_index] = 1
					if(tupleResult[j.multi_index] < 0):
						tupleResult[j.multi_index] = round(0 - tupleResult[j.multi_index]) 
				else:
					tupleResult[j.multi_index] = 0
				j.iternext()
			layers.append(tupleResult)
			m = m + 1
		print "i got here"
		volume=numpy.array(layers) # create the 3d volume
	
		return volume
	
		
		