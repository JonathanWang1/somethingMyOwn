#!/usr/bin/env python
#-*- coding: UTF-8 -*-

""" This program loads a model with PyASSIMP, and display it.

It make a large use of shaders to illustrate a 'modern' OpenGL pipeline.

Based on:
 - pygame + mouselook code from http://3dengine.org/Spectator_%28PyOpenGL%29
 - http://www.lighthouse3d.com/tutorials
 - http://www.songho.ca/opengl/gl_transform.html
 - http://code.activestate.com/recipes/325391/
 - ASSIMP's C++ SimpleOpenGL viewer

Authors: Séverin Lemaignan, 2012-2013
"""
import sys

import logging
from gi.overrides.Gdk import Color
from IN import INTMAX_C
from sys import maxint
logger = logging.getLogger("pyassimp")
gllogger = logging.getLogger("OpenGL")
gllogger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

import OpenGL
OpenGL.ERROR_CHECKING=False
OpenGL.ERROR_LOGGING = False
#OpenGL.ERROR_ON_COPY = True
#OpenGL.FULL_LOGGING = True
from OpenGL.GL import *
from OpenGL.error import GLError
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
from OpenGL.GL import shaders

import pygame

import math, random
import numpy
from numpy import linalg, dtype

import pyassimp
from pyassimp.postprocess import *
from pyassimp.helper import *
import mestTest
import ray_tri
#from mathutils import geometry

class DefaultCamera:
    def __init__(self, w, h, fov):
        self.clipplanenear = 1.0
        self.clipplanefar = 100000.0
        self.aspect = w/h
        self.horizontalfov = fov * math.pi/180 #should be delved into later
        self.transformation = [[ 0.68, -0.32, 0.65, 7.48],
                               [ 0.73,  0.31, -0.61, -6.51],
                               [-0.01,  0.89,  0.44,  5.34],
                               [ 0.,    0.,    0.,    1.  ]]
        #self.transformation = [[ 1., 1., 0., 0.],
        #                       [ 0., 1., 0., 0.],
        #                       [ 0., 0., 1., 0.],
        #                       [ 0., 0., 0., 1.  ]]
        self.lookat = [0.0,0.0,-1.0]

    def __str__(self):
        return "Default camera"

class PyAssimp3DViewer:

    def __init__(self, model, index, w=1024, h=768, fov=75):
        
        self.width = w
        self.height = h
        self.fov = fov
        self.base_name = "Material " + str(index) 
        
        self.triRay = ray_tri.TriRayIntersect()
        self.position = [0,0,0]# take the record of last mouse click position

        pygame.init()
        pygame.display.set_caption(self.base_name)
        pygame.display.set_mode((w,h), pygame.OPENGL | pygame.DOUBLEBUF)

        self.prepare_shaders()

        self.cameras = [DefaultCamera(float(w),float(h),float(fov))]
        self.current_cam_index = 0

        self.load_model(model)

        # for FPS computation
        self.frames = 0
        self.last_fps_time = glutGet(GLUT_ELAPSED_TIME)


        self.cycle_cameras()
    def quit_viewer(self):
        pygame.display.quit()
        pygame.quit()

    def prepare_shaders(self):

        phong_weightCalc = """
        float phong_weightCalc(
            in vec3 light_pos, // light position
            in vec3 frag_normal // geometry normal
        ) {
            // returns vec2( ambientMult, diffuseMult )
            float n_dot_pos = max( 0.0, dot(
                frag_normal, light_pos
            ));
            return n_dot_pos;
        }
        """

        vertex = shaders.compileShader("""
            attribute vec3 Vertex_position;
            attribute vec3 Vertex_normal;
            varying vec4 baseColor;
            void main() {
                gl_Position = gl_ModelViewProjectionMatrix * vec4( Vertex_position,1.0);
                baseColor = vec4(Vertex_normal,1.0);
            }""",GL_VERTEX_SHADER)

        fragment = shaders.compileShader("""
        varying vec4 baseColor;
        void main() {
            gl_FragColor = baseColor;
        }
        """, GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vertex,fragment)
        self.set_shader_accessors( (
        ), (
            'Vertex_position','Vertex_normal',
        ), self.shader)

    def set_shader_accessors(self, uniforms, attributes, shader):
        # add accessors to the shaders uniforms and attributes
        for uniform in uniforms:
            location = glGetUniformLocation( shader,  uniform )
            if location in (None,-1):
                logger.warning('No uniform: %s'%( uniform ))
            setattr( shader, uniform, location )

        for attribute in attributes:
            location = glGetAttribLocation( shader, attribute )
            if location in (None,-1):
                logger.warning('No attribute: %s'%( attribute ))
            setattr( shader, attribute, location )


    def prepare_gl_buffers(self, mesh):

        mesh.gl = {}

        # Fill the buffer for vertex and normals positions
        v = numpy.array(mesh.vertices, 'f')
        c = numpy.array(mesh.color, 'f')
        
        """
        #right now we conment this out, later I think we will use normal later
        n = numpy.array(mesh.normals, 'f')
        """
        mesh.gl["vbo"] = vbo.VBO(numpy.hstack((v,c)))
        
        #mesh.gl["vbo"] = vbo.VBO(v)

        # Fill the buffer for vertex positions
        mesh.gl["faces"] = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 
                    mesh.faces,
                    GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0)

    
    def load_model(self, path, postprocess = aiProcessPreset_TargetRealtime_MaxQuality):
        logger.info("Loading model:" + path + "...")

        if postprocess:
            self.scene = pyassimp.load(path, postprocess)
        else:
            self.scene = pyassimp.load(path)
        logger.info("Done.")

        scene = self.scene
        #log some statistics
        logger.info("  meshes: %d" % len(scene.meshes))
        logger.info("  total faces: %d" % sum([len(mesh.faces) for mesh in scene.meshes]))
        logger.info("  materials: %d" % len(scene.materials))
        self.bb_min, self.bb_max = get_bounding_box(self.scene)
        logger.info("  bounding box:" + str(self.bb_min) + " - " + str(self.bb_max))

        self.scene_center = [(a + b) / 2. for a, b in zip(self.bb_min, self.bb_max)]
        
        for index, mesh in enumerate(scene.meshes):
            """convert the vertice and face in the original mesh, and also give a color in there"""
            self.c = mestTest.Convert(mesh, path)
            self.c.convert()
            modifyVertices, modifyTri, color, triangleSelected = self.c.surfaceDisplay(5,True)
            mesh.vertices = numpy.array(modifyVertices)
            mesh.color = numpy.array(color)
            mesh.faces = numpy.array(modifyTri, dtype = 'int32')
            self.prepare_gl_buffers(mesh)

        # Finally release the model
        pyassimp.release(scene)

        logger.info("Ready for 3D rendering!")

    def cycle_cameras(self):
        if not self.cameras:
            logger.info("No camera in the scene")
            return None
        self.current_cam_index = (self.current_cam_index + 1) % len(self.cameras)
        self.current_cam = self.cameras[self.current_cam_index]
        self.set_camera(self.current_cam)
        logger.info("Switched to camera <%s>" % self.current_cam)

    def set_camera_projection(self, camera = None):

        if not camera:
            camera = self.cameras[self.current_cam_index]

        znear = camera.clipplanenear
        zfar = camera.clipplanefar
        aspect = camera.aspect
        fov = camera.horizontalfov
        
        print znear, zfar, aspect, fov

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Compute gl frustrum
        tangent = math.tan(fov/2.)
        h = znear * tangent
        w = h * aspect

        # params: left, right, bottom, top, near, far
        glFrustum(-w, w, -h, h, znear, zfar)
        # equivalent to:
        #gluPerspective(fov * 180/math.pi, aspect, znear, zfar)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()


    def set_camera(self, camera):

        self.set_camera_projection(camera)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        cam = transform([0.0, 0.0, 0.0], camera.transformation)
        at = transform(camera.lookat, camera.transformation)
        gluLookAt(cam[0], cam[2], -cam[1],
                   at[0],  at[2],  -at[1],
                       0,      1,       0)

    def render(self, wireframe = False, twosided = False):

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)


        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)
        glDisable(GL_CULL_FACE) if twosided else glEnable(GL_CULL_FACE)

        shader = self.shader
        

        glUseProgram(shader)
        #glUniform4f( shader.Global_ambient, .4,.2,.2,.1 )
        #glUniform4f( shader.Light_ambient, .4,.4,.4, 1.0 )
        #glUniform4f( shader.Light_diffuse, 1,1,1,1 )
        #glUniform3f( shader.Light_location, 2,2,10 )

        self.recursive_render(self.scene.rootnode, shader)


        glUseProgram( 0 )

    def recursive_render(self, node, shader):
        """ Main recursive rendering method.
        """

        # save model matrix and apply node transformation
        glPushMatrix()
        m = node.transformation.transpose() # OpenGL row major
        glMultMatrixf(m)

        for mesh in node.meshes:

            stride = 24 # 6 * 4 bytes

            #diffuse = mesh.material.properties["diffuse"]
            #if len(diffuse) == 3: diffuse.append(1.0)
            #ambient = mesh.material.properties["ambient"]
            #if len(ambient) == 3: ambient.append(1.0)

            #glUniform4f( shader.Material_diffuse, *diffuse )
            #glUniform4f( shader.Material_ambient, *ambient )

            vbo = mesh.gl["vbo"]
            vbo.bind()

            glEnableVertexAttribArray( shader.Vertex_position )
            glEnableVertexAttribArray( shader.Vertex_normal )

            glVertexAttribPointer(
                shader.Vertex_position,
                3, GL_FLOAT,False, stride, vbo
            )

            glVertexAttribPointer(
                shader.Vertex_normal,
                3, GL_FLOAT,False, stride, vbo+12
            )

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
            glDrawElements(GL_TRIANGLES, len(mesh.faces) * 3, GL_UNSIGNED_INT, None)

            vbo.unbind()
            glDisableVertexAttribArray( shader.Vertex_position )

            glDisableVertexAttribArray( shader.Vertex_normal )


            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        for child in node.children:
            self.recursive_render(child, shader)

        glPopMatrix()


    def loop(self):

        pygame.display.flip()
        pygame.event.pump()
        self.keys = [k for k, pressed in enumerate(pygame.key.get_pressed()) if pressed]

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Compute FPS
        gl_time = glutGet(GLUT_ELAPSED_TIME)
        self.frames += 1
        if gl_time - self.last_fps_time >= 1000:
            current_fps = self.frames * 1000 / (gl_time - self.last_fps_time)
            pygame.display.set_caption(self.base_name + " - %.0f fps" % current_fps)
            self.frames = 0
            self.last_fps_time = gl_time


        return True

    def controls_3d(self,
                    mouse_button=1, \
                    up_key=pygame.K_UP, \
                    down_key=pygame.K_DOWN, \
                    left_key=pygame.K_LEFT, \
                    right_key=pygame.K_RIGHT):
        """ The actual camera setting cycle """
        mouse_dx,mouse_dy = pygame.mouse.get_rel()
        if pygame.mouse.get_pressed()[mouse_button]:
            look_speed = .2
            buffer = glGetDoublev(GL_MODELVIEW_MATRIX)
            c = (-1 * numpy.mat(buffer[:3,:3]) * \
                numpy.mat(buffer[3,:3]).T).reshape(3,1)
            # c is camera center in absolute coordinates, 
            # we need to move it back to (0,0,0) 
            # before rotating the camera
            glTranslate(c[0],c[1],c[2])
            m = buffer.flatten()
            glRotate(mouse_dx * look_speed, m[1],m[5],m[9])
            glRotate(mouse_dy * look_speed, m[0],m[4],m[8])
            
            # compensate roll
            glRotated(-math.atan2(-m[4],m[5]) * \
                57.295779513082320876798154814105 ,m[2],m[6],m[10])
            glTranslate(-c[0],-c[1],-c[2])
            
            #select a triangle!!!!
            pos = pygame.mouse.get_pos() 
            if pos != self.position:
                self.position = pos
                projectionCoord, glxPoint = self.getRay(pos)
                projectionCoord = projectionCoord.ravel().tolist()
                triSeletedList = []
                
                bufferViewMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
                viewMatrix = numpy.mat(bufferViewMatrix).T
                bufferProjectionMatrix = glGetDoublev(GL_PROJECTION_MATRIX)
                projectionMatrix = numpy.mat(bufferProjectionMatrix).T
                
                frontPoint = maxint
                selectedTri = None
                
                for triangle in self.c.TV:
                    vertices = []
                    for vertexId in triangle:
                        vertices.append(self.c.V[vertexId])
                    v0 = vertices[0].tolist()
                    v1 = vertices[1].tolist()
                    v2 = vertices[2].tolist()
                    if self.triRay.intersect(glxPoint, projectionCoord, v0, v1, v2):
                        averagePoint = []
                        averagePoint.append((v0[0] + v1[0] + v2[0]) / 3.0)
                        averagePoint.append((v0[1] + v1[1] + v2[1]) / 3.0)
                        averagePoint.append((v0[2] + v1[2] + v2[2]) / 3.0)
                        averagePoint.append(1.0)
                        averagePoint = numpy.mat(averagePoint).T
                        viewPoint = projectionMatrix * viewMatrix * averagePoint
                        viewPoint = numpy.array(viewPoint)
                        print viewPoint[2]
                        if viewPoint[2] < frontPoint:
                            frontPoint = viewPoint[2]
                            selectedTri = triangle
                            
                    if selectedTri != None:
                        selectedId = self.c.TV.index(selectedTri)
                        scene = self.scene
                        for index, mesh in enumerate(scene.meshes):
                            modifyVertices, modifyTri, color, triangleSelected = self.c.surfaceDisplay(selectedId,False)
                            mesh.vertices = numpy.array(modifyVertices)
                            mesh.color = numpy.array(color)
                            mesh.faces = numpy.array(modifyTri, dtype = 'int32')
                            self.triangleSelected = triangleSelected
                            self.prepare_gl_buffers(mesh)
        
        # move forward-back or right-left
        if up_key in self.keys:
            fwd = .1
        elif down_key in self.keys:
            fwd = -.1
        else:
            fwd = 0

        if left_key in self.keys:
            strafe = .1
        elif right_key in self.keys:
            strafe = -.1
        else:
            strafe = 0

        if abs(fwd) or abs(strafe):
            m = glGetDoublev(GL_MODELVIEW_MATRIX).flatten()
            glTranslate(fwd*m[2],fwd*m[6],fwd*m[10])
            glTranslate(strafe*m[0],strafe*m[4],strafe*m[8])
    def getRay(self, position):
        #get normalized device coord
        x = 2.0 * position[0] / self.width - 1.0
        y = 0.0 - (2.0 * position[1] / self.height - 1.0)
        originX = position[0]
        originY = self.height - position[1]
        print x, y
        
        clipcoord = [x, y, -1.0, 1.0]
        clipcoord = numpy.array(clipcoord).reshape(4,1)
        clipcoord = numpy.mat(clipcoord[:4])
        #print clipcoord
        
        bufferViewMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        viewMatrix = numpy.mat(bufferViewMatrix).T
        #print viewMatrix
        bufferProjectionMatrix = glGetDoublev(GL_PROJECTION_MATRIX)
        projectionMatrix = numpy.mat(bufferProjectionMatrix).T
        #print projectionMatrix
        
        viewCoord = numpy.linalg.inv(projectionMatrix) * clipcoord
        #print viewCoord
        viewX = numpy.squeeze(numpy.asarray(viewCoord[0][0]))
        viewY = numpy.squeeze(numpy.asarray(viewCoord[1][0]))
        viewNewCoord = numpy.array([viewX, viewY, -1.0, 0.0]).reshape(4,1)
        #print viewNewCoord
        viewNewCoord = numpy.mat(viewNewCoord[:4])
        projectionCoord = numpy.linalg.inv(viewMatrix) * viewNewCoord
        
        projectionCoord = projectionCoord[:3]
        projectionCoord = projectionCoord / numpy.linalg.norm(projectionCoord)
        print projectionCoord
        
        viewPort = glGetIntegerv(GL_VIEWPORT)
        
        #z1 = glReadPixels(originX, int(originY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        #z = z1[0]
        #z2 = glReadPixels(originX, int(originY), 0, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        
        glx1, gly1, glz1 = gluUnProject(originX, originY, 0,   model=bufferViewMatrix,
                                proj=bufferProjectionMatrix,
                                view=viewPort)
        
        #glx2, gly2, glz2 = gluUnProject(originX, originY, z2,   model=bufferViewMatrix,
        #                        proj=bufferProjectionMatrix,
        #                        view=viewPort)
        glxPoint = [glx1, gly1, glz1] 
        
        return projectionCoord, glxPoint 

if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print("Usage: " + __file__ + " <model>")
        sys.exit(2)

    app = PyAssimp3DViewer(model = sys.argv[1], w = 1024, h = 768, fov = 90.0)

    while app.loop():
        app.render()
        app.controls_3d(0)
        if pygame.K_f in app.keys: pygame.display.toggle_fullscreen()
        if pygame.K_TAB in app.keys: app.cycle_cameras()
        if pygame.K_ESCAPE in app.keys:
            break
