#!/usr/bin/env python

# Author: Shao Zhang, Phil Saltzman, and Greg Lindley
# Last Updated: 2015-03-13
#
# This tutorial demonstrates the use of tasks. A task is a function that
# gets called once every frame. They are good for things that need to be
# updated very often. In the case of asteroids, we use tasks to update
# the positions of all the objects, and to check if the bullets or the
# ship have hit the asteroids.
#
# Note: This definitely a complicated example. Tasks are the cores of
# most games so it seemed appropriate to show what a full game in Panda
# could look like.

from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, TransparencyAttrib
from panda3d.core import LPoint3, LVector3, BitMask32
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
from math import sin, cos, pi
from random import randint, choice, random, randrange
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
from datetime import datetime
import sys
import time
from panda3d.core import WindowProperties


# Constants that will control the behavior of the game. It is good to
# group constants like this so that they can be changed once without
# having to find everywhere they are used in code
SPRITE_POS = 55     # At default field of view and a depth of 55, the screen
# dimensions is 40x30 units
SCREEN_X = 20       # Screen goes from -20 to 20 on X
SCREEN_Y = 15       # Screen goes from -15 to 15 on Y
TURN_RATE = 360     # Degrees ship can turn in 1 second
ACCELERATION = 10   # Ship acceleration in units/sec/sec
MAX_VEL = 6         # Maximum ship velocity in units/sec
MAX_VEL_SQ = MAX_VEL ** 2  # Square of the ship velocity
DEG_TO_RAD = pi / 180  # translates degrees to radians for sin and cos
BULLET_LIFE = 2     # How long bullets stay on screen before removed
BULLET_REPEAT = .2  # How often bullets can be fired
BULLET_SPEED = 10   # Speed bullets move
AST_INIT_VEL = 1    # Velocity of the largest asteroids
AST_INIT_SCALE = 1  # Initial asteroid scale
AST_VEL_SCALE = 2.2  # How much asteroid speed multiplies when broken up
AST_SIZE_SCALE = .6  # How much asteroid scale changes when broken up
AST_MIN_SCALE = 1.1  # If and asteroid is smaller than this and is hit,
# it disapears instead of splitting up

asteroids = []
global chosenNum
global localNum2
global mouseOver
mouseOver = False
global outputDataContents
outputDataContents = "timeStamp,event,timeSinceLastClick,timeSinceLastRedClick\n"
global timerOverall
global timerRed
global timerOverallNew
timerOverallNew = 99999
global timerRedNew
timerRedNew = 99999

# This helps reduce the amount of code used by loading objects, since all of
# the objects are pretty much the same.
def loadObject(tex=None, pos=LPoint3(0, 0), depth=SPRITE_POS, scale=1,
               transparency=True):
    # Every object uses the plane model and is parented to the camera
    # so that it faces the screen.
    obj = loader.loadModel("models/plane")
    obj.reparentTo(camera)

    # Set the initial position and scale.
    obj.setPos(pos.getX(), depth, pos.getY())
    obj.setScale(scale)

    # This tells Panda not to worry about the order that things are drawn in
    # (ie. disable Z-testing).  This prevents an effect known as Z-fighting.
    obj.setBin("unsorted", 0)
    obj.setDepthTest(False)

    if transparency:
        # Enable transparency blending.
        obj.setTransparency(TransparencyAttrib.MAlpha)

    if tex:
        # Load and set the requested texture.
        tex = loader.loadTexture("textures/" + tex)
        obj.setTexture(tex, 1)

    return obj


# Macro-like function used to reduce the amount to code needed to create the
# on screen instructions
def genLabelText(text, i):
    return OnscreenText(text=text, parent=base.a2dTopLeft, pos=(0.07, -.09 * i - 0.1),
                        fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.09)


class AsteroidsDemo(ShowBase):

    def __init__(self):
        # Initialize the ShowBase class from which we inherit, which will
        # create a window and set up everything we need for rendering into it.
        ShowBase.__init__(self)

        wp = WindowProperties()
        wp.setSize(360, 720)
        base.win.requestProperties(wp)

        # This code puts the standard title and instruction text on screen
        self.title = OnscreenText(text="Panda3D: Game",
                                  parent=base.a2dBottomRight, scale=.09,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        self.escapeText = genLabelText("ESC: Quit", 0)
        self.leftClickText = genLabelText("[Left Click]: On Red Dot", 1)

        # Disable default mouse-based camera control.  This is a method on the
        # ShowBase class from which we inherit.
        
        self.disableMouse()

        self.picker = CollisionTraverser()  # Make a traverser
        self.pq = CollisionHandlerQueue()  # Make a handler
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()  # Make our ray
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        #self.picker.showCollisions(render)

        # Load the background starfield.
        self.setBackgroundColor((0, 0, 0, 1))

        posXs = [5, -6, 7, -2, 3, -4, 1, 0, -2, -4, 7, -3, 10, -4, 11, 6, 3]
        posZs = [-11, 12, -2, 12, -13, 14, -11, 10, -12, -2, 2, -1, 0, -4, -5, 6, 13]

        for i in range(17):
            asteroid1 = loadObject(tex="asteroid1.png", scale=AST_INIT_SCALE)
            
            #asteroid1.setX(choice(tuple(range(-SCREEN_X+5, 0)) + tuple(range(0, SCREEN_X-5))))
            #asteroid1.setZ(choice(tuple(range(-SCREEN_Y+5, 0)) + tuple(range(0, SCREEN_Y-5))))
            
            asteroid1.setX(posXs[i])
            asteroid1.setZ(posZs[i])
            
            asteroid1.setColor(0.0, 0.0, 1.0, 1.0)
            asteroids.append(asteroid1)

            asteroids[i].find("**/pPlane1").node().setIntoCollideMask(BitMask32.bit(1))
            asteroids[i].find("**/pPlane1").node().setTag('asteroid', str(i))
        
        global chosenNum
        chosenNum = randrange(17)

        global localNum2
        localNum2 = randrange(17)
        while (chosenNum == localNum2):
            localNum2 = randrange(17)

        asteroids[chosenNum].setColor(1.0, 0.0, 0.0, 1.0)
        global outputDataContents
        outputDataContents = outputDataContents + datetime.now().strftime("%H:%M:%S") + ",firstRedAppears,,\n"

        self.mouseTask = taskMgr.add(self.mouseTask, 'mouseTask')

        self.accept("mouse1", self.changeColor) 

        self.gameTask = taskMgr.doMethodLater(2, self.everySecond, 'everySecond')
        self.gameTask2 = taskMgr.doMethodLater(2, self.everySecondRed, 'everySecondRed')

        self.accept("escape", self.saveDataExit)  # Escape quits


    def makeid(self, length):
        result = ""
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        charactersLength = len(characters)
        for i in range(length):
            result = result + characters[randrange(charactersLength)]
        return result

    def mouseTask(self, task):
        # This task deals with the highlighting and dragging based on the mouse
        # Check to see if we can access the mouse. We need it to do anything
        # else
        global mouseOver
        if self.mouseWatcherNode.hasMouse():
            # get the mouse position
            mpos = self.mouseWatcherNode.getMouse()

            # Set the position of the ray based on the mouse position
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())

            # Do the actual collision pass (Do it only on the squares for
            # efficiency purposes)
            global chosenNum
            self.picker.traverse(asteroids[chosenNum])
            if self.pq.getNumEntries() > 0:
                # if we have hit something, sort the hits so that the closest
                # is first, and highlight that node
                self.pq.sortEntries()
                i = int(self.pq.getEntry(0).getIntoNode().getTag('asteroid'))
                # Set the highlight on the picked square
                if (chosenNum == i):
                    mouseOver = True
        return Task.cont

    def everySecond(self, task):
        global localNum2
        global chosenNum
        asteroids[localNum2].setColor(0.0, 0.0, 1.0, 1.0)
        localNum2 = randrange(17)
        while (chosenNum == localNum2):
            localNum2 = randrange(17)
        asteroids[localNum2].setColor(1.0, 1.0, 0.0, 1.0)
        return task.again

    def everySecondRed(self, task):
        global chosenNum
        global localNum2
        asteroids[chosenNum].setColor(0.0, 0.0, 1.0, 1.0)
        localNum = randrange(17)
        while (chosenNum == localNum or localNum2 == localNum):
            localNum = randrange(17)
        chosenNum = localNum
        asteroids[chosenNum].setColor(1.0, 0.0, 0.0, 1.0)
        return task.again

    def changeColor(self):
        global mouseOver
        global outputDataContents
        global timerOverall
        global timerRed
        global timerOverallNew
        global timerRedNew
        if (mouseOver == True):
            timerOverall = time.perf_counter() - timerOverallNew
            if timerOverall < 0:
                timerOverall = 0
            timerOverallNew = time.perf_counter()
            timerRed = time.perf_counter() - timerRedNew
            if timerRed < 0:
                timerRed = 0
            timerRedNew = time.perf_counter()
            outputDataContents = outputDataContents + datetime.now().strftime("%H:%M:%S") + ",leftClkInsideRed,"+str(timerOverall)+","+str(timerRed)+"\n"
            #global chosenNum
            #global localNum2
            #asteroids[chosenNum].setColor(0.0, 0.0, 1.0, 1.0)
            #localNum = randrange(17)
            #while (chosenNum == localNum or localNum2 == localNum):
            #    localNum = randrange(17)
            #chosenNum = localNum
            #asteroids[chosenNum].setColor(1.0, 0.0, 0.0, 1.0)
            mouseOver = False
        else:
            timerOverall = time.perf_counter() - timerOverallNew
            if timerOverall < 0:
                timerOverall = 0
            timerOverallNew = time.perf_counter()
            outputDataContents = outputDataContents + datetime.now().strftime("%H:%M:%S") + ",leftClkOutsideRed,"+str(timerOverall)+",\n"

    def saveDataExit(self):
        fileNameSave = "dataFile_"+self.makeid(16)+".txt"
        f = open(fileNameSave, "w")
        f.write(outputDataContents)
        f.close()
        sys.exit()

# We now have everything we need. Make an instance of the class and start
# 3D rendering
demo = AsteroidsDemo()
demo.run()
