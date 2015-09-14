import pyassimp 
import sys
import numpy
import multiprocessing
import cPickle as pickle
import gzip
import itertools

###### Helper functions #####
def makeHash(p):
	'''casts the input to a numpy array and returns a string hash representing the object'''
	n=numpy.array([p[0],p[1],p[2]])
	return n.tostring(),n

def topoTable(i):
	return list(numpy.nonzero(numpy.array(TL)==i)[0])
	
def linePairs(T):
	return [(min(i),max(i)) for i in itertools.combinations(T,2)]

def linePointers(T):
	return [LineStr.index(repr(i)) for i in T]

###### Conversion Algorithm ######
def convert(fname):
	try:
		safeThreads=int(multiprocessing.cpu_count()-2)
		print "Beginning mesh conversion of "+ fname
		obj=pyassimp.load(fname)
		
		print "...building vertex hash list"
		pool=multiprocessing.Pool(processes=safeThreads)
		hashes=pool.map(makeHash,obj.meshes[0].vertices)
		pool.terminate()
		#hashes = makeHash(obj.meshes[0].vertices)
		print "\thashes calculated: "+repr(len(hashes))
		#print type(hashes);
		#for i in hashes:
		#	print i;
		Ktot=[t[0] for t in hashes] # all keys, return the first item in the list!
		#print type(Ktot)
		print "...finding unique vertices"
		a=dict(hashes) # collapse the hash list into a dictionary to ensure uniqueness
		V=a.values() # list of unique vertices
		print "\tunique vertices: "+repr(len(V))
		K=a.keys() # list of unique keys
		
		print "...determining point indices"
		Kidx=[K.index(key) for key in Ktot] # point indices
		
		for i in Kidx:
			print i
			
		print "...creating triangle vertex pointers"
		TV=[list(i) for i in list(numpy.array(Kidx).reshape(len(Kidx)/3,3))] # triangle vertex indices
		print "\tTotal triangles: "+repr(len(TV))
		
		fname=fname[:-3]+"mesh"
		print "...saving mesh data to: "+fname
		#savedata=(V,TV,L,TL,LT)
		savedata=(V,TV)
		f=gzip.open(fname,"wb")
		pickle.dump(savedata,f)
		f.close()
		
		pyassimp.release(obj) # release the pyassimp object to prevent memory leaks
		return True
	except:
		return False
	
	
if __name__ == "__main__":
	convert("../sphere.stl")
