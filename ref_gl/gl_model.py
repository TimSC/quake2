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
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

"""
import numpy as np
from ref_gl import gl_rmain, gl_model_h, gl_image
from qcommon import qfiles
from game import q_shared
"""
// models.c -- model loading and caching

#include "gl_local.h"

"""
loadmodel = None #model_t	*
modfilelen = None #int
"""
void Mod_LoadSpriteModel (model_t *mod, void *buffer);
void Mod_LoadBrushModel (model_t *mod, void *buffer);
void Mod_LoadAliasModel (model_t *mod, void *buffer);
model_t *Mod_LoadModel (model_t *mod, qboolean crash);
"""
mod_novis = None# byte[MAX_MAP_LEAFS/8];

MAX_MOD_KNOWN	= 512
mod_known = [] #model_t[MAX_MOD_KNOWN]
for i in range(MAX_MOD_KNOWN):
	mod_known.append(gl_model_h.model_t())
mod_numknown = 0 #int
"""
// the inline * models from the current map are kept seperate
model_t	mod_inline[MAX_MOD_KNOWN];
"""
registration_sequence = 0 #int		
"""
/*
===============
Mod_PointInLeaf
===============
*/
mleaf_t *Mod_PointInLeaf (vec3_t p, model_t *model)
{
	mnode_t		*node;
	float		d;
	cplane_t	*plane;
	
	if (!model || !model->nodes)
		ri.Sys_Error (ERR_DROP, "Mod_PointInLeaf: bad model");

	node = model->nodes;
	while (1)
	{
		if (node->contents != -1)
			return (mleaf_t *)node;
		plane = node->plane;
		d = DotProduct (p,plane->normal) - plane->dist;
		if (d > 0)
			node = node->children[0];
		else
			node = node->children[1];
	}
	
	return NULL;	// never reached
}


/*
===================
Mod_DecompressVis
===================
*/
byte *Mod_DecompressVis (byte *in, model_t *model)
{
	static byte	decompressed[MAX_MAP_LEAFS/8];
	int		c;
	byte	*out;
	int		row;

	row = (model->vis->numclusters+7)>>3;	
	out = decompressed;

	if (!in)
	{	// no vis info, so make all visible
		while (row)
		{
			*out++ = 0xff;
			row--;
		}
		return decompressed;		
	}

	do
	{
		if (*in)
		{
			*out++ = *in++;
			continue;
		}
	
		c = in[1];
		in += 2;
		while (c)
		{
			*out++ = 0;
			c--;
		}
	} while (out - decompressed < row);
	
	return decompressed;
}

/*
==============
Mod_ClusterPVS
==============
*/
byte *Mod_ClusterPVS (int cluster, model_t *model)
{
	if (cluster == -1 || !model->vis)
		return mod_novis;
	return Mod_DecompressVis ( (byte *)model->vis + model->vis->bitofs[cluster][DVIS_PVS],
		model);
}


//===============================================================================

/*
================
Mod_Modellist_f
================
*/
void Mod_Modellist_f (void)
{
	int		i;
	model_t	*mod;
	int		total;

	total = 0;
	ri.Con_Printf (PRINT_ALL,"Loaded models:\n");
	for (i=0, mod=mod_known ; i < mod_numknown ; i++, mod++)
	{
		if (!mod->name[0])
			continue;
		ri.Con_Printf (PRINT_ALL, "%8i : %s\n",mod->extradatasize, mod->name);
		total += mod->extradatasize;
	}
	ri.Con_Printf (PRINT_ALL, "Total resident: %i\n", total);
}

/*
===============
Mod_Init
===============
"""
def Mod_Init ():
	global mod_novis

	mod_novis = bytearray([0xff]*(qfiles.MAX_MAP_LEAFS//8))


"""
==================
Mod_ForName

Loads in a model for the given name
==================
"""
def Mod_ForName (name, crash)->gl_model_h.model_t: #char *, qboolean

	global loadmodel, modfilelen, mod_numknown
	"""
	model_t	*mod;
	unsigned *buf;
	int		i;
	"""
	
	if name is None or len(name) == 0:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "Mod_ForName: NULL name");
		
	#
	# inline models are grabbed only from worldmodel
	#
	if name[0] == '*':
	
		i = int(name[1:])
		if i < 1 or gl_rmain.r_worldmodel is None or i >= gl_rmain.r_worldmodel.numsubmodels:
			gl_rmain.ri.Sys_Error (ERR_DROP, "bad inline model number")
		return mod_inline[i]


	#
	# search the currently loaded models
	#
	for i in range(mod_numknown):
		mod = mod_known[i]
	
		if mod.name is None:
			continue
		if mod.name == name:
			return mod
	
	
	#
	# find a free model slot spot
	#
	found = False
	mod = None
	for i in range(mod_numknown):
	
		mod = mod_known[i]

		if mod.name is None:
			found = True
			break	# free spot
	
	if not found:
		# assign next mod
		if mod_numknown == MAX_MOD_KNOWN:
			gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "mod_numknown == MAX_MOD_KNOWN")
		mod = mod_known[mod_numknown]
		mod_numknown+=1
	
	mod.name = name
	
	#
	# load the file
	#
	modfilelen, buf = gl_rmain.ri.FS_LoadFile (mod.name)
	if buf is None:
	
		if crash:
			gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "Mod_NumForName: {} not found".format(mod.name))
		mod.name = None
		return None
	
	loadmodel = mod

	#
	# fill it in
	#


	# call the apropriate loader

	val = q_shared.LittleLong(buf[:4])

	if val == qfiles.IDALIASHEADER:
		#loadmodel.extradata = Hunk_Begin (0x200000)
		Mod_LoadAliasModel (mod, buf)
		
	elif val == qfiles.IDSPRITEHEADER:
		#loadmodel.extradata = Hunk_Begin (0x10000)
		Mod_LoadSpriteModel (mod, buf)
	
	elif val == qfiles.IDBSPHEADER:
		#loadmodel.extradata = Hunk_Begin (0x1000000)
		Mod_LoadBrushModel (mod, buf)

	else:
		gl_rmain.ri.Sys_Error (ERR_DROP,"Mod_NumForName: unknown fileid for {}".format(mod.name))

	#loadmodel.extradatasize = Hunk_End ()

	#ri.FS_FreeFile (buf)

	return mod

"""
===============================================================================

					BRUSHMODEL LOADING

===============================================================================
*/
"""
mod_base = None #byte *


"""
=================
Mod_LoadLighting
=================
"""
def Mod_LoadLighting (l: qfiles.lump_t):

	if not l.filelen:
	
		loadmodel.lightdata = None
		return
	
	in_offset = l.fileofs
	in_offset2 = in_offset + l.filelen

	loadmodel.lightdata = mod_base[in_offset:in_offset2]


"""
=================
Mod_LoadVisibility
=================
*/
void Mod_LoadVisibility (qfiles.lump_t *l)
{
	int		i;

	if (!l->filelen)
	{
		loadmodel->vis = NULL;
		return;
	}
	loadmodel->vis = Hunk_Alloc ( l->filelen);	
	memcpy (loadmodel->vis, mod_base + l->fileofs, l->filelen);

	loadmodel->vis->numclusters = q_shared.LittleLong (loadmodel->vis->numclusters);
	for (i=0 ; i<loadmodel->vis->numclusters ; i++)
	{
		loadmodel->vis->bitofs[i][0] = q_shared.LittleLong (loadmodel->vis->bitofs[i][0]);
		loadmodel->vis->bitofs[i][1] = q_shared.LittleLong (loadmodel->vis->bitofs[i][1]);
	}
}


/*
=================
Mod_LoadVertexes
=================
"""
def Mod_LoadVertexes (l): #qfiles.lump_t *

	global mod_base, loadmodel
	print ("Mod_LoadVertexes", l)
	"""
	dvertex_t	*in;
	mvertex_t	*out;
	int			i, count;
	"""

	#in = (void *)(mod_base + l->fileofs);
	if l.filelen % qfiles.dvertex_t.packed_size():
		gl_rmain.ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size in {}".format(loadmodel.name))
	count = l.filelen // qfiles.dvertex_t.packed_size()
	#out = Hunk_Alloc ( count*sizeof(*out))

	loadmodel.vertexes = np.zeros((count, 3), dtype=np.float32)
	loadmodel.numvertexes = count
	in_obj = qfiles.dvertex_t()
	out = loadmodel.vertexes

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.dvertex_t.packed_size()
		in_offset2 = in_offset + qfiles.dvertex_t.packed_size()
		in_obj.load(mod_base[in_offset:in_offset2])

		out[i, 0] = in_obj.point[0]
		out[i, 1] = in_obj.point[1]
		out[i, 2] = in_obj.point[2]

"""
=================
RadiusFromBounds
=================
*/
float RadiusFromBounds (vec3_t mins, vec3_t maxs)
{
	int		i;
	vec3_t	corner;

	for (i=0 ; i<3 ; i++)
	{
		corner[i] = fabs(mins[i]) > fabs(maxs[i]) ? fabs(mins[i]) : fabs(maxs[i]);
	}

	return VectorLength (corner);
}


/*
=================
Mod_LoadSubmodels
=================
*/
void Mod_LoadSubmodels (qfiles.lump_t *l)
{
	dmodel_t	*in;
	mmodel_t	*out;
	int			i, j, count;

	in = (void *)(mod_base + l->fileofs);
	if (l->filelen % sizeof(*in))
		ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size in %s",loadmodel->name);
	count = l->filelen / sizeof(*in);
	out = Hunk_Alloc ( count*sizeof(*out));	

	loadmodel->submodels = out;
	loadmodel->numsubmodels = count;

	for ( i=0 ; i<count ; i++, in++, out++)
	{
		for (j=0 ; j<3 ; j++)
		{	// spread the mins / maxs by a pixel
			out->mins[j] = LittleFloat (in->mins[j]) - 1;
			out->maxs[j] = LittleFloat (in->maxs[j]) + 1;
			out->origin[j] = LittleFloat (in->origin[j]);
		}
		out->radius = RadiusFromBounds (out->mins, out->maxs);
		out->headnode = q_shared.LittleLong (in->headnode);
		out->firstface = q_shared.LittleLong (in->firstface);
		out->numfaces = q_shared.LittleLong (in->numfaces);
	}
}

/*
=================
Mod_LoadEdges
=================
"""
def Mod_LoadEdges (l: qfiles.lump_t):

	print ("Mod_LoadEdges", l)
	"""
	dedge_t *in;
	medge_t *out;
	int 	i, count;
	"""

	#in = (void *)(mod_base + l->fileofs);
	if l.filelen % qfiles.dedge_t.packed_size():
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size in {}".format(loadmodel.name))
	count = l.filelen // qfiles.dedge_t.packed_size()
	out = np.zeros((count, 2), dtype=np.uint16)

	loadmodel.edges = out
	loadmodel.numedges = count
	in_obj = qfiles.dedge_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.dedge_t.packed_size()
		in_offset2 = in_offset + qfiles.dedge_t.packed_size()
		in_obj.load(mod_base[in_offset:in_offset2])

		out[i, 0] = in_obj.v[0]
		out[i, 1] = in_obj.v[1]
	


"""
=================
Mod_LoadTexinfo
=================
"""
def Mod_LoadTexinfo (l: qfiles.lump_t):

	print ("Mod_LoadTexinfo", l)
	"""
	texinfo_t *in;
	mtexinfo_t *out, *step;
	int 	i, j, count;
	char	name[MAX_QPATH];
	int		next;
	"""

	#in = (void *)(mod_base + l->fileofs);
	if l.filelen % qfiles.texinfo_t.packed_size():
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size in {}".format(loadmodel.name))
	count = l.filelen // qfiles.texinfo_t.packed_size()
	out = []

	loadmodel.texinfo = out
	loadmodel.numtexinfo = count
	in_obj = qfiles.texinfo_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.texinfo_t.packed_size()
		in_offset2 = in_offset + qfiles.texinfo_t.packed_size()
		in_obj.load(mod_base[in_offset:in_offset2])

		out_obj = gl_model_h.mtexinfo_t()

		out_obj.vecs = in_obj.vecs.copy()

		out_obj.flags = in_obj.flags
		next = in_obj.nexttexinfo

		if next > 0:
			out_obj.next = next
		else:
		    out_obj.next = None
		name = "textures/{}.wal".format(in_obj.texture)

		out_obj.image = gl_image.GL_FindImage (name, gl_image.imagetype_t.it_wall)
		if out_obj.image is None:
		
			gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "Couldn't load {}\n".format(name))
			out_obj.image = gl_rmain.r_notexture
		
		out.append(out_obj)

	
	# count animation frames
	for i in range(count):
	
		out = loadmodel.texinfo[i]
		out.numframes = 1
		step = None
		if out.next is not None:
			step = loadmodel.texinfo[out.next]

		while step is not None and id(step) != id(out):
			out.numframes+=1

			if step.next is not None:
				step = loadmodel.texinfo[step.next]
			else:
				step = None


"""
================
CalcSurfaceExtents

Fills in s->texturemins[] and s->extents[]
================
*/
void CalcSurfaceExtents (msurface_t *s)
{
	float	mins[2], maxs[2], val;
	int		i,j, e;
	mvertex_t	*v;
	mtexinfo_t	*tex;
	int		bmins[2], bmaxs[2];

	mins[0] = mins[1] = 999999;
	maxs[0] = maxs[1] = -99999;

	tex = s->texinfo;
	
	for (i=0 ; i<s->numedges ; i++)
	{
		e = loadmodel->surfedges[s->firstedge+i];
		if (e >= 0)
			v = &loadmodel->vertexes[loadmodel->edges[e].v[0]];
		else
			v = &loadmodel->vertexes[loadmodel->edges[-e].v[1]];
		
		for (j=0 ; j<2 ; j++)
		{
			val = v->position[0] * tex->vecs[j][0] + 
				v->position[1] * tex->vecs[j][1] +
				v->position[2] * tex->vecs[j][2] +
				tex->vecs[j][3];
			if (val < mins[j])
				mins[j] = val;
			if (val > maxs[j])
				maxs[j] = val;
		}
	}

	for (i=0 ; i<2 ; i++)
	{	
		bmins[i] = floor(mins[i]/16);
		bmaxs[i] = ceil(maxs[i]/16);

		s->texturemins[i] = bmins[i] * 16;
		s->extents[i] = (bmaxs[i] - bmins[i]) * 16;

//		if ( !(tex->flags & TEX_SPECIAL) && s->extents[i] > 512 /* 256 */ )
//			ri.Sys_Error (ERR_DROP, "Bad surface extents");
	}
}


void GL_BuildPolygonFromSurface(msurface_t *fa);
void GL_CreateSurfaceLightmap (msurface_t *surf);
void GL_EndBuildingLightmaps (void);
void GL_BeginBuildingLightmaps (model_t *m);

/*
=================
Mod_LoadFaces
=================
*/
void Mod_LoadFaces (qfiles.lump_t *l)
{
	dface_t		*in;
	msurface_t 	*out;
	int			i, count, surfnum;
	int			planenum, side;
	int			ti;

	in = (void *)(mod_base + l->fileofs);
	if (l->filelen % sizeof(*in))
		ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size in %s",loadmodel->name);
	count = l->filelen / sizeof(*in);
	out = Hunk_Alloc ( count*sizeof(*out));	

	loadmodel->surfaces = out;
	loadmodel->numsurfaces = count;

	currentmodel = loadmodel;

	GL_BeginBuildingLightmaps (loadmodel);

	for ( surfnum=0 ; surfnum<count ; surfnum++, in++, out++)
	{
		out->firstedge = q_shared.LittleLong(in->firstedge);
		out->numedges = LittleShort(in->numedges);		
		out->flags = 0;
		out->polys = NULL;

		planenum = LittleShort(in->planenum);
		side = LittleShort(in->side);
		if (side)
			out->flags |= SURF_PLANEBACK;			

		out->plane = loadmodel->planes + planenum;

		ti = LittleShort (in->texinfo);
		if (ti < 0 || ti >= loadmodel->numtexinfo)
			ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: bad texinfo number");
		out->texinfo = loadmodel->texinfo + ti;

		CalcSurfaceExtents (out);
				
	// lighting info

		for (i=0 ; i<MAXLIGHTMAPS ; i++)
			out->styles[i] = in->styles[i];
		i = q_shared.LittleLong(in->lightofs);
		if (i == -1)
			out->samples = NULL;
		else
			out->samples = loadmodel->lightdata + i;
		
	// set the drawing flags
		
		if (out->texinfo->flags & SURF_WARP)
		{
			out->flags |= SURF_DRAWTURB;
			for (i=0 ; i<2 ; i++)
			{
				out->extents[i] = 16384;
				out->texturemins[i] = -8192;
			}
			GL_SubdivideSurface (out);	// cut up polygon for warps
		}

		// create lightmaps and polygons
		if ( !(out->texinfo->flags & (SURF_SKY|SURF_TRANS33|SURF_TRANS66|SURF_WARP) ) )
			GL_CreateSurfaceLightmap (out);

		if (! (out->texinfo->flags & SURF_WARP) ) 
			GL_BuildPolygonFromSurface(out);

	}

	GL_EndBuildingLightmaps ();
}


/*
=================
Mod_SetParent
=================
*/
void Mod_SetParent (mnode_t *node, mnode_t *parent)
{
	node->parent = parent;
	if (node->contents != -1)
		return;
	Mod_SetParent (node->children[0], node);
	Mod_SetParent (node->children[1], node);
}

/*
=================
Mod_LoadNodes
=================
*/
void Mod_LoadNodes (qfiles.lump_t *l)
{
	int			i, j, count, p;
	dnode_t		*in;
	mnode_t 	*out;

	in = (void *)(mod_base + l->fileofs);
	if (l->filelen % sizeof(*in))
		ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size in %s",loadmodel->name);
	count = l->filelen / sizeof(*in);
	out = Hunk_Alloc ( count*sizeof(*out));	

	loadmodel->nodes = out;
	loadmodel->numnodes = count;

	for ( i=0 ; i<count ; i++, in++, out++)
	{
		for (j=0 ; j<3 ; j++)
		{
			out->minmaxs[j] = LittleShort (in->mins[j]);
			out->minmaxs[3+j] = LittleShort (in->maxs[j]);
		}
	
		p = q_shared.LittleLong(in->planenum);
		out->plane = loadmodel->planes + p;

		out->firstsurface = LittleShort (in->firstface);
		out->numsurfaces = LittleShort (in->numfaces);
		out->contents = -1;	// differentiate from leafs

		for (j=0 ; j<2 ; j++)
		{
			p = q_shared.LittleLong (in->children[j]);
			if (p >= 0)
				out->children[j] = loadmodel->nodes + p;
			else
				out->children[j] = (mnode_t *)(loadmodel->leafs + (-1 - p));
		}
	}
	
	Mod_SetParent (loadmodel->nodes, NULL);	// sets nodes and leafs
}

/*
=================
Mod_LoadLeafs
=================
*/
void Mod_LoadLeafs (qfiles.lump_t *l)
{
	dleaf_t 	*in;
	mleaf_t 	*out;
	int			i, j, count, p;
//	glpoly_t	*poly;

	in = (void *)(mod_base + l->fileofs);
	if (l->filelen % sizeof(*in))
		ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size in %s",loadmodel->name);
	count = l->filelen / sizeof(*in);
	out = Hunk_Alloc ( count*sizeof(*out));	

	loadmodel->leafs = out;
	loadmodel->numleafs = count;

	for ( i=0 ; i<count ; i++, in++, out++)
	{
		for (j=0 ; j<3 ; j++)
		{
			out->minmaxs[j] = LittleShort (in->mins[j]);
			out->minmaxs[3+j] = LittleShort (in->maxs[j]);
		}

		p = q_shared.LittleLong(in->contents);
		out->contents = p;

		out->cluster = LittleShort(in->cluster);
		out->area = LittleShort(in->area);

		out->firstmarksurface = loadmodel->marksurfaces +
			LittleShort(in->firstleafface);
		out->nummarksurfaces = LittleShort(in->numleaffaces);
		
		// gl underwater warp
#if 0
		if (out->contents & (CONTENTS_WATER|CONTENTS_SLIME|CONTENTS_LAVA|CONTENTS_THINWATER) )
		{
			for (j=0 ; j<out->nummarksurfaces ; j++)
			{
				out->firstmarksurface[j]->flags |= SURF_UNDERWATER;
				for (poly = out->firstmarksurface[j]->polys ; poly ; poly=poly->next)
					poly->flags |= SURF_UNDERWATER;
			}
		}
#endif
	}	
}

/*
=================
Mod_LoadMarksurfaces
=================
*/
void Mod_LoadMarksurfaces (qfiles.lump_t *l)
{	
	int		i, j, count;
	short		*in;
	msurface_t **out;
	
	in = (void *)(mod_base + l->fileofs);
	if (l->filelen % sizeof(*in))
		ri.Sys_Error (ERR_DROP, "MOD_LoadBmodel: funny lump size in %s",loadmodel->name);
	count = l->filelen / sizeof(*in);
	out = Hunk_Alloc ( count*sizeof(*out));	

	loadmodel->marksurfaces = out;
	loadmodel->nummarksurfaces = count;

	for ( i=0 ; i<count ; i++)
	{
		j = LittleShort(in[i]);
		if (j < 0 ||  j >= loadmodel->numsurfaces)
			ri.Sys_Error (ERR_DROP, "Mod_ParseMarksurfaces: bad surface number");
		out[i] = loadmodel->surfaces + j;
	}
}

/*
=================
Mod_LoadSurfedges
=================
"""
def Mod_LoadSurfedges (l: qfiles.lump_t):
	
	print ("Mod_LoadSurfedges", l)	
	#int		i, count;
	#int		*in, *out;
	
	#in = (void *)(mod_base + l->fileofs);
	if l.filelen % 4:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size in {}".format(loadmodel.name))
	count = l.filelen // 4
	if count < 1 or count >= qfiles.MAX_MAP_SURFEDGES:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: bad surfedges count in {}: {}".format(
		loadmodel.name, count))

	out = np.zeros((count,), dtype=np.int32)

	loadmodel.surfedges = out
	loadmodel.numsurfedges = count

	for i in range(count):
		in_offset = l.fileofs + i * 4
		in_offset2 = in_offset + 4

		out[i] = q_shared.LittleSLong (mod_base[in_offset: in_offset2])



"""
=================
Mod_LoadPlanes
=================
"""
def Mod_LoadPlanes (l: qfiles.lump_t):

	print ("Mod_LoadPlanes", l)
	"""
	int			i, j;
	cplane_t	*out;
	dplane_t 	*in;
	int			count;
	int			bits;
	"""	

	#in = (void *)(mod_base + l->fileofs);
	if l.filelen % qfiles.dplane_t.packed_size():
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size in {}".format(loadmodel.name))
	count = l.filelen // qfiles.dplane_t.packed_size()
	out = []
	
	loadmodel.planes = out
	loadmodel.numplanes = count
	in_obj = qfiles.dplane_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.dplane_t.packed_size()
		in_offset2 = in_offset + qfiles.dplane_t.packed_size()
		in_obj.load(mod_base[in_offset:in_offset2])

		out_obj = q_shared.cplane_t()

		bits = 0
		for j in range(3):
		
			out_obj.normal[j] = in_obj.normal[j]
			if out_obj.normal[j] < 0.0:
				bits |= (1<<j)
		
		out_obj.dist = in_obj.dist
		out_obj.type = in_obj.type
		out_obj.signbits = bits
	
		out.append(out_obj)


"""
=================
Mod_LoadBrushModel
=================
"""
def Mod_LoadBrushModel (mod, buff): #model_t *, void *

	global loadmodel, mod_base
	print ("Mod_LoadBrushModel")
	"""
	int			i;
	dheader_t	*header;
	mmodel_t 	*bm;
	"""
	
	loadmodel.type = gl_model_h.modtype_t.mod_brush
	if id(loadmodel) != id(mod_known[0]):
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "Loaded a brush model after the world")

	header = qfiles.dheader_t()
	header.parse(buff)

	if header.version != qfiles.BSPVERSION:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "Mod_LoadBrushModel: {} has wrong version number ({} should be {})".format(mod.name, i, qfiles.BSPVERSION))

	mod_base = buff

	# load into heap
	
	Mod_LoadVertexes (header.lumps[qfiles.LUMP_VERTEXES])
	Mod_LoadEdges (header.lumps[qfiles.LUMP_EDGES])
	Mod_LoadSurfedges (header.lumps[qfiles.LUMP_SURFEDGES])
	Mod_LoadLighting (header.lumps[qfiles.LUMP_LIGHTING])
	Mod_LoadPlanes (header.lumps[qfiles.LUMP_PLANES])
	Mod_LoadTexinfo (header.lumps[qfiles.LUMP_TEXINFO])
	"""
	Mod_LoadFaces (header.lumps[qfiles.LUMP_FACES])
	Mod_LoadMarksurfaces (header.lumps[qfiles.LUMP_LEAFFACES])
	Mod_LoadVisibility (header.lumps[qfiles.LUMP_VISIBILITY])
	Mod_LoadLeafs (header.lumps[qfiles.LUMP_LEAFS])
	Mod_LoadNodes (header.lumps[qfiles.LUMP_NODES])
	Mod_LoadSubmodels (header.lumps[qfiles.LUMP_MODELS])
	mod.numframes = 2		# regular and alternate animation


	
#
# set up the submodels
#
	for (i=0 ; i<mod->numsubmodels ; i++)
	{
		model_t	*starmod;

		bm = &mod->submodels[i];
		starmod = &mod_inline[i];

		*starmod = *loadmodel;
		
		starmod->firstmodelsurface = bm->firstface;
		starmod->nummodelsurfaces = bm->numfaces;
		starmod->firstnode = bm->headnode;
		if (starmod->firstnode >= loadmodel->numnodes)
			ri.Sys_Error (ERR_DROP, "Inline model %i has bad firstnode", i);

		VectorCopy (bm->maxs, starmod->maxs);
		VectorCopy (bm->mins, starmod->mins);
		starmod->radius = bm->radius;
	
		if (i == 0)
			*loadmodel = *starmod;

		starmod->numleafs = bm->visleafs;
	}
}

/*
==============================================================================

ALIAS MODELS

==============================================================================
*/

/*
=================
Mod_LoadAliasModel
=================
"""
def Mod_LoadAliasModel (mod, buff): #model_t *, void *

	print ("Mod_LoadAliasModel")
	raise NotImplementedError()
	"""
	int					i, j;
	dmdl_t				*pinmodel, *pheader;
	dstvert_t			*pinst, *poutst;
	dtriangle_t			*pintri, *pouttri;
	daliasframe_t		*pinframe, *poutframe;
	int					*pincmd, *poutcmd;
	int					version;

	pinmodel = (dmdl_t *)buffer;

	version = q_shared.LittleLong (pinmodel->version);
	if (version != ALIAS_VERSION)
		ri.Sys_Error (ERR_DROP, "%s has wrong version number (%i should be %i)",
				 mod->name, version, ALIAS_VERSION);

	pheader = Hunk_Alloc (q_shared.LittleLong(pinmodel->ofs_end));
	
	// byte swap the header fields and sanity check
	for (i=0 ; i<sizeof(dmdl_t)/4 ; i++)
		((int *)pheader)[i] = q_shared.LittleLong (((int *)buffer)[i]);

	if (pheader->skinheight > MAX_LBM_HEIGHT)
		ri.Sys_Error (ERR_DROP, "model %s has a skin taller than %d", mod->name,
				   MAX_LBM_HEIGHT);

	if (pheader->num_xyz <= 0)
		ri.Sys_Error (ERR_DROP, "model %s has no vertices", mod->name);

	if (pheader->num_xyz > MAX_VERTS)
		ri.Sys_Error (ERR_DROP, "model %s has too many vertices", mod->name);

	if (pheader->num_st <= 0)
		ri.Sys_Error (ERR_DROP, "model %s has no st vertices", mod->name);

	if (pheader->num_tris <= 0)
		ri.Sys_Error (ERR_DROP, "model %s has no triangles", mod->name);

	if (pheader->num_frames <= 0)
		ri.Sys_Error (ERR_DROP, "model %s has no frames", mod->name);

//
// load base s and t vertices (not used in gl version)
//
	pinst = (dstvert_t *) ((byte *)pinmodel + pheader->ofs_st);
	poutst = (dstvert_t *) ((byte *)pheader + pheader->ofs_st);

	for (i=0 ; i<pheader->num_st ; i++)
	{
		poutst[i].s = LittleShort (pinst[i].s);
		poutst[i].t = LittleShort (pinst[i].t);
	}

//
// load triangle lists
//
	pintri = (dtriangle_t *) ((byte *)pinmodel + pheader->ofs_tris);
	pouttri = (dtriangle_t *) ((byte *)pheader + pheader->ofs_tris);

	for (i=0 ; i<pheader->num_tris ; i++)
	{
		for (j=0 ; j<3 ; j++)
		{
			pouttri[i].index_xyz[j] = LittleShort (pintri[i].index_xyz[j]);
			pouttri[i].index_st[j] = LittleShort (pintri[i].index_st[j]);
		}
	}

//
// load the frames
//
	for (i=0 ; i<pheader->num_frames ; i++)
	{
		pinframe = (daliasframe_t *) ((byte *)pinmodel 
			+ pheader->ofs_frames + i * pheader->framesize);
		poutframe = (daliasframe_t *) ((byte *)pheader 
			+ pheader->ofs_frames + i * pheader->framesize);

		memcpy (poutframe->name, pinframe->name, sizeof(poutframe->name));
		for (j=0 ; j<3 ; j++)
		{
			poutframe->scale[j] = LittleFloat (pinframe->scale[j]);
			poutframe->translate[j] = LittleFloat (pinframe->translate[j]);
		}
		// verts are all 8 bit, so no swapping needed
		memcpy (poutframe->verts, pinframe->verts, 
			pheader->num_xyz*sizeof(dtrivertx_t));

	}

	mod->type = mod_alias;

	//
	// load the glcmds
	//
	pincmd = (int *) ((byte *)pinmodel + pheader->ofs_glcmds);
	poutcmd = (int *) ((byte *)pheader + pheader->ofs_glcmds);
	for (i=0 ; i<pheader->num_glcmds ; i++)
		poutcmd[i] = q_shared.LittleLong (pincmd[i]);


	// register all skins
	memcpy ((char *)pheader + pheader->ofs_skins, (char *)pinmodel + pheader->ofs_skins,
		pheader->num_skins*MAX_SKINNAME);
	for (i=0 ; i<pheader->num_skins ; i++)
	{
		mod->skins[i] = GL_FindImage ((char *)pheader + pheader->ofs_skins + i*MAX_SKINNAME
			, it_skin);
	}

	mod->mins[0] = -32;
	mod->mins[1] = -32;
	mod->mins[2] = -32;
	mod->maxs[0] = 32;
	mod->maxs[1] = 32;
	mod->maxs[2] = 32;
}

/*
==============================================================================

SPRITE MODELS

==============================================================================
*/

/*
=================
Mod_LoadSpriteModel
=================
"""
def Mod_LoadSpriteModel (mod, buff): # model_t *, void *

	print ("Mod_LoadSpriteModel")
	raise NotImplementedError()
	"""
	dsprite_t	*sprin, *sprout;
	int			i;

	sprin = (dsprite_t *)buffer;
	sprout = Hunk_Alloc (modfilelen);

	sprout->ident = q_shared.LittleLong (sprin->ident);
	sprout->version = q_shared.LittleLong (sprin->version);
	sprout->numframes = q_shared.LittleLong (sprin->numframes);

	if (sprout->version != SPRITE_VERSION)
		ri.Sys_Error (ERR_DROP, "%s has wrong version number (%i should be %i)",
				 mod->name, sprout->version, SPRITE_VERSION);

	if (sprout->numframes > MAX_MD2SKINS)
		ri.Sys_Error (ERR_DROP, "%s has too many frames (%i > %i)",
				 mod->name, sprout->numframes, MAX_MD2SKINS);

	// byte swap everything
	for (i=0 ; i<sprout->numframes ; i++)
	{
		sprout->frames[i].width = q_shared.LittleLong (sprin->frames[i].width);
		sprout->frames[i].height = q_shared.LittleLong (sprin->frames[i].height);
		sprout->frames[i].origin_x = q_shared.LittleLong (sprin->frames[i].origin_x);
		sprout->frames[i].origin_y = q_shared.LittleLong (sprin->frames[i].origin_y);
		memcpy (sprout->frames[i].name, sprin->frames[i].name, MAX_SKINNAME);
		mod->skins[i] = GL_FindImage (sprout->frames[i].name,
			it_sprite);
	}

	mod->type = mod_sprite;
}

//=============================================================================

/*
@@@@@@@@@@@@@@@@@@@@@
R_BeginRegistration

Specifies the model that will be used as the world
@@@@@@@@@@@@@@@@@@@@@
"""
def R_BeginRegistration (model): #char *
	
	global registration_sequence

	#char	fullname[MAX_QPATH];
	#cvar_t	*flushmap;

	registration_sequence+=1
	gl_rmain.r_oldviewcluster = -1		# force markleafs

	fullname = "maps/{}.bsp".format(model)

	# explicitly free the old map if different
	# this guarantees that mod_known[0] is the world map
	flushmap = gl_rmain.ri.Cvar_Get ("flushmap", "0", 0)
	if mod_known[0].name != fullname or flushmap.value:
		Mod_Free (mod_known[0])
	r_worldmodel = Mod_ForName(fullname, True)

	r_viewcluster = -1

"""
@@@@@@@@@@@@@@@@@@@@@
R_RegisterModel

@@@@@@@@@@@@@@@@@@@@@
"""
def R_RegisterModel (name): # char * (returns struct model_s *)
	
	pass
	"""
	model_t	*mod;
	int		i;
	dsprite_t	*sprout;
	dmdl_t		*pheader;

	mod = Mod_ForName (name, false);
	if (mod)
	{
		mod->registration_sequence = registration_sequence;

		// register any images used by the models
		if (mod->type == mod_sprite)
		{
			sprout = (dsprite_t *)mod->extradata;
			for (i=0 ; i<sprout->numframes ; i++)
				mod->skins[i] = GL_FindImage (sprout->frames[i].name, it_sprite);
		}
		else if (mod->type == mod_alias)
		{
			pheader = (dmdl_t *)mod->extradata;
			for (i=0 ; i<pheader->num_skins ; i++)
				mod->skins[i] = GL_FindImage ((char *)pheader + pheader->ofs_skins + i*MAX_SKINNAME, it_skin);
//PGM
			mod->numframes = pheader->num_frames;
//PGM
		}
		else if (mod->type == mod_brush)
		{
			for (i=0 ; i<mod->numtexinfo ; i++)
				mod->texinfo[i].image->registration_sequence = registration_sequence;
		}
	}
	return mod;

	"""

"""
@@@@@@@@@@@@@@@@@@@@@
R_EndRegistration

@@@@@@@@@@@@@@@@@@@@@
"""
def R_EndRegistration ():

	pass
	"""
	int		i;
	model_t	*mod;

	for (i=0, mod=mod_known ; i<mod_numknown ; i++, mod++)
	{
		if (!mod->name[0])
			continue;
		if (mod->registration_sequence != registration_sequence)
		{	// don't need this model
			Mod_Free (mod);
		}
	}

	GL_FreeUnusedImages ();
	"""

"""
//=============================================================================


/*
================
Mod_Free
================
"""
def Mod_Free (mod): # model_t *

	mod.extradata = None
	mod.reset()

"""
================
Mod_FreeAll
================
*/
void Mod_FreeAll (void)
{
	int		i;

	for (i=0 ; i<mod_numknown ; i++)
	{
		if (mod_known[i].extradatasize)
			Mod_Free (&mod_known[i]);
	}
}
"""
