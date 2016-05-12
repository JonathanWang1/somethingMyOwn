'''
Created on Feb 5, 2016

@author: root
'''
import numpy

class TriRayIntersect:
    def __init__(self):
        pass
    
    def vectorSubtract(self, b,c):
        a = []
        a.append(b[0] - c[0])
        a.append(b[1] - c[1])
        a.append(b[2] - c[2])
        return a

    def intersect(self, p,d,v0,v1,v2):
        e1 = self.vectorSubtract(v1, v0)
        e2 = self.vectorSubtract(v2, v0)
    
        h = numpy.cross(d, e2)
        a = numpy.inner(e1, h)
    
        if a > -0.00001 and a < 0.00001:
            return False
    
        f = 1.0 / a
        s = self.vectorSubtract(p,v0)
        u = f * numpy.inner(s,h)
    
        if u < 0.0 or u > 1.0:
            return False
    
        q = numpy.cross(s, e1)
        v = f * numpy.inner(d, q)
    
        if v < 0.0 or u + v > 1.0:
            return False
    
        t = f * numpy.inner(e2, q)
    
        if t > 0.00001:
            return True
        else:
            return False
        
if __name__ == '__main__':
    vec1 = [1,-1,0]
    vec2 = [-1,-1,0]
    vec3 = [0,1,0]
    point = [0,0,-1]
    direction = [0,0,11]
    ray = TriRayIntersect()
    print ray.intersect(point,direction,vec1,vec2,vec3)
