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

from __future__ import annotations

import math
import os
from io import BytesIO
from typing import Dict, Iterable, Optional, Tuple

import cairosvg
from OpenGL.GL import (
  GL_COLOR_BUFFER_BIT,
  GL_COLOR_MATERIAL,
  GL_CURRENT_BIT,
  GL_DEPTH_BUFFER_BIT,
  GL_ENABLE_BIT,
  GL_MODELVIEW,
  GL_POLYGON_BIT,
  GL_PROJECTION,
  GL_TEXTURE,
  GL_STENCIL_BUFFER_BIT,
  GL_TEXTURE_2D,
  GL_TEXTURE_BIT,
  GL_TRANSFORM_BIT,
  GL_TRIANGLE_STRIP,
  glBegin,
  glClear,
  glClearColor,
  glColor4f,
  glDisable,
  glEnable,
  glEnd,
  glLoadIdentity,
  glMatrixMode,
  glMultMatrixf,
  glOrtho,
  glPopAttrib,
  glPopMatrix,
  glPushAttrib,
  glPushMatrix,
  glScalef,
  glTexCoord2f,
  glTranslatef,
  glVertex2f,
  glDepthMask,
)
from PIL import Image
from numpy import dot, identity
from numpy import float32 as np_float32

from . import Config, Log
from .Texture import Texture

Config.define("opengl", "svgshaders", bool, False, text = "Use OpenGL SVG shaders", options = {False: "No", True: "Yes"})

LOW_QUALITY = 0
NORMAL_QUALITY = 1
HIGH_QUALITY = 2

_VectorSize = Tuple[int, int]


def _matrix_to_gl_array(matrix) -> Iterable[float]:
  """Convert a 3x3 transform matrix into a column-major 4x4 array."""
  return [
    matrix[0, 0], matrix[1, 0], 0.0, 0.0,
    matrix[0, 1], matrix[1, 1], 0.0, 0.0,
    0.0,          0.0,          1.0, 0.0,
    matrix[0, 2], matrix[1, 2], 0.0, 1.0,
  ]


class SvgTransform:
  def __init__(self, baseTransform: Optional["SvgTransform"] = None):
    self.matrix = identity(3, np_float32)
    if baseTransform:
      self.matrix = baseTransform.matrix.copy()

  def transform(self, other: "SvgTransform"):
    self.matrix = dot(self.matrix, other.matrix)

  def reset(self):
    self.matrix = identity(3, np_float32)

  def translate(self, dx: float, dy: float):
    self.matrix[0, 2] += dx
    self.matrix[1, 2] += dy

  def rotate(self, angle: float):
    s = math.sin(angle)
    c = math.cos(angle)
    rotation = identity(3, np_float32)
    rotation[0, 0] =  c
    rotation[0, 1] = -s
    rotation[1, 0] =  s
    rotation[1, 1] =  c
    self.matrix = dot(self.matrix, rotation)

  def scale(self, sx: float, sy: float):
    scaling = identity(3, np_float32)
    scaling[0, 0] = sx
    scaling[1, 1] = sy
    self.matrix = dot(self.matrix, scaling)

  def applyGL(self):
    glMultMatrixf(_matrix_to_gl_array(self.matrix))


class SvgContext:
  def __init__(self, geometry):
    self.geometry = geometry
    self.transform = SvgTransform()
    self._quality = NORMAL_QUALITY
    self.setGeometry(geometry)
    self.setProjection(geometry)

  def setGeometry(self, geometry = None):
    geometry = geometry or self.geometry
    self.geometry = geometry
    self.transform.reset()
    self.transform.scale(geometry[2] / 640.0, geometry[3] / 480.0)

  def setProjection(self, geometry = None):
    geometry = geometry or self.geometry
    self.geometry = geometry
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    left, top, width, height = geometry
    glOrtho(left, left + width, top + height, top, -100, 100)
    glMatrixMode(GL_MODELVIEW)

  def setRenderingQuality(self, quality):
    self._quality = quality

  def getRenderingQuality(self):
    return self._quality

  def clear(self, r = 0, g = 0, b = 0, a = 0):
    glDepthMask(1)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(r, g, b, a)
    glClear(GL_COLOR_BUFFER_BIT | GL_STENCIL_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


class SvgDrawing:
  def __init__(self, context, svgData):
    self.context = context
    self.transform = SvgTransform()
    self.texture: Optional[Texture] = None
    self._svg_path: Optional[str] = None
    self._svg_bytes: Optional[bytes] = None
    self._source_label: Optional[str] = None
    self._intrinsic_size: Optional[_VectorSize] = None
    self._vector_textures: Dict[_VectorSize, Texture] = {}

    if hasattr(svgData, "read"):
      data = svgData.read()
      if isinstance(data, str):
        data = data.encode(Config.encoding)
      self._svg_bytes = data
      self._source_label = getattr(svgData, "name", None)
      self._initialize_vector_renderer()
    elif isinstance(svgData, str):
      self._source_label = svgData
      base, ext = os.path.splitext(svgData)
      ext = ext.lower()
      if ext == ".png":
        self.texture = Texture(svgData)
        self._intrinsic_size = self.texture.pixelSize
      elif ext == ".svg":
        self._svg_path = svgData
        try:
          self._initialize_vector_renderer()
        except Exception as exc:
          Log.warn("Failed to initialize SVG renderer for '%s': %s" % (svgData, exc))
          bitmapFile = base + ".png"
          if os.path.exists(bitmapFile):
            Log.debug("Loading cached bitmap '%s' instead of '%s'." % (bitmapFile, svgData))
            self.texture = Texture(bitmapFile)
            self._intrinsic_size = self.texture.pixelSize
          else:
            raise
      else:
        self.texture = Texture(svgData)
        self._intrinsic_size = self.texture.pixelSize
    else:
      self.texture = Texture(svgData)
      self._intrinsic_size = self.texture.pixelSize

    if not self.texture and not self._intrinsic_size:
      raise RuntimeError("Unable to load SVG resource: %r" % (svgData,))

  def _initialize_vector_renderer(self):
    image = self._render_svg_image()
    self._intrinsic_size = image.size
    self._vector_textures[image.size] = self._image_to_texture(image)

  def _image_to_texture(self, image: Image.Image) -> Texture:
    texture = Texture()
    texture.loadImage(image)
    if self._svg_path:
      texture.name = self._svg_path
    elif self._source_label:
      texture.name = self._source_label
    return texture

  def _render_svg_image(self, output_size: Optional[_VectorSize] = None) -> Image.Image:
    kwargs = {}
    if output_size:
      width, height = output_size
      kwargs["output_width"] = max(1, int(width))
      kwargs["output_height"] = max(1, int(height))
    try:
      if self._svg_path:
        png_data = cairosvg.svg2png(url = self._svg_path, **kwargs)
      else:
        png_data = cairosvg.svg2png(bytestring = self._svg_bytes, **kwargs)
    except Exception as exc:
      label = self._svg_path or (self._source_label or "<memory>")
      raise RuntimeError("Failed to render SVG '%s' with CairoSVG: %s" % (label, exc)) from exc

    try:
      image = Image.open(BytesIO(png_data))
      return image.convert("RGBA")
    except Exception as exc:
      label = self._svg_path or (self._source_label or "<memory>")
      raise RuntimeError("Failed to decode rendered SVG '%s': %s" % (label, exc)) from exc

  def _render_svg_texture(self, output_size: Optional[_VectorSize] = None) -> Texture:
    image = self._render_svg_image(output_size = output_size)
    return self._image_to_texture(image)

  def _get_vector_texture(self, size: _VectorSize) -> Texture:
    key = (max(1, int(size[0])), max(1, int(size[1])))
    texture = self._vector_textures.get(key)
    if texture is None:
      texture = self._render_svg_texture(output_size = key)
      self._vector_textures[key] = texture
    return texture

  def _normalized_transform_and_size(self, transform: SvgTransform) -> Tuple[SvgTransform, _VectorSize]:
    if not self._intrinsic_size:
      raise RuntimeError("SVG drawing does not have intrinsic size information.")

    matrix = transform.matrix.copy()
    scale_x = math.hypot(matrix[0, 0], matrix[1, 0])
    scale_y = math.hypot(matrix[0, 1], matrix[1, 1])
    scale_x = max(scale_x, 1e-6)
    scale_y = max(scale_y, 1e-6)
    matrix[0, 0] /= scale_x
    matrix[1, 0] /= scale_x
    matrix[0, 1] /= scale_y
    matrix[1, 1] /= scale_y

    normalized = SvgTransform()
    normalized.matrix = matrix

    base_w, base_h = self._intrinsic_size
    target_size = (
      max(1, int(round(base_w * scale_x))),
      max(1, int(round(base_h * scale_y))),
    )
    return normalized, target_size

  def _getEffectiveTransform(self) -> SvgTransform:
    transform = SvgTransform(self.transform)
    transform.transform(self.context.transform)
    return transform

  def convertToTexture(self, width: int, height: int):
    if self.texture and self.texture.pixelSize == (width, height):
      return

    texture = self._render_svg_texture(output_size = (width, height))
    if texture:
      self.texture = texture
      return

    raise RuntimeError("Unable to convert SVG drawing to texture of size %sx%s." % (width, height))

  def draw(self, color = (1, 1, 1, 1)):
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    self.context.setProjection()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()

    transform = self._getEffectiveTransform()
    if self.texture:
      glLoadIdentity()
      transform.applyGL()
      glScalef(self.texture.pixelSize[0], self.texture.pixelSize[1], 1)
      glTranslatef(-.5, -.5, 0)
      glColor4f(*color)
      self.texture.bind()
      glEnable(GL_TEXTURE_2D)
      glBegin(GL_TRIANGLE_STRIP)
      glTexCoord2f(0.0, 1.0)
      glVertex2f(0.0, 1.0)
      glTexCoord2f(1.0, 1.0)
      glVertex2f(1.0, 1.0)
      glTexCoord2f(0.0, 0.0)
      glVertex2f(0.0, 0.0)
      glTexCoord2f(1.0, 0.0)
      glVertex2f(1.0, 0.0)
      glEnd()
      glDisable(GL_TEXTURE_2D)
    else:
      glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT | GL_STENCIL_BUFFER_BIT | GL_TRANSFORM_BIT | GL_COLOR_BUFFER_BIT | GL_POLYGON_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT)
      try:
        normalized, target_size = self._normalized_transform_and_size(transform)
        texture = self._get_vector_texture(target_size)
        glLoadIdentity()
        normalized.applyGL()
        glScalef(texture.pixelSize[0], texture.pixelSize[1], 1)
        glTranslatef(-.5, -.5, 0)
        glColor4f(*color)
        texture.bind()
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(0.0, 1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(0.0, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, 0.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)
      except Exception as exc:
        label = self._svg_path or (self._source_label or "<memory>")
        Log.error("Unable to render SVG '%s': %s" % (label, exc))
      finally:
        glPopAttrib()

    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
