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

class Timer(object):
  def __init__(self, fps = 60, tickrate = 1.0):
    self.fps                   = fps
    self.timestep              = 1000.0 / fps
    self.tickrate              = tickrate
    self.ticks                 = self.getTime()
    self.frame                 = 0
    self.fpsEstimate           = 0
    self.fpsEstimateStartTick  = self.ticks
    self.fpsEstimateStartFrame = self.frame
    self.fpsEstimateElapsed    = 0.0
    self.highPriority          = False
    self.clock                 = pygame.time.Clock()

  def getTime(self):
    return int(pygame.time.get_ticks() * self.tickrate)

  time = property(getTime)

  def advanceFrame(self):
    if self.highPriority:
      elapsed = self.clock.tick_busy_loop(self.fps)
    else:
      elapsed = self.clock.tick(self.fps)

    diff = elapsed * self.tickrate
    self.ticks += diff
    self.frame += 1

    self.fpsEstimateElapsed += elapsed
    if self.fpsEstimateElapsed > 250:
      n = self.frame - self.fpsEstimateStartFrame
      if self.fpsEstimateElapsed:
        self.fpsEstimate = 1000.0 * n / self.fpsEstimateElapsed
      else:
        self.fpsEstimate = 0
      self.fpsEstimateStartTick = self.ticks
      self.fpsEstimateStartFrame = self.frame
      self.fpsEstimateElapsed = 0.0

    return [min(diff, self.timestep * 16)]
