import pyassimp 
import sys
import numpy
import multiprocessing
import cPickle as pickle
import gzip
import itertools
from Queue import Queue
from sets import Set
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

###### Helper functions #####

class Convert():
    def __init__(self, mesh, name):
        #self.initUI()
        #self.V =  vertice.tolist()
        #self.TV = triangle.tolist()
        self.fname = name
        self.mesh = mesh
    
    def makeHash(self, p):
        '''casts the input to a numpy array and returns a string hash representing the object'''
        n=numpy.array([p[0],p[1],p[2]])
        return n.tostring(),n

    ###### Conversion Algorithm ######
    def convert(self):
        try:
            """
            safeThreads=int(multiprocessing.cpu_count()-2)
           
            print "...building vertex hash list"
            pool=multiprocessing.Pool(processes=safeThreads)
            hashes=pool.map(self.makeHash,self.obj.meshes[0].vertices)
            pool.terminate()
            """
            
            hashes = []
            for vertex in self.mesh.vertices:
                hashes.append(self.makeHash(vertex)) 
            print "\thashes calculated: "+repr(len(hashes))
            #print type(hashes);
            #for i in hashes:
            #    print i;
            Ktot=[t[0] for t in hashes] # all keys, return the first item in the list!
            #print type(Ktot)
            print "...finding unique vertices"
            a=dict(hashes) # collapse the hash list into a dictionary to ensure uniqueness
            self.V=a.values() # list of unique vertices
            print "\tunique vertices: "+repr(len(self.V))
            K=a.keys() # list of unique keys
            
            print "...determining point indices"
            Kidx=[K.index(key) for key in Ktot] # point indices
            
            for i in Kidx:
                print i
                
            print "...creating triangle vertex pointers"
            self.TV=[list(i) for i in list(numpy.array(Kidx).reshape(len(Kidx)/3,3))] # triangle vertex indices
            print "\tTotal triangles: "+repr(len(self.TV))
            
            fname=self.fname[:-3]+"mesh"
            print type(self.V)
            print type(self.TV)
            print "...saving mesh data to: "+fname
            #savedata=(V,TV,L,TL,LT)
            savedata=(self.V,self.TV)
            f=gzip.open(fname,"wb")
            pickle.dump(savedata,f)
            f.close()
            
            #pyassimp.release(self.obj) # release the pyassimp object to prevent memory leaks
            return True
        except:
            return False
    
        
    def findAroundTri(self, triangleId):
        triangleAround = []
        for i in self.TV:
            if Set(i).intersection(self.TV[triangleId]):
                targetId = self.TV.index(i)
                if targetId != triangleId:
                    triangleAround.append(targetId)
        return triangleAround
                        
    def calculateNormal(self, vertex1, vertex2, vertex3):
        line1 = vertex3 - vertex1
        line2 = vertex3 - vertex2
        normal = numpy.cross(line1, line2)
        normlised = normal / numpy.linalg.norm(normal)
        return normlised
    
    def findTriangleVertex(self, triangleId):
        vertex = []
        for i in self.TV[triangleId]:
            vertex.append(self.V[i])
        return vertex
    def whetherInSameFace(self, triangleId1, triangleId2):
        vertex1 = self.findTriangleVertex(triangleId1)
        vertex2 = self.findTriangleVertex(triangleId2)
        normal1 = self.calculateNormal(vertex1[0], vertex1[1], vertex1[2])
        normal2 = self.calculateNormal(vertex2[0], vertex2[1], vertex2[2])
        dotProduct = normal1[0] * normal2[0] + normal1[1] * normal2[1] + normal1[2] * normal2[2]
        if abs(dotProduct) > 0.8:
            return True
        else:
            return False
    
    def findMatchTriangle(self, triangleId): 
        triangleFlag = []
        for i in range(0, len(self.TV)):
            triangleFlag.append("notSearched") 
        
        triInFace = []        
        searchingQueue = Queue()
        searchingQueue.put(triangleId)
        triangleFlag[triangleId] = "inPlane"
        
        while not(searchingQueue.empty()):
            targetId = searchingQueue.get()
            triInFace.append(targetId)
            triangleAround = self.findAroundTri(targetId)
            for j in triangleAround:
                if triangleFlag[j] == "notSearched":
                    if self.whetherInSameFace(targetId, j):
                        searchingQueue.put(j)
                        triangleFlag[j] = "inPlane"
                    else:
                        triangleFlag[j] = "notInPlane"
        return triInFace
    
    
    
    def surfaceDisplay(self, trianleId, oringal = False):
        result = self.findMatchTriangle(trianleId)
        self.color = numpy.zeros(numpy.array(self.V).shape, dtype='f')
        triangleSelected = []
        
        if not oringal:
            for triangle in self.TV:
                if self.TV.index(triangle) in result:
                    triangleSelected.append(triangle)
                    for vertex in triangle:
                        self.color[vertex] = numpy.array([1, 0, 0])
                else:
                    for vertex in triangle: 
                        if numpy.array_equal(self.color[vertex], [1,0,0]):   
                            continue
                        else:
                            self.color[vertex] = numpy.array([0, 1, 0])
        else:
            for triangle in self.TV:
                for vertex in triangle: 
                    self.color[vertex] = numpy.array([0, 1, 0])
                    
        return self.V, self.TV, self.color, triangleSelected 
            
if __name__ == "__main__":
    c = Convert("HalfDonut.stl")
    c.convert()
    #result = c.findMatchTriangle(3)
    #print result
    
    
    pygame.init()
    
    display = (800,600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

    gluPerspective(90, (display[0]/display[1]), 0.1, 50.0)

    glTranslatef(0.0,0.0,-2)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        glRotatef(1, 3, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        c.surfaceDisplay(5)
        pygame.display.flip()
        pygame.time.wait(5)
    
    