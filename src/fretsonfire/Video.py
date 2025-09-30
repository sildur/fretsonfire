#####################################################################
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

import pygame
from OpenGL.GL import glEnable
from OpenGL.GL.ARB.multisample import GL_MULTISAMPLE_ARB
import Log

class Video:
  def __init__(self, caption = "Game"):
    self.screen     = None
    self.caption    = caption
    self.fullscreen = False
    self.flags      = pygame.OPENGL | pygame.DOUBLEBUF
    self._baseFlags = pygame.OPENGL | pygame.DOUBLEBUF
    self._multisamples = 0
    self._displayInitialized = False

  def _ensureDisplayInitialized(self):
    if not self._displayInitialized or not pygame.display.get_init():
      pygame.display.init()
      self._displayInitialized = True

  def _configureGlAttributes(self, multisamples):
    pygame.display.gl_set_attribute(pygame.GL_RED_SIZE,   8)
    pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE, 8)
    pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE,  8)
    pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

    if multisamples:
      pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
      pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, multisamples)
    else:
      pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
      pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)

  def setMode(self, resolution, fullscreen = False, flags = pygame.OPENGL | pygame.DOUBLEBUF,
              multisamples = 0):
    requestedFullscreen = fullscreen or bool(flags & pygame.FULLSCREEN)
    baseFlags = flags & ~pygame.FULLSCREEN
    if requestedFullscreen:
      flags = baseFlags | pygame.FULLSCREEN
    else:
      flags = baseFlags

    self._ensureDisplayInitialized()

    self._baseFlags = baseFlags
    self.flags      = flags
    self.fullscreen = requestedFullscreen

    try:
      self._configureGlAttributes(multisamples)
      self.screen = pygame.display.set_mode(resolution, flags)
    except Exception as e:
      Log.error(str(e))
      if multisamples:
        Log.warn("Video setup failed. Trying without antialiasing.")
        self._configureGlAttributes(0)
        multisamples = 0
        self.screen = pygame.display.set_mode(resolution, flags)
      else:
        Log.error("Video setup failed. Make sure your graphics card supports 32 bit display modes.")
        raise

    pygame.display.set_caption(self.caption)
    pygame.mouse.set_visible(False)

    self._multisamples = multisamples

    if multisamples:
      try:
        glEnable(GL_MULTISAMPLE_ARB)
      except:
        pass

    return bool(self.screen)
    
  def toggleFullscreen(self):
    assert self.screen

    resolution = self.screen.get_size()
    return self.setMode(resolution, not self.fullscreen, self._baseFlags, self._multisamples)

  def flip(self):
    pygame.display.flip()

  def getVideoModes(self):
    return pygame.display.list_modes()
