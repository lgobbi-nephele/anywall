import os
import sys
import ctypes
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import cv2

# Set the path to the directory containing freeglut.dll
freeglut_path = 'C:\\Users\\Utente\\Desktop\\Downloads\\freeglut-3.2.1\\freeglut-3.2.1\\build\\bin\\Debug'
os.environ['PATH'] = freeglut_path + os.pathsep + os.environ['PATH']

# Attempt to load the DLL to verify it’s on the PATH
try:
    dll = ctypes.CDLL("freeglut.dll")
    print("Loaded freeglut.dll successfully.")
except OSError:
    print("Failed to load freeglut.dll.")
    sys.exit(1)

# Load image and convert to OpenGL texture
texture_id = None

def load_texture():
    global texture_id
    frame = cv2.imread("C:\\Anywall\\resources\\placeholder.png", cv2.IMREAD_COLOR)
    if frame is None:
        print("Failed to load image.")
        sys.exit(1)
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, frame.shape[1], frame.shape[0], 0, GL_BGR, GL_UNSIGNED_BYTE, frame)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-1,  1, 0)
    glTexCoord2f(1, 0); glVertex3f(1,  1, 0)
    glTexCoord2f(1, 1); glVertex3f(1, -1, 0)
    glTexCoord2f(0, 1); glVertex3f(-1, -1, 0)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    glutSwapBuffers()

# Initialize GLUT and create a window
glutInit(sys.argv)
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_BORDERLESS | GLUT_CAPTIONLESS)
glutInitWindowSize(480, 270)  # Set desired window size
window_name = str(1).encode('utf-8')
glutCreateWindow(window_name)

# Position the window at the center of the screen
screen_width = glutGet(GLUT_SCREEN_WIDTH)
screen_height = glutGet(GLUT_SCREEN_HEIGHT)
glutPositionWindow((screen_width - 480) // 2, (screen_height - 270) // 2)

# OpenGL initialization
glClearColor(0.0, 0.0, 0.0, 1.0)

# Load the texture before starting the main loop
load_texture()

# Set the display callback
glutDisplayFunc(display)

# Enter the GLUT main loop
glutMainLoop()
