"""
Copyright (C) 1997-2001 Id Software, Inc.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307, USA.

"""

import math
import OpenGL.GL as GL
import numpy as np
from ref_gl import gl_warp, gl_image, gl_rmain, gl_model, gl_model_h
from linux import qgl_linux
from game import q_shared
from qcommon import qfiles

"""
Python port of the GL surface handling code is still in progress.
The original C source is preserved in quake2-original/ref_gl/gl_rsurf.c for reference.
"""

modelorg = np.zeros((3,), dtype=np.float32)

class entity_t(object):
    """Temporary entity placeholder used during world rendering."""

    def __init__(self):
        self.frame = 0

DYNAMIC_LIGHT_WIDTH = 128
DYNAMIC_LIGHT_HEIGHT = 128

LIGHTMAP_BYTES = 4

BLOCK_WIDTH = 128
BLOCK_HEIGHT = 128
LIGHTMAP_BYTES = 4
MAX_LIGHTMAPS = 128
TURB_SCALE = 256.0 / (2 * math.pi)

r_alpha_surfaces = None


class gllightmapstate_t(object):

    def __init__(self):
        self.allocated = [0] * BLOCK_WIDTH
        self.lightmap_buffer = bytearray(4 * BLOCK_WIDTH * BLOCK_HEIGHT)
        self.current_lightmap_texture = 1
        self.internal_format = None
        self.lightmap_surfaces = [[] for _ in range(MAX_LIGHTMAPS)]
        self.lightmap_surfaces = [[] for _ in range(MAX_LIGHTMAPS)]


gl_lms = gllightmapstate_t()


def R_CullBox(mins, maxs):
    """Stubbed frustum check; always draws for now."""
    return False


def R_TextureAnimation(texinfo):
    if texinfo and texinfo.image:
        return texinfo.image
    return gl_rmain.r_notexture


def GL_RenderLightmappedPoly(surf):
    # placeholder for per-surface multitexture drawing path (defer to R_RenderBrushPoly)
    GL_BuildPolygonFromSurface(surf)

    if not surf.polys:
        return

    image = R_TextureAnimation(surf.texinfo)
    if image is None:
        return

    tex_base = gl_rmain.gl_state.lightmap_textures or gl_image.TEXNUM_LIGHTMAPS

    gl_image.GL_MBind(GL.GL_TEXTURE0, image.texnum)
    gl_image.GL_MBind(GL.GL_TEXTURE1, tex_base + surf.lightmaptexturenum)

    flowing = surf.texinfo and (surf.texinfo.flags & q_shared.SURF_FLOWING)
    scroll = 0.0
    if flowing:
        scroll = -64 * ((gl_rmain.r_newrefdef.time / 40.0) - int(gl_rmain.r_newrefdef.time / 40.0))
        if scroll == 0.0:
            scroll = -64.0

    poly = surf.polys
    while poly:
        v = poly.verts
        GL.glBegin(GL.GL_POLYGON)
        for i in range(poly.numverts):
            s = v[i, 3]
            if flowing:
                s += scroll
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0, s, v[i, 4])
            GL.glMultiTexCoord2f(GL.GL_TEXTURE1, v[i, 5], v[i, 6])
            GL.glVertex3fv(v[i, :3])
        GL.glEnd()
        poly = poly.chain


def R_AddSkySurface(surf):
    pass


GL_LIGHTMAP_FORMAT = GL.GL_RGBA


def R_SetCacheState(surf):
    pass


def R_BuildLightMap(surf, dest, stride):
    pass


def LM_InitBlock():

    gl_lms.allocated = [0] * BLOCK_WIDTH
    gl_lms.lightmap_surfaces = [[] for _ in range(MAX_LIGHTMAPS)]


def LM_AllocBlock(w, h):

    best = BLOCK_HEIGHT
    best_x = 0
    best_y = 0

    for i in range(BLOCK_WIDTH - w):
        best2 = 0
        for j in range(w):
            if gl_lms.allocated[i + j] >= best:
                break
            best2 = max(best2, gl_lms.allocated[i + j])
        else:
            best = best2
            best_x = i
            best_y = best2

    if best + h > BLOCK_HEIGHT:
        return None

    for i in range(w):
        gl_lms.allocated[best_x + i] = best + h

    return best_x, best_y


def LM_UploadBlock(dynamic=False):
    """Upload the allocated lightmap block to the selected GL texture."""
    texture = 0 if dynamic else gl_lms.current_lightmap_texture
    tex_base = gl_rmain.gl_state.lightmap_textures or gl_image.TEXNUM_LIGHTMAPS
    gl_image.GL_Bind(tex_base + texture)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

    if dynamic:
        height = max(gl_lms.allocated) if gl_lms.allocated else 0
        if height == 0:
            return
        size = BLOCK_WIDTH * height * LIGHTMAP_BYTES
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D,
            0,
            0,
            0,
            BLOCK_WIDTH,
            height,
            GL_LIGHTMAP_FORMAT,
            GL.GL_UNSIGNED_BYTE,
            gl_lms.lightmap_buffer[:size],
        )
    else:
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            gl_lms.internal_format or GL.GL_RGBA,
            BLOCK_WIDTH,
            BLOCK_HEIGHT,
            0,
            GL_LIGHTMAP_FORMAT,
            GL.GL_UNSIGNED_BYTE,
            gl_lms.lightmap_buffer,
        )
        gl_lms.current_lightmap_texture += 1
        if gl_lms.current_lightmap_texture == MAX_LIGHTMAPS:
            gl_rmain.ri.Sys_Error(
                q_shared.ERR_DROP, "LM_UploadBlock() - MAX_LIGHTMAPS exceeded"
            )


def GL_CreateSurfaceLightmap(surf):
    if surf.flags & (q_shared.SURF_SKY | gl_model_h.SURF_DRAWTURB):
        return

    smax = (surf.extents[0] >> 4) + 1
    tmax = (surf.extents[1] >> 4) + 1

    result = LM_AllocBlock(smax, tmax)
    if result is None:
        LM_UploadBlock(False)
        LM_InitBlock()
        result = LM_AllocBlock(smax, tmax)
        if result is None:
            raise RuntimeError("LM_AllocBlock failed twice")

    surf.light_s, surf.light_t = result
    surf.lightmaptexturenum = gl_lms.current_lightmap_texture

    base = gl_lms.lightmap_buffer
    offset = (surf.light_t * BLOCK_WIDTH + surf.light_s) * LIGHTMAP_BYTES
    dest = base[offset : offset + LIGHTMAP_BYTES * BLOCK_WIDTH * tmax]

    R_SetCacheState(surf)
    R_BuildLightMap(surf, dest, BLOCK_WIDTH * LIGHTMAP_BYTES)

    surfaces = gl_lms.lightmap_surfaces[surf.lightmaptexturenum]
    if surf not in surfaces:
        surfaces.append(surf)


def GL_BuildPolygonFromSurface(surf):

    currentmodel = gl_rmain.currentmodel
    if currentmodel is None or currentmodel.vertexes is None:
        return

    texinfo = surf.texinfo
    if texinfo is None:
        return

    pedges = currentmodel.edges
    numverts = surf.numedges
    poly = gl_model_h.glpoly_t()
    poly.next = surf.polys
    poly.flags = surf.flags
    poly.chain = surf.polys
    surf.polys = poly
    poly.numverts = numverts

    for i in range(numverts):
        lindex = int(currentmodel.surfedges[surf.firstedge + i])
        if lindex >= 0:
            edge = pedges[lindex]
            vertex_idx = int(edge[0])
        else:
            edge = pedges[-lindex]
            vertex_idx = int(edge[1])

        vec = currentmodel.vertexes[vertex_idx]

        s = (
            vec[0] * texinfo.vecs[0][0]
            + vec[1] * texinfo.vecs[0][1]
            + vec[2] * texinfo.vecs[0][2]
            + texinfo.vecs[0][3]
        )
        t = (
            vec[0] * texinfo.vecs[1][0]
            + vec[1] * texinfo.vecs[1][1]
            + vec[2] * texinfo.vecs[1][2]
            + texinfo.vecs[1][3]
        )

        width = texinfo.image.width if texinfo.image else 1.0
        height = texinfo.image.height if texinfo.image else 1.0
        s /= width
        t /= height

        poly.verts[i, :3] = vec
        poly.verts[i, 3] = s
        poly.verts[i, 4] = t

        light_s = (
            vec[0] * texinfo.vecs[0][0]
            + vec[1] * texinfo.vecs[0][1]
            + vec[2] * texinfo.vecs[0][2]
            + texinfo.vecs[0][3]
        )
        light_t = (
            vec[0] * texinfo.vecs[1][0]
            + vec[1] * texinfo.vecs[1][1]
            + vec[2] * texinfo.vecs[1][2]
            + texinfo.vecs[1][3]
        )
        light_s -= surf.texturemins[0]
        light_t -= surf.texturemins[1]
        light_s += surf.light_s * 16 + 8
        light_t += surf.light_t * 16 + 8
        light_s /= BLOCK_WIDTH * 16
        light_t /= BLOCK_HEIGHT * 16

        poly.verts[i, 5] = light_s
        poly.verts[i, 6] = light_t


def GL_BeginBuildingLightmaps(m):
    LM_InitBlock()
    gl_rmain.r_framecount = 1
    gl_image.GL_EnableMultitexture(True)
    gl_image.GL_SelectTexture(GL.GL_TEXTURE1)

    lightstyles = [{"rgb": (1, 1, 1), "white": 3}] * q_shared.MAX_LIGHTSTYLES
    gl_rmain.r_newrefdef.lightstyles = lightstyles

    if not gl_rmain.gl_state.lightmap_textures:
        gl_rmain.gl_state.lightmap_textures = gl_image.TEXNUM_LIGHTMAPS

    gl_lms.current_lightmap_texture = 1
    gl_lms.internal_format = gl_image.gl_tex_solid_format


def GL_EndBuildingLightmaps():
    LM_UploadBlock(False)
    gl_image.GL_EnableMultitexture(False)

r_alpha_surfaces = None


def R_DrawWorld ():

    if not gl_rmain.r_drawworld.value:
        return

    if gl_rmain.r_newrefdef.rdflags & q_shared.RDF_NOWORLDMODEL:
        return

    R_MarkLeaves ()

    gl_rmain.currentmodel = gl_rmain.r_worldmodel
    q_shared.VectorCopy (gl_rmain.r_newrefdef.vieworg, modelorg)

    ent = entity_t()
    ent.frame = int(gl_rmain.r_newrefdef.time * 2)
    gl_rmain.currententity = ent

    gl_rmain.gl_state.currenttextures[0] = -1
    gl_rmain.gl_state.currenttextures[1] = -1

    GL.glColor3f (1.0, 1.0, 1.0)
    gl_warp.R_ClearSkyBox ()

    root_node = (
        gl_rmain.r_worldmodel.nodes[0]
        if gl_rmain.r_worldmodel and gl_rmain.r_worldmodel.nodes
        else None
    )

    if qgl_linux.qglMTexCoord2fSGIS:

        gl_image.GL_EnableMultitexture (True)

        gl_image.GL_SelectTexture (GL.GL_TEXTURE0)
        gl_image.GL_TexEnv (GL.GL_REPLACE)
        gl_image.GL_SelectTexture (GL.GL_TEXTURE1)

        if gl_rmain.gl_lightmap.value:
            gl_image.GL_TexEnv (GL.GL_REPLACE)
        else:
            gl_image.GL_TexEnv (GL.GL_MODULATE)

        R_RecursiveWorldNode (root_node)

        gl_image.GL_EnableMultitexture (False)
    else:

        R_RecursiveWorldNode (root_node)

    DrawTextureChains ()
    R_BlendLightmaps ()
    R_DrawAlphaSurfaces ()

    gl_warp.R_DrawSkyBox ()
    R_DrawTriangleOutlines ()


def R_MarkLeaves ():

    world = gl_rmain.r_worldmodel
    if world is None:
        return

    if (
        gl_rmain.r_oldviewcluster == gl_rmain.r_viewcluster
        and gl_rmain.r_oldviewcluster2 == gl_rmain.r_viewcluster2
        and not gl_rmain.r_novis.value
        and gl_rmain.r_viewcluster != -1
    ):
        return

    if gl_rmain.gl_lockpvs and gl_rmain.gl_lockpvs.value:
        return

    gl_rmain.r_visframecount += 1
    gl_rmain.r_oldviewcluster = gl_rmain.r_viewcluster
    gl_rmain.r_oldviewcluster2 = gl_rmain.r_viewcluster2

    if gl_rmain.r_novis.value or gl_rmain.r_viewcluster == -1 or not world.vis:
        for leaf in world.leafs:
            leaf.visframe = gl_rmain.r_visframecount
        for node in world.nodes:
            node.visframe = gl_rmain.r_visframecount
        return

    row = (world.numleafs + 7) // 8
    base_vis = gl_model.Mod_ClusterPVS(gl_rmain.r_viewcluster, world)
    if base_vis is None:
        vis = bytearray(row)
    else:
        vis = bytearray(base_vis)

    if gl_rmain.r_viewcluster2 != gl_rmain.r_viewcluster and gl_rmain.r_viewcluster2 != -1:
        fatvis = bytearray(row)
        fatvis[:len(vis)] = vis[:row]
        vis2_raw = gl_model.Mod_ClusterPVS(gl_rmain.r_viewcluster2, world)
        vis2 = bytearray(vis2_raw if vis2_raw is not None else [0]*row)
        for i in range(row):
            val1 = fatvis[i]
            val2 = vis2[i] if i < len(vis2) else 0
            fatvis[i] = val1 | val2
        vis = fatvis
    else:
        vis = vis[:row]
        if len(vis) < row:
            vis += bytearray(row - len(vis))

    for leaf in world.leafs:
        cluster = leaf.cluster
        if cluster == -1:
            continue
        idx = cluster >> 3

        if idx < len(vis) and (vis[idx] & (1 << (cluster & 7))):
            node = leaf
            while node:
                if node.visframe == gl_rmain.r_visframecount:
                    break
                node.visframe = gl_rmain.r_visframecount
                node = node.parent




def R_RecursiveWorldNode (node):
    if node is None:
        return

    if node.contents == q_shared.CONTENTS_SOLID:
        return

    if node.visframe != gl_rmain.r_visframecount:
        return

    if R_CullBox (node.minmaxs[0:3], node.minmaxs[3:6]):
        return

    if node.contents != -1:
        leaf = node
        areabits = gl_rmain.r_newrefdef.areabits
        if areabits:
            area = leaf.area
            idx = area >> 3
            mask = 1 << (area & 7)
            if idx >= len(areabits) or not (areabits[idx] & mask):
                return

        for surf in leaf.firstmarksurface:
            surf.visframe = gl_rmain.r_framecount
        return

    plane = node.plane
    if plane is None:
        return

    if plane.type == qfiles.PLANE_X:
        dot = modelorg[0] - plane.dist
    elif plane.type == qfiles.PLANE_Y:
        dot = modelorg[1] - plane.dist
    elif plane.type == qfiles.PLANE_Z:
        dot = modelorg[2] - plane.dist
    else:
        dot = q_shared.DotProduct (modelorg, plane.normal) - plane.dist

    side = 0 if dot >= 0 else 1
    sidebit = 0 if side == 0 else q_shared.SURF_PLANEBACK

    R_RecursiveWorldNode (node.children[side])

    world = gl_rmain.r_worldmodel
    surfaces = world.surfaces
    start = node.firstsurface
    end = start + node.numsurfaces
    for surf in surfaces[start:end]:
        if surf.visframe != gl_rmain.r_framecount:
            continue
        if (surf.flags & q_shared.SURF_PLANEBACK) != sidebit:
            continue

        texinfo = surf.texinfo
        flags = texinfo.flags if texinfo else 0

        if flags & q_shared.SURF_SKY:
            R_AddSkySurface (surf)
        elif flags & (q_shared.SURF_TRANS33 | q_shared.SURF_TRANS66):
            global r_alpha_surfaces
            surf.texturechain = r_alpha_surfaces
            r_alpha_surfaces = surf
        else:
            if qgl_linux.qglMTexCoord2fSGIS and not (surf.flags & gl_model_h.SURF_DRAWTURB):
                GL_RenderLightmappedPoly (surf)
            else:
                image = R_TextureAnimation (surf.texinfo)
                surf.texturechain = image.texturechain
                image.texturechain = surf

    R_RecursiveWorldNode (node.children[1 - side])


def R_RenderBrushPoly(surf):
    GL_BuildPolygonFromSurface(surf)


def DrawTextureChains ():
    """Iterates texture chains, dispatching brush polys for rendering."""

    for image in gl_image.gltextures[: gl_image.numgltextures]:

        if not image.registration_sequence:
            continue

        surf = image.texturechain
        if not surf:
            continue

        while surf:
            R_RenderBrushPoly(surf)
            surf = surf.texturechain

        image.texturechain = None


def DrawGLPolyChain(polys, soffset=0.0, toffset=0.0):
    while polys:
        GL.glBegin(GL.GL_POLYGON)
        verts = polys.verts
        for j in range(polys.numverts):
            GL.glTexCoord2f(verts[j, 5] - soffset, verts[j, 6] - toffset)
            GL.glVertex3fv(verts[j, :3])
        GL.glEnd()
        polys = polys.chain


def DrawGLPoly(polys):
    """Draw a regular polygon chain using texture coordinates from the surface."""
    while polys:
        gl_rmain.c_brush_polys += 1
        GL.glBegin(GL.GL_POLYGON)
        for j in range(polys.numverts):
            v = polys.verts[j]
            GL.glTexCoord2f(v[3], v[4])
            GL.glVertex3fv(v[:3])
        GL.glEnd()
        polys = polys.chain


def DrawGLFlowingPoly(surf):
    """Draw a flowing surface by scrolling its texture coordinates."""
    if not surf or not surf.polys:
        return
    poly = surf.polys
    scroll = -64 * ((gl_rmain.r_newrefdef.time / 40.0) - int(gl_rmain.r_newrefdef.time / 40.0))
    if scroll == 0.0:
        scroll = -64.0
    gl_rmain.c_brush_polys += 1
    GL.glBegin(GL.GL_POLYGON)
    for i in range(poly.numverts):
        v = poly.verts[i]
        GL.glTexCoord2f(v[3] + scroll, v[4])
        GL.glVertex3fv(v[:3])
    GL.glEnd()


def EmitWaterPolys(surf):
    """Warp a water surface for a dynamic water effect."""
    if not surf or not surf.polys:
        return
    time = gl_rmain.r_newrefdef.time
    flowing = surf.texinfo and (surf.texinfo.flags & q_shared.SURF_FLOWING)
    scroll = 0.0
    if flowing:
        scroll = -64 * ((time * 0.5) - int(time * 0.5))
    poly = surf.polys
    while poly:
        gl_rmain.c_brush_polys += 1
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        for i in range(poly.numverts):
            v = poly.verts[i]
            os = v[3]
            ot = v[4]
            s = os + math.sin((ot * 0.125 + time) * TURB_SCALE)
            s += scroll
            s *= 1.0 / 64.0
            t = ot + math.sin((os * 0.125 + time) * TURB_SCALE)
            t *= 1.0 / 64.0
            GL.glTexCoord2f(s, t)
            GL.glVertex3fv(v[:3])
        GL.glEnd()
        poly = poly.chain

def R_BlendLightmaps ():
    """Blends the static and dynamic lightmapped surfaces."""
    world = gl_rmain.r_worldmodel
    if gl_rmain.r_fullbright.value or world is None or not world.lightdata:
        return

    GL.glDepthMask(GL.GL_FALSE)

    if not gl_rmain.gl_lightmap.value:
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)

    tex_base = gl_rmain.gl_state.lightmap_textures or gl_image.TEXNUM_LIGHTMAPS

    for idx, surfaces in enumerate(gl_lms.lightmap_surfaces):
        if idx == 0 or not surfaces:
            continue
        gl_image.GL_Bind(tex_base + idx)
        for surf in surfaces:
            if surf.polys:
                DrawGLPolyChain(surf.polys, 0.0, 0.0)

    if (
        gl_rmain.gl_dynamic
        and gl_rmain.gl_dynamic.value
        and gl_lms.lightmap_surfaces[0]
    ):
        LM_InitBlock()
        gl_image.GL_Bind(tex_base + 0)
        dyn_surfaces = gl_lms.lightmap_surfaces[0]
        newdrawsurf_idx = 0
        for idx, surf in enumerate(dyn_surfaces):
            smax = (surf.extents[0] >> 4) + 1
            tmax = (surf.extents[1] >> 4) + 1
            result = LM_AllocBlock(smax, tmax)
            if result is None:
                LM_UploadBlock(True)
                for drawsurf in dyn_surfaces[newdrawsurf_idx:idx]:
                    if drawsurf.polys:
                        soff = (drawsurf.light_s - drawsurf.dlight_s) * (1.0 / 128.0)
                        toff = (drawsurf.light_t - drawsurf.dlight_t) * (1.0 / 128.0)
                        DrawGLPolyChain(drawsurf.polys, soff, toff)
                newdrawsurf_idx = idx
                LM_InitBlock()
                result = LM_AllocBlock(smax, tmax)
                if result is None:
                    raise RuntimeError("LM_AllocBlock failed twice (dynamic)")
            surf.dlight_s, surf.dlight_t = result
            offset = (surf.dlight_t * BLOCK_WIDTH + surf.dlight_s) * LIGHTMAP_BYTES
            dest = gl_lms.lightmap_buffer[
                offset : offset + BLOCK_WIDTH * LIGHTMAP_BYTES * tmax
            ]
            R_BuildLightMap(surf, dest, BLOCK_WIDTH * LIGHTMAP_BYTES)
        if newdrawsurf_idx < len(dyn_surfaces):
            LM_UploadBlock(True)
        for drawsurf in dyn_surfaces[newdrawsurf_idx:]:
            if drawsurf.polys:
                soff = (drawsurf.light_s - drawsurf.dlight_s) * (1.0 / 128.0)
                toff = (drawsurf.light_t - drawsurf.dlight_t) * (1.0 / 128.0)
                DrawGLPolyChain(drawsurf.polys, soff, toff)

    GL.glDepthMask(GL.GL_TRUE)
    if not gl_rmain.gl_lightmap.value:
        GL.glDisable(GL.GL_BLEND)


def R_DrawAlphaSurfaces():
    global r_alpha_surfaces

    if r_alpha_surfaces is None:
        return

    GL.glLoadMatrixf(gl_rmain.r_world_matrix)
    GL.glEnable(GL.GL_BLEND)
    gl_image.GL_TexEnv(GL.GL_MODULATE)

    intensity = getattr(gl_rmain.gl_state, "inverse_intensity", 1.0) or 1.0
    surf = r_alpha_surfaces
    while surf:
        texnum = surf.texinfo.image.texnum if surf.texinfo and surf.texinfo.image else 0
        gl_image.GL_Bind(texnum)
        flags = surf.texinfo.flags if surf.texinfo else 0
        alpha = 1.0
        if flags & q_shared.SURF_TRANS33:
            alpha = 0.33
        elif flags & q_shared.SURF_TRANS66:
            alpha = 0.66
        GL.glColor4f(intensity, intensity, intensity, alpha)

        if surf.flags & gl_model_h.SURF_DRAWTURB:
            EmitWaterPolys(surf)
        elif flags & q_shared.SURF_FLOWING:
            DrawGLFlowingPoly(surf)
        else:
            DrawGLPoly(surf.polys)

        surf = surf.texturechain

    gl_image.GL_TexEnv(GL.GL_REPLACE)
    GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    GL.glDisable(GL.GL_BLEND)
    r_alpha_surfaces = None


def R_DrawTriangleOutlines ():
    """Stub that will later draw debug triangle outlines."""
    pass
