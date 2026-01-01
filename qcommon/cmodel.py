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
import struct
from game import q_shared
from qcommon import qfiles, files, common, cvar, md4
"""
// cmodel.c -- model loading

#include "qcommon.h"
"""
class cnode_t(object):

	def __init__(self):
		self.plane = None #cplane_t *
		self.children = [None, None] # int[2], negative numbers are leafs

class cbrushside_t(object):

	def __init__(self):
		self.plane = None #cplane_t *
		self.surface = None #mapsurface_t *


class cleaf_t(object):

	def __init__(self):
		self.contents: int = None
		self.cluster: int = None
		self.area: int = None
		self.firstleafbrush: int = 0 #unsigned short	
		self.numleafbrushes: int = 0 #unsigned short	


class cbrush_t(object):

	def __init__(self):
		self.contents: int = None
		self.numsides: int = None
		self.firstbrushside: int = None
		self.checkcount: int = None		# to avoid repeated testings


class carea_t(object):

	def __init__(self):
		self.numareaportals: int = None
		self.firstareaportal: int = None
		self.floodnum: int = None			# if two areas have equal floodnums, they are connected
		self.floodvalid: int = None


checkcount: int = None

map_name: str = None # char		[MAX_QPATH];

numbrushsides: int = None
map_brushsides = []
for i in range(qfiles.MAX_MAP_BRUSHSIDES):
	map_brushsides.append(cbrushside_t())

numtexinfo: int = None
map_surfaces = []
for i in range(qfiles.MAX_MAP_TEXINFO):
	map_surfaces.append(q_shared.mapsurface_t())

numplanes: int = None
map_planes = []
for i in range(qfiles.MAX_MAP_PLANES+6): # extra for box hull
	map_planes.append(q_shared.cplane_t())

numnodes: int = None
map_nodes = []
for i in range(qfiles.MAX_MAP_NODES+6): # extra for box hull
	map_nodes.append(cnode_t())

numleafs: int = 1	# allow leaf funcs to be called without a map
map_leafs = []
for i in range(qfiles.MAX_MAP_LEAFS):
	map_leafs.append(cleaf_t())
emptyleaf: int = None
solidleaf: int = None

numleafbrushes: int = None
map_leafbrushes = []
for i in range(qfiles.MAX_MAP_LEAFBRUSHES):
	map_leafbrushes.append(None) # unsigned short

numcmodels: int = None
map_cmodels = []
for i in range(qfiles.MAX_MAP_MODELS):
	map_cmodels.append(q_shared.cmodel_t())

numbrushes: int = None
map_brushes = []
for i in range(qfiles.MAX_MAP_BRUSHES):
	map_brushes.append(cbrush_t())

numvisibility: int = None
map_visibility = None

map_vis = qfiles.dvis_t()

numentitychars: int = None
map_entitystring = None

numareas: int = 1
map_areas = []
for i in range(qfiles.MAX_MAP_AREAS):
	map_areas.append(carea_t())

numareaportals: int = None
map_areaportals = []
for i in range(qfiles.MAX_MAP_AREAPORTALS):
	map_areaportals.append(qfiles.dareaportal_t())

numclusters: int = 1

nullsurface = q_shared.mapsurface_t()

floodvalid = 0

portalopen = [] #qboolean[MAX_MAP_AREAPORTALS];
for i in range(qfiles.MAX_MAP_AREAPORTALS):
	portalopen.append(False)

map_noareas = None # cvar_t	*

#void	CM_InitBoxHull (void)
#void	FloodAreaConnections (void)

c_pointcontents: int = None
c_traces: int = None
c_brush_traces: int = None
last_checksum = None


"""
===============================================================================

					MAP LOADING

===============================================================================
"""
cmod_base = None # byte*
"""
=================
CMod_LoadSubmodels
=================
"""
def CMod_LoadSubmodels (l): #lump_t *

	global numcmodels, map_cmodels, cmod_base
	print ("CMod_LoadSubmodels", l)
	"""
	dmodel_t	*in;
	cmodel_t	*out;
	int			i, j, count;
	"""

	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.dmodel_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.dmodel_t.packed_size()

	if count < 1:
		common.Com_Error (q_shared.ERR_DROP, "Map with no models")
	if count > qfiles.MAX_MAP_MODELS:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many models")

	numcmodels = count
	in_obj = qfiles.dmodel_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.dmodel_t.packed_size()
		in_offset2 = in_offset + qfiles.dmodel_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_cmodels[i]

		for j in range(3):
			# spread the mins / maxs by a pixel
			out.mins[j] = in_obj.mins[j] - 1.0
			out.maxs[j] = in_obj.maxs[j] + 1.0
			out.origin[j] = in_obj.origin[j]
		
		out.headnode = in_obj.headnode

"""
=================
CMod_LoadSurfaces
=================
"""
def CMod_LoadSurfaces (l: qfiles.lump_t):

	global numtexinfo, map_surfaces, cmod_base
	print ("CMod_LoadSurfaces", l)
	"""
	texinfo_t	*in;
	mapsurface_t	*out;
	int			i, count;
	"""

	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.texinfo_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.texinfo_t.packed_size()
	if count < 1:
		common.Com_Error (q_shared.ERR_DROP, "Map with no surfaces")
	if count > qfiles.MAX_MAP_TEXINFO:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many surfaces")

	numtexinfo = count
	in_obj = qfiles.texinfo_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.texinfo_t.packed_size()
		in_offset2 = in_offset + qfiles.texinfo_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_surfaces[i]

		out.c.name = in_obj.texture
		out.rname = in_obj.texture
		out.c.flags = in_obj.flags
		out.c.value = in_obj.value

"""
=================
CMod_LoadNodes

=================
"""
def CMod_LoadNodes (l): #lump_t *
	
	global cmod_base, map_nodes, numnodes

	print ("CMod_LoadNodes", l)
	"""
	dnode_t		*in;
	int			child;
	cnode_t		*out;
	int			i, j, count;
	"""
	
	#in = (void *)(cmod_base + l->fileofs);
	in_offset = 0
	if l.filelen % qfiles.dnode_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.dnode_t.packed_size()

	if count < 1:
		common.Com_Error (q_shared.ERR_DROP, "Map has no nodes")
	if count > qfiles.MAX_MAP_NODES:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many nodes")

	in_obj = qfiles.dnode_t()

	#out = map_nodes

	numnodes = count

	for i in range(count):

		in_offset = l.fileofs + i * qfiles.dnode_t.packed_size()
		in_offset2 = in_offset + qfiles.dnode_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_nodes[i]

		out.plane = map_planes[in_obj.planenum]
		out.children[0] = in_obj.children[0]
		out.children[1] = in_obj.children[1]

"""
=================
CMod_LoadBrushes

=================
"""
def CMod_LoadBrushes (l): #lump_t *

	global map_brushes, numbrushes, cmod_base
	print ("CMod_LoadBrushes", l)
	"""
	dbrush_t	*in;
	cbrush_t	*out;
	int			i, count;
	"""
	
	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.dbrush_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.dbrush_t.packed_size()

	if count > qfiles.MAX_MAP_BRUSHES:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many brushes")

	out = map_brushes

	numbrushes = count
	in_obj = qfiles.dbrush_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.dbrush_t.packed_size()
		in_offset2 = in_offset + qfiles.dbrush_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_brushes[i]

		out.firstbrushside = in_obj.firstside
		out.numsides = in_obj.numsides
		out.contents = in_obj.contents
	



"""
=================
CMod_LoadLeafs
=================
"""
def CMod_LoadLeafs (l): #lump_t *

	global numclusters, map_leafs, cmod_base
	print ("CMod_LoadLeafs", l)
	"""
	int			i;
	cleaf_t		*out;
	dleaf_t 	*in;
	int			count;
	"""
	
	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.dleaf_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.dleaf_t.packed_size()

	if count < 1:
		common.Com_Error (q_shared.ERR_DROP, "Map with no leafs")
	# need to save space for box planes
	if count > qfiles.MAX_MAP_PLANES:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many planes")

	out = map_leafs
	numleafs = count
	numclusters = 0
	in_obj = qfiles.dleaf_t()

	for i in range(count):

		in_offset = l.fileofs + i * qfiles.dleaf_t.packed_size()
		in_offset2 = in_offset + qfiles.dleaf_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_leafs[i]
		out.contents = in_obj.contents
		out.cluster = in_obj.cluster
		out.area = in_obj.area
		out.firstleafbrush = in_obj.firstleafbrush
		out.numleafbrushes = in_obj.numleafbrushes

		if out.cluster >= numclusters:
			numclusters = out.cluster + 1

	if map_leafs[0].contents != qfiles.CONTENTS_SOLID:
		common.Com_Error (q_shared.ERR_DROP, "Map leaf 0 is not CONTENTS_SOLID")
	solidleaf = 0
	emptyleaf = -1
	for i in range(1, numleafs):
	
		if not map_leafs[i].contents:
		
			emptyleaf = i
			break
		
	if emptyleaf == -1:
		common.Com_Error (q_shared.ERR_DROP, "Map does not have an empty leaf")
	
"""
=================
CMod_LoadPlanes
=================
"""
def CMod_LoadPlanes (l): #lump_t *

	global map_planes, numplanes, cmod_base
	print ("CMod_LoadPlanes", l)
	"""
	int			i, j;
	cplane_t	*out;
	dplane_t 	*in;
	int			count;
	int			bits;
	"""
	
	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.dplane_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size");
	count = l.filelen // qfiles.dplane_t.packed_size()

	
	if count < 1:
		common.Com_Error (q_shared.ERR_DROP, "Map with no planes")
	# need to save space for box planes
	if count > qfiles.MAX_MAP_PLANES:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many planes")

	numplanes = count
	in_obj = qfiles.dplane_t()

	for i in range(count):
	
		in_offset = l.fileofs + i * qfiles.dplane_t.packed_size()
		in_offset2 = in_offset + qfiles.dplane_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_planes[i]
		bits = 0
		for j in range(3):
		
			out.normal[j] = in_obj.normal[j]
			if out.normal[j] < 0:
				bits |= 1<<j
		
		out.dist = in_obj.dist
		out.type = in_obj.type
		out.signbits = bits
	

"""
=================
CMod_LoadLeafBrushes
=================
"""
def CMod_LoadLeafBrushes (l): #lump_t *

	global map_leafbrushes, numleafbrushes, cmod_base
	print ("CMod_LoadLeafBrushes", l)
	"""
	int			i;
	unsigned short	*out;
	unsigned short 	*in;
	int			count;
	"""
	
	#in = (void *)(cmod_base + l->fileofs)
	if l.filelen % 2:
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // 2

	if count < 1:
		common.Com_Error (q_shared.ERR_DROP, "Map with no planes")
	# need to save space for box planes
	if count > qfiles.MAX_MAP_LEAFBRUSHES:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many leafbrushes")

	out = map_leafbrushes
	numleafbrushes = count

	for i in range(count):
		in_offset = l.fileofs + i * 2
		in_offset2 = in_offset + 2

		map_leafbrushes[i] = q_shared.LittleShort (cmod_base[in_offset:in_offset2])


"""
=================
CMod_LoadBrushSides
=================
"""
def CMod_LoadBrushSides (l): #lump_t *

	global cmod_base, map_brushsides, numbrushsides, map_planes, map_surfaces, numtexinfo
	print ("CMod_LoadBrushSides", l)
	"""
	int			i, j;
	cbrushside_t	*out;
	dbrushside_t 	*in;
	int			count;
	int			num;
	"""

	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.dbrushside_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.dbrushside_t.packed_size()

	# need to save space for box planes
	if count > qfiles.MAX_MAP_BRUSHSIDES:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many planes")

	#out = map_brushsides
	numbrushsides = count
	in_obj = qfiles.dbrushside_t()

	for i in range(count):

		in_offset = l.fileofs + i * qfiles.dbrushside_t.packed_size()
		in_offset2 = in_offset + qfiles.dbrushside_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])
	
		out = map_brushsides[i]

		num = in_obj.planenum
		out.plane = map_planes[num]
		j = in_obj.texinfo
		if j >= numtexinfo:
			common.Com_Error (q_shared.ERR_DROP, "Bad brushside texinfo")
		out.surface = map_surfaces[j]
	


"""
=================
CMod_LoadAreas
=================
"""

def CMod_LoadAreas (l): #lump_t *

	global numareas, map_areas, map_areas
	print ("CMod_LoadAreas", l)
	"""
	int			i;
	carea_t		*out;
	darea_t 	*in;
	int			count;
	"""

	#in = (void *)(cmod_base + l->fileofs);
	if l.filelen % qfiles.darea_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.darea_t.packed_size()

	if count > qfiles.MAX_MAP_AREAS:
		common.Com_Error (q_shared.ERR_DROP, "Map has too many areas")

	numareas = count
	in_obj = qfiles.darea_t()

	for i in range(count):

		in_offset = l.fileofs + i * qfiles.darea_t.packed_size()
		in_offset2 = in_offset + qfiles.darea_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_areas[i]

		out.numareaportals = in_obj.numareaportals
		out.firstareaportal = in_obj.firstareaportal
		out.floodvalid = 0
		out.floodnum = 0

"""
=================
CMod_LoadAreaPortals
=================
"""
def CMod_LoadAreaPortals (l): #lump_t *

	global numareaportals, map_areaportals, cmod_base
	print ("CMod_LoadAreaPortals", l)
	"""
	int			i;
	dareaportal_t		*out;
	dareaportal_t 	*in;
	int			count;
	"""

	#in = (void *)(cmod_base + l->fileofs)
	if l.filelen % qfiles.dareaportal_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "MOD_LoadBmodel: funny lump size")
	count = l.filelen // qfiles.dareaportal_t.packed_size()

	if count > qfiles.dareaportal_t.packed_size():
		common.Com_Error (q_shared.ERR_DROP, "Map has too many areas")

	numareaportals = count
	in_obj = qfiles.dareaportal_t()

	for i in range(count):

		in_offset = l.fileofs + i * qfiles.dareaportal_t.packed_size()
		in_offset2 = in_offset + qfiles.dareaportal_t.packed_size()
		in_obj.load(cmod_base[in_offset:in_offset2])

		out = map_areaportals[i]
	
		out.portalnum = in_obj.portalnum
		out.otherarea = in_obj.otherarea
	

"""
=================
CMod_LoadVisibility
=================
"""
def CMod_LoadVisibility (l): #lump_t *

	global map_vis, map_visibility, numvisibility, cmod_base
	print ("CMod_LoadVisibility", l)

	numvisibility = l.filelen
	if l.filelen > qfiles.MAX_MAP_VISIBILITY:
		common.Com_Error (q_shared.ERR_DROP, "Map has too large visibility lump")

	map_visibility = cmod_base[l.fileofs:l.fileofs+l.filelen]

	map_vis.load(cmod_base[l.fileofs:l.fileofs+qfiles.dvis_t.packed_size()])

"""
=================
CMod_LoadEntityString
=================
"""
def CMod_LoadEntityString (l): #lump_t *

	global map_entitystring, numentitychars
	print ("CMod_LoadEntityString", l)
	
	numentitychars = l.filelen
	if l.filelen > qfiles.MAX_MAP_ENTSTRING:
		common.Com_Error (q_shared.ERR_DROP, "Map has too large entity lump")

	map_entitystring = cmod_base[l.fileofs: l.fileofs+l.filelen].decode('ascii')
	
"""
==================
CM_LoadMap

Loads in the map and all submodels
==================
"""
def CM_LoadMap (name, clientload): #char *, qboolean (returns cmodel_t *, unsigned *)

	global last_checksum
	global numplanes, numnodes, numleafs, numcmodels, numvisibility, numentitychars, map_entitystring, map_name
	global numclusters, numareas
	global map_noareas, cmod_base
	global portalopen

	print ("CM_LoadMap", name, clientload)

	#return q_shared.cmodel_t(), 0
	"""
	unsigned		*buf;
	int				i;
	dheader_t		header;
	int				length;
	static unsigned	last_checksum;
	"""
	checksum = 0 #unsigned (output)

	map_noareas = cvar.Cvar_Get ("map_noareas", "0", 0)

	if map_name == name and (clientload or int(cvar.Cvar_VariableValue ("flushmap"))):
	
		checksum = last_checksum
		if not clientload:
		
			for i in range(len(portalopen)):
				portalopen[i] = False
			FloodAreaConnections ()
		
		return map_cmodels[0], checksum # still have the right version
	
	# free old stuff
	numplanes = 0
	numnodes = 0
	numleafs = 0
	numcmodels = 0
	numvisibility = 0
	numentitychars = 0
	map_entitystring = None
	map_name = None

	if name is None or len(name) == 0:

		numleafs = 1
		numclusters = 1
		numareas = 1
		checksum = 0

		return map_cmodels[0], checksum # cinematic servers won't have anything at all

	#
	# load the file
	#
	length, buf = files.FS_LoadFile (name)
	if buf is None:
		common.common.Com_Error (q_shared.ERR_DROP, "Couldn't load {}".format(name))

	last_checksum = q_shared.LittleLong (md4.Com_BlockChecksum (buf))
	checksum = last_checksum

	header = qfiles.dheader_t()
	header.parse(buf)

	if header.version != qfiles.BSPVERSION:
		common.common.Com_Error (q_shared.ERR_DROP, "CMod_LoadBrushModel: {} has wrong version number ({} should be {})".format( \
			name, header.version, qfiles.BSPVERSION))

	cmod_base = buf

	# load into heap
	CMod_LoadSurfaces (header.lumps[qfiles.LUMP_TEXINFO])
	CMod_LoadLeafs (header.lumps[qfiles.LUMP_LEAFS])
	CMod_LoadLeafBrushes (header.lumps[qfiles.LUMP_LEAFBRUSHES])
	CMod_LoadPlanes (header.lumps[qfiles.LUMP_PLANES])
	CMod_LoadBrushes (header.lumps[qfiles.LUMP_BRUSHES])
	CMod_LoadBrushSides (header.lumps[qfiles.LUMP_BRUSHSIDES])
	CMod_LoadSubmodels (header.lumps[qfiles.LUMP_MODELS])
	CMod_LoadNodes (header.lumps[qfiles.LUMP_NODES])
	CMod_LoadAreas (header.lumps[qfiles.LUMP_AREAS])
	CMod_LoadAreaPortals (header.lumps[qfiles.LUMP_AREAPORTALS])
	CMod_LoadVisibility (header.lumps[qfiles.LUMP_VISIBILITY])
	CMod_LoadEntityString (header.lumps[qfiles.LUMP_ENTITIES])

	del buf, cmod_base

	CM_InitBoxHull ()

	for i in range(len(portalopen)):
		portalopen[i] = False
	FloodAreaConnections ()

	map_name = name

	return map_cmodels[0], checksum


"""
==================
CM_InlineModel
==================
"""
def CM_InlineModel (name): # (cmodel_t	*)

	print ("CM_InlineModel")
	"""
	int		num;

	if (!name || name[0] != '*')
		common.Com_Error (q_shared.ERR_DROP, "CM_InlineModel: bad name");
	num = atoi (name+1);
	if (num < 1 || num >= numcmodels)
		common.Com_Error (q_shared.ERR_DROP, "CM_InlineModel: bad number");

	return &map_cmodels[num];
}

"""
def CM_NumClusters ():

	return numclusters


def CM_NumInlineModels ():

	return numcmodels


def CM_EntityString ():

	return map_entitystring

"""
int		CM_LeafContents (int leafnum)
{
	if (leafnum < 0 || leafnum >= numleafs)
		common.Com_Error (q_shared.ERR_DROP, "CM_LeafContents: bad number");
	return map_leafs[leafnum].contents;
}

int		CM_LeafCluster (int leafnum)
{
	if (leafnum < 0 || leafnum >= numleafs)
		common.Com_Error (q_shared.ERR_DROP, "CM_LeafCluster: bad number");
	return map_leafs[leafnum].cluster;
}

int		CM_LeafArea (int leafnum)
{
	if (leafnum < 0 || leafnum >= numleafs)
		common.Com_Error (q_shared.ERR_DROP, "CM_LeafArea: bad number");
	return map_leafs[leafnum].area;
}

//=======================================================================

"""
box_planes = None # cplane_t*
box_headnode = None # int			
box_brush = None #cbrush_t *
box_leaf = None # cleaf_t *

"""
===================
CM_InitBoxHull

Set up the planes and nodes so that the six floats of a bounding box
can just be stored out and get a proper clipping hull structure.
===================
"""
def CM_InitBoxHull ():

	global numnodes, box_headnode, box_planes, map_planes

	"""
	int			i;
	int			side;
	cnode_t		*c;
	cplane_t	*p;
	cbrushside_t	*s;
	"""

	box_headnode = numnodes
	box_planes = map_planes[numplanes]

	"""
	if (numnodes+6 > MAX_MAP_NODES
		|| numbrushes+1 > MAX_MAP_BRUSHES
		|| numleafbrushes+1 > MAX_MAP_LEAFBRUSHES
		|| numbrushsides+6 > MAX_MAP_BRUSHSIDES
		|| numplanes+12 > MAX_MAP_PLANES)
		common.Com_Error (q_shared.ERR_DROP, "Not enough room for box tree");

	box_brush = &map_brushes[numbrushes];
	box_brush->numsides = 6;
	box_brush->firstbrushside = numbrushsides;
	box_brush->contents = CONTENTS_MONSTER;

	box_leaf = &map_leafs[numleafs];
	box_leaf->contents = CONTENTS_MONSTER;
	box_leaf->firstleafbrush = numleafbrushes;
	box_leaf->numleafbrushes = 1;

	map_leafbrushes[numleafbrushes] = numbrushes;

	for (i=0 ; i<6 ; i++)
	{
		side = i&1;

		// brush sides
		s = &map_brushsides[numbrushsides+i];
		s->plane = 	map_planes + (numplanes+i*2+side);
		s->surface = &nullsurface;

		// nodes
		c = &map_nodes[box_headnode+i];
		c->plane = map_planes + (numplanes+i*2);
		c->children[side] = -1 - emptyleaf;
		if (i != 5)
			c->children[side^1] = box_headnode+i + 1;
		else
			c->children[side^1] = -1 - numleafs;

		// planes
		p = &box_planes[i*2];
		p->type = i>>1;
		p->signbits = 0;
		VectorClear (p->normal);
		p->normal[i>>1] = 1;

		p = &box_planes[i*2+1];
		p->type = 3 + (i>>1);
		p->signbits = 0;
		VectorClear (p->normal);
		p->normal[i>>1] = -1;
	}	
}


/*
===================
CM_HeadnodeForBox

To keep everything totally uniform, bounding boxes are turned into small
BSP trees instead of being compared directly.
===================
*/
int	CM_HeadnodeForBox (vec3_t mins, vec3_t maxs)
{
	box_planes[0].dist = maxs[0];
	box_planes[1].dist = -maxs[0];
	box_planes[2].dist = mins[0];
	box_planes[3].dist = -mins[0];
	box_planes[4].dist = maxs[1];
	box_planes[5].dist = -maxs[1];
	box_planes[6].dist = mins[1];
	box_planes[7].dist = -mins[1];
	box_planes[8].dist = maxs[2];
	box_planes[9].dist = -maxs[2];
	box_planes[10].dist = mins[2];
	box_planes[11].dist = -mins[2];

	return box_headnode;
}


/*
==================
CM_PointLeafnum_r

==================
*/
int CM_PointLeafnum_r (vec3_t p, int num)
{
	float		d;
	cnode_t		*node;
	cplane_t	*plane;

	while (num >= 0)
	{
		node = map_nodes + num;
		plane = node->plane;
		
		if (plane->type < 3)
			d = p[plane->type] - plane->dist;
		else
			d = DotProduct (plane->normal, p) - plane->dist;
		if (d < 0)
			num = node->children[1];
		else
			num = node->children[0];
	}

	c_pointcontents++;		// optimize counter

	return -1 - num;
}

int CM_PointLeafnum (vec3_t p)
{
	if (!numplanes)
		return 0;		// sound may call this without map loaded
	return CM_PointLeafnum_r (p, 0);
}



/*
=============
CM_BoxLeafnums

Fills in a list of all the leafs touched
=============
*/
int		leaf_count, leaf_maxcount;
int		*leaf_list;
float	*leaf_mins, *leaf_maxs;
int		leaf_topnode;

void CM_BoxLeafnums_r (int nodenum)
{
	cplane_t	*plane;
	cnode_t		*node;
	int		s;

	while (1)
	{
		if (nodenum < 0)
		{
			if (leaf_count >= leaf_maxcount)
			{
//				Com_Printf ("CM_BoxLeafnums_r: overflow\n");
				return;
			}
			leaf_list[leaf_count++] = -1 - nodenum;
			return;
		}
	
		node = &map_nodes[nodenum];
		plane = node->plane;
//		s = BoxOnPlaneSide (leaf_mins, leaf_maxs, plane);
		s = BOX_ON_PLANE_SIDE(leaf_mins, leaf_maxs, plane);
		if (s == 1)
			nodenum = node->children[0];
		else if (s == 2)
			nodenum = node->children[1];
		else
		{	// go down both
			if (leaf_topnode == -1)
				leaf_topnode = nodenum;
			CM_BoxLeafnums_r (node->children[0]);
			nodenum = node->children[1];
		}

	}
}

int	CM_BoxLeafnums_headnode (vec3_t mins, vec3_t maxs, int *list, int listsize, int headnode, int *topnode)
{
	leaf_list = list;
	leaf_count = 0;
	leaf_maxcount = listsize;
	leaf_mins = mins;
	leaf_maxs = maxs;

	leaf_topnode = -1;

	CM_BoxLeafnums_r (headnode);

	if (topnode)
		*topnode = leaf_topnode;

	return leaf_count;
}

int	CM_BoxLeafnums (vec3_t mins, vec3_t maxs, int *list, int listsize, int *topnode)
{
	return CM_BoxLeafnums_headnode (mins, maxs, list,
		listsize, map_cmodels[0].headnode, topnode);
}



/*
==================
CM_PointContents

==================
*/
int CM_PointContents (vec3_t p, int headnode)
{
	int		l;

	if (!numnodes)	// map not loaded
		return 0;

	l = CM_PointLeafnum_r (p, headnode);

	return map_leafs[l].contents;
}

/*
==================
CM_TransformedPointContents

Handles offseting and rotation of the end points for moving and
rotating entities
==================
*/
int	CM_TransformedPointContents (vec3_t p, int headnode, vec3_t origin, vec3_t angles)
{
	vec3_t		p_l;
	vec3_t		temp;
	vec3_t		forward, right, up;
	int			l;

	// subtract origin offset
	VectorSubtract (p, origin, p_l);

	// rotate start and end into the models frame of reference
	if (headnode != box_headnode && 
	(angles[0] || angles[1] || angles[2]) )
	{
		AngleVectors (angles, forward, right, up);

		VectorCopy (p_l, temp);
		p_l[0] = DotProduct (temp, forward);
		p_l[1] = -DotProduct (temp, right);
		p_l[2] = DotProduct (temp, up);
	}

	l = CM_PointLeafnum_r (p_l, headnode);

	return map_leafs[l].contents;
}


/*
===============================================================================

BOX TRACING

===============================================================================
*/

// 1/32 epsilon to keep floating point happy
#define	DIST_EPSILON	(0.03125)

vec3_t	trace_start, trace_end;
vec3_t	trace_mins, trace_maxs;
vec3_t	trace_extents;

trace_t	trace_trace;
int		trace_contents;
qboolean	trace_ispoint;		// optimized case

/*
================
CM_ClipBoxToBrush
================
*/
void CM_ClipBoxToBrush (vec3_t mins, vec3_t maxs, vec3_t p1, vec3_t p2,
					  trace_t *trace, cbrush_t *brush)
{
	int			i, j;
	cplane_t	*plane, *clipplane;
	float		dist;
	float		enterfrac, leavefrac;
	vec3_t		ofs;
	float		d1, d2;
	qboolean	getout, startout;
	float		f;
	cbrushside_t	*side, *leadside;

	enterfrac = -1;
	leavefrac = 1;
	clipplane = NULL;

	if (!brush->numsides)
		return;

	c_brush_traces++;

	getout = false;
	startout = false;
	leadside = NULL;

	for (i=0 ; i<brush->numsides ; i++)
	{
		side = &map_brushsides[brush->firstbrushside+i];
		plane = side->plane;

		// FIXME: special case for axial

		if (!trace_ispoint)
		{	// general box case

			// push the plane out apropriately for mins/maxs

			// FIXME: use signbits into 8 way lookup for each mins/maxs
			for (j=0 ; j<3 ; j++)
			{
				if (plane->normal[j] < 0)
					ofs[j] = maxs[j];
				else
					ofs[j] = mins[j];
			}
			dist = DotProduct (ofs, plane->normal);
			dist = plane->dist - dist;
		}
		else
		{	// special point case
			dist = plane->dist;
		}

		d1 = DotProduct (p1, plane->normal) - dist;
		d2 = DotProduct (p2, plane->normal) - dist;

		if (d2 > 0)
			getout = true;	// endpoint is not in solid
		if (d1 > 0)
			startout = true;

		// if completely in front of face, no intersection
		if (d1 > 0 && d2 >= d1)
			return;

		if (d1 <= 0 && d2 <= 0)
			continue;

		// crosses face
		if (d1 > d2)
		{	// enter
			f = (d1-DIST_EPSILON) / (d1-d2);
			if (f > enterfrac)
			{
				enterfrac = f;
				clipplane = plane;
				leadside = side;
			}
		}
		else
		{	// leave
			f = (d1+DIST_EPSILON) / (d1-d2);
			if (f < leavefrac)
				leavefrac = f;
		}
	}

	if (!startout)
	{	// original point was inside brush
		trace->startsolid = true;
		if (!getout)
			trace->allsolid = true;
		return;
	}
	if (enterfrac < leavefrac)
	{
		if (enterfrac > -1 && enterfrac < trace->fraction)
		{
			if (enterfrac < 0)
				enterfrac = 0;
			trace->fraction = enterfrac;
			trace->plane = *clipplane;
			trace->surface = &(leadside->surface->c);
			trace->contents = brush->contents;
		}
	}
}

/*
================
CM_TestBoxInBrush
================
*/
void CM_TestBoxInBrush (vec3_t mins, vec3_t maxs, vec3_t p1,
					  trace_t *trace, cbrush_t *brush)
{
	int			i, j;
	cplane_t	*plane;
	float		dist;
	vec3_t		ofs;
	float		d1;
	cbrushside_t	*side;

	if (!brush->numsides)
		return;

	for (i=0 ; i<brush->numsides ; i++)
	{
		side = &map_brushsides[brush->firstbrushside+i];
		plane = side->plane;

		// FIXME: special case for axial

		// general box case

		// push the plane out apropriately for mins/maxs

		// FIXME: use signbits into 8 way lookup for each mins/maxs
		for (j=0 ; j<3 ; j++)
		{
			if (plane->normal[j] < 0)
				ofs[j] = maxs[j];
			else
				ofs[j] = mins[j];
		}
		dist = DotProduct (ofs, plane->normal);
		dist = plane->dist - dist;

		d1 = DotProduct (p1, plane->normal) - dist;

		// if completely in front of face, no intersection
		if (d1 > 0)
			return;

	}

	// inside this brush
	trace->startsolid = trace->allsolid = true;
	trace->fraction = 0;
	trace->contents = brush->contents;
}


/*
================
CM_TraceToLeaf
================
*/
void CM_TraceToLeaf (int leafnum)
{
	int			k;
	int			brushnum;
	cleaf_t		*leaf;
	cbrush_t	*b;

	leaf = &map_leafs[leafnum];
	if ( !(leaf->contents & trace_contents))
		return;
	// trace line against all brushes in the leaf
	for (k=0 ; k<leaf->numleafbrushes ; k++)
	{
		brushnum = map_leafbrushes[leaf->firstleafbrush+k];
		b = &map_brushes[brushnum];
		if (b->checkcount == checkcount)
			continue;	// already checked this brush in another leaf
		b->checkcount = checkcount;

		if ( !(b->contents & trace_contents))
			continue;
		CM_ClipBoxToBrush (trace_mins, trace_maxs, trace_start, trace_end, &trace_trace, b);
		if (!trace_trace.fraction)
			return;
	}

}


/*
================
CM_TestInLeaf
================
*/
void CM_TestInLeaf (int leafnum)
{
	int			k;
	int			brushnum;
	cleaf_t		*leaf;
	cbrush_t	*b;

	leaf = &map_leafs[leafnum];
	if ( !(leaf->contents & trace_contents))
		return;
	// trace line against all brushes in the leaf
	for (k=0 ; k<leaf->numleafbrushes ; k++)
	{
		brushnum = map_leafbrushes[leaf->firstleafbrush+k];
		b = &map_brushes[brushnum];
		if (b->checkcount == checkcount)
			continue;	// already checked this brush in another leaf
		b->checkcount = checkcount;

		if ( !(b->contents & trace_contents))
			continue;
		CM_TestBoxInBrush (trace_mins, trace_maxs, trace_start, &trace_trace, b);
		if (!trace_trace.fraction)
			return;
	}

}


/*
==================
CM_RecursiveHullCheck

==================
*/
void CM_RecursiveHullCheck (int num, float p1f, float p2f, vec3_t p1, vec3_t p2)
{
	cnode_t		*node;
	cplane_t	*plane;
	float		t1, t2, offset;
	float		frac, frac2;
	float		idist;
	int			i;
	vec3_t		mid;
	int			side;
	float		midf;

	if (trace_trace.fraction <= p1f)
		return;		// already hit something nearer

	// if < 0, we are in a leaf node
	if (num < 0)
	{
		CM_TraceToLeaf (-1-num);
		return;
	}

	//
	// find the point distances to the seperating plane
	// and the offset for the size of the box
	//
	node = map_nodes + num;
	plane = node->plane;

	if (plane->type < 3)
	{
		t1 = p1[plane->type] - plane->dist;
		t2 = p2[plane->type] - plane->dist;
		offset = trace_extents[plane->type];
	}
	else
	{
		t1 = DotProduct (plane->normal, p1) - plane->dist;
		t2 = DotProduct (plane->normal, p2) - plane->dist;
		if (trace_ispoint)
			offset = 0;
		else
			offset = fabs(trace_extents[0]*plane->normal[0]) +
				fabs(trace_extents[1]*plane->normal[1]) +
				fabs(trace_extents[2]*plane->normal[2]);
	}


#if 0
CM_RecursiveHullCheck (node->children[0], p1f, p2f, p1, p2);
CM_RecursiveHullCheck (node->children[1], p1f, p2f, p1, p2);
return;
#endif

	// see which sides we need to consider
	if (t1 >= offset && t2 >= offset)
	{
		CM_RecursiveHullCheck (node->children[0], p1f, p2f, p1, p2);
		return;
	}
	if (t1 < -offset && t2 < -offset)
	{
		CM_RecursiveHullCheck (node->children[1], p1f, p2f, p1, p2);
		return;
	}

	// put the crosspoint DIST_EPSILON pixels on the near side
	if (t1 < t2)
	{
		idist = 1.0/(t1-t2);
		side = 1;
		frac2 = (t1 + offset + DIST_EPSILON)*idist;
		frac = (t1 - offset + DIST_EPSILON)*idist;
	}
	else if (t1 > t2)
	{
		idist = 1.0/(t1-t2);
		side = 0;
		frac2 = (t1 - offset - DIST_EPSILON)*idist;
		frac = (t1 + offset + DIST_EPSILON)*idist;
	}
	else
	{
		side = 0;
		frac = 1;
		frac2 = 0;
	}

	// move up to the node
	if (frac < 0)
		frac = 0;
	if (frac > 1)
		frac = 1;
		
	midf = p1f + (p2f - p1f)*frac;
	for (i=0 ; i<3 ; i++)
		mid[i] = p1[i] + frac*(p2[i] - p1[i]);

	CM_RecursiveHullCheck (node->children[side], p1f, midf, p1, mid);


	// go past the node
	if (frac2 < 0)
		frac2 = 0;
	if (frac2 > 1)
		frac2 = 1;
		
	midf = p1f + (p2f - p1f)*frac2;
	for (i=0 ; i<3 ; i++)
		mid[i] = p1[i] + frac2*(p2[i] - p1[i]);

	CM_RecursiveHullCheck (node->children[side^1], midf, p2f, mid, p2);
}



//======================================================================

/*
==================
CM_BoxTrace
==================
*/
trace_t		CM_BoxTrace (vec3_t start, vec3_t end,
						  vec3_t mins, vec3_t maxs,
						  int headnode, int brushmask)
{
	int		i;

	checkcount++;		// for multi-check avoidance

	c_traces++;			// for statistics, may be zeroed

	// fill in a default trace
	memset (&trace_trace, 0, sizeof(trace_trace));
	trace_trace.fraction = 1;
	trace_trace.surface = &(nullsurface.c);

	if (!numnodes)	// map not loaded
		return trace_trace;

	trace_contents = brushmask;
	VectorCopy (start, trace_start);
	VectorCopy (end, trace_end);
	VectorCopy (mins, trace_mins);
	VectorCopy (maxs, trace_maxs);

	//
	// check for position test special case
	//
	if (start[0] == end[0] && start[1] == end[1] && start[2] == end[2])
	{
		int		leafs[1024];
		int		i, numleafs;
		vec3_t	c1, c2;
		int		topnode;

		VectorAdd (start, mins, c1);
		VectorAdd (start, maxs, c2);
		for (i=0 ; i<3 ; i++)
		{
			c1[i] -= 1;
			c2[i] += 1;
		}

		numleafs = CM_BoxLeafnums_headnode (c1, c2, leafs, 1024, headnode, &topnode);
		for (i=0 ; i<numleafs ; i++)
		{
			CM_TestInLeaf (leafs[i]);
			if (trace_trace.allsolid)
				break;
		}
		VectorCopy (start, trace_trace.endpos);
		return trace_trace;
	}

	//
	// check for point special case
	//
	if (mins[0] == 0 && mins[1] == 0 && mins[2] == 0
		&& maxs[0] == 0 && maxs[1] == 0 && maxs[2] == 0)
	{
		trace_ispoint = true;
		VectorClear (trace_extents);
	}
	else
	{
		trace_ispoint = false;
		trace_extents[0] = -mins[0] > maxs[0] ? -mins[0] : maxs[0];
		trace_extents[1] = -mins[1] > maxs[1] ? -mins[1] : maxs[1];
		trace_extents[2] = -mins[2] > maxs[2] ? -mins[2] : maxs[2];
	}

	//
	// general sweeping through world
	//
	CM_RecursiveHullCheck (headnode, 0, 1, start, end);

	if (trace_trace.fraction == 1)
	{
		VectorCopy (end, trace_trace.endpos);
	}
	else
	{
		for (i=0 ; i<3 ; i++)
			trace_trace.endpos[i] = start[i] + trace_trace.fraction * (end[i] - start[i]);
	}
	return trace_trace;
}


/*
==================
CM_TransformedBoxTrace

Handles offseting and rotation of the end points for moving and
rotating entities
==================
*/
#ifdef _WIN32
#pragma optimize( "", off )
#endif


trace_t		CM_TransformedBoxTrace (vec3_t start, vec3_t end,
						  vec3_t mins, vec3_t maxs,
						  int headnode, int brushmask,
						  vec3_t origin, vec3_t angles)
{
	trace_t		trace;
	vec3_t		start_l, end_l;
	vec3_t		a;
	vec3_t		forward, right, up;
	vec3_t		temp;
	qboolean	rotated;

	// subtract origin offset
	VectorSubtract (start, origin, start_l);
	VectorSubtract (end, origin, end_l);

	// rotate start and end into the models frame of reference
	if (headnode != box_headnode && 
	(angles[0] || angles[1] || angles[2]) )
		rotated = true;
	else
		rotated = false;

	if (rotated)
	{
		AngleVectors (angles, forward, right, up);

		VectorCopy (start_l, temp);
		start_l[0] = DotProduct (temp, forward);
		start_l[1] = -DotProduct (temp, right);
		start_l[2] = DotProduct (temp, up);

		VectorCopy (end_l, temp);
		end_l[0] = DotProduct (temp, forward);
		end_l[1] = -DotProduct (temp, right);
		end_l[2] = DotProduct (temp, up);
	}

	// sweep the box through the model
	trace = CM_BoxTrace (start_l, end_l, mins, maxs, headnode, brushmask);

	if (rotated && trace.fraction != 1.0)
	{
		// FIXME: figure out how to do this with existing angles
		VectorNegate (angles, a);
		AngleVectors (a, forward, right, up);

		VectorCopy (trace.plane.normal, temp);
		trace.plane.normal[0] = DotProduct (temp, forward);
		trace.plane.normal[1] = -DotProduct (temp, right);
		trace.plane.normal[2] = DotProduct (temp, up);
	}

	trace.endpos[0] = start[0] + trace.fraction * (end[0] - start[0]);
	trace.endpos[1] = start[1] + trace.fraction * (end[1] - start[1]);
	trace.endpos[2] = start[2] + trace.fraction * (end[2] - start[2]);

	return trace;
}

#ifdef _WIN32
#pragma optimize( "", on )
#endif



/*
===============================================================================

PVS / PHS

===============================================================================
*/

/*
===================
CM_DecompressVis
===================
*/
void CM_DecompressVis (byte *in, byte *out)
{
	int		c;
	byte	*out_p;
	int		row;

	row = (numclusters+7)>>3;	
	out_p = out;

	if (!in || !numvisibility)
	{	// no vis info, so make all visible
		while (row)
		{
			*out_p++ = 0xff;
			row--;
		}
		return;		
	}

	do
	{
		if (*in)
		{
			*out_p++ = *in++;
			continue;
		}
	
		c = in[1];
		in += 2;
		if ((out_p - out) + c > row)
		{
			c = row - (out_p - out);
			Com_DPrintf ("warning: Vis decompression overrun\n");
		}
		while (c)
		{
			*out_p++ = 0;
			c--;
		}
	} while (out_p - out < row);
}

byte	pvsrow[MAX_MAP_LEAFS/8];
byte	phsrow[MAX_MAP_LEAFS/8];

byte	*CM_ClusterPVS (int cluster)
{
	if (cluster == -1)
		memset (pvsrow, 0, (numclusters+7)>>3);
	else
		CM_DecompressVis (map_visibility + map_vis->bitofs[cluster][DVIS_PVS], pvsrow);
	return pvsrow;
}

byte	*CM_ClusterPHS (int cluster)
{
	if (cluster == -1)
		memset (phsrow, 0, (numclusters+7)>>3);
	else
		CM_DecompressVis (map_visibility + map_vis->bitofs[cluster][DVIS_PHS], phsrow);
	return phsrow;
}


/*
===============================================================================

AREAPORTALS

===============================================================================
*/

void FloodArea_r (carea_t *area, int floodnum)
{
	int		i;
	dareaportal_t	*p;

	if (area->floodvalid == floodvalid)
	{
		if (area->floodnum == floodnum)
			return;
		common.Com_Error (q_shared.ERR_DROP, "FloodArea_r: reflooded");
	}

	area->floodnum = floodnum;
	area->floodvalid = floodvalid;
	p = &map_areaportals[area->firstareaportal];
	for (i=0 ; i<area->numareaportals ; i++, p++)
	{
		if (portalopen[p->portalnum])
			FloodArea_r (&map_areas[p->otherarea], floodnum);
	}
}

/*
====================
FloodAreaConnections


====================
"""
def FloodArea_r (area: carea_t, floodnum: int):
	if area.floodvalid == floodvalid:
		if area.floodnum == floodnum:
			return
		common.Com_Error (q_shared.ERR_DROP, "FloodArea_r: reflooded")

	area.floodnum = floodnum
	area.floodvalid = floodvalid

	first_portal = area.firstareaportal if area.firstareaportal is not None else 0
	num_portals = area.numareaportals if area.numareaportals is not None else 0
	for i in range(num_portals):
		portal = map_areaportals[first_portal + i]
		if portalopen[portal.portalnum]:
			FloodArea_r (map_areas[portal.otherarea], floodnum)


def FloodAreaConnections ():
	"""
	Recursively flood areas connected through open portals.
	"""
	global floodvalid

	floodvalid += 1
	floodnum = 0

	for i in range(1, numareas):
		area = map_areas[i]
		if area.floodvalid == floodvalid:
			continue
		floodnum += 1
		FloodArea_r (area, floodnum)

"""
	int		i;
	carea_t	*area;
	int		floodnum;

	// all current floods are now invalid
	floodvalid++;
	floodnum = 0;

	// area 0 is not used
	for (i=1 ; i<numareas ; i++)
	{
		area = &map_areas[i];
		if (area->floodvalid == floodvalid)
			continue;		// already flooded into
		floodnum++;
		FloodArea_r (area, floodnum);
	}
	"""

"""
void	CM_SetAreaPortalState (int portalnum, qboolean open)
{
	if (portalnum > numareaportals)
		common.Com_Error (q_shared.ERR_DROP, "areaportal > numareaportals");

	portalopen[portalnum] = open;
	FloodAreaConnections ();
}

qboolean	CM_AreasConnected (int area1, int area2)
{
	if (map_noareas->value)
		return true;

	if (area1 > numareas || area2 > numareas)
		common.Com_Error (q_shared.ERR_DROP, "area > numareas");

	if (map_areas[area1].floodnum == map_areas[area2].floodnum)
		return true;
	return false;
}


/*
=================
CM_WriteAreaBits

Writes a length byte followed by a bit vector of all the areas
that area in the same flood as the area parameter

This is used by the client refreshes to cull visibility
=================
*/
int CM_WriteAreaBits (byte *buffer, int area)
{
	int		i;
	int		floodnum;
	int		bytes;

	bytes = (numareas+7)>>3;

	if (map_noareas->value)
	{	// for debugging, send everything
		memset (buffer, 255, bytes);
	}
	else
	{
		memset (buffer, 0, bytes);

		floodnum = map_areas[area].floodnum;
		for (i=0 ; i<numareas ; i++)
		{
			if (map_areas[i].floodnum == floodnum || !area)
				buffer[i>>3] |= 1<<(i&7);
		}
	}

	return bytes;
}


/*
===================
CM_WritePortalState

Writes the portal state to a savegame file
===================
*/
void	CM_WritePortalState (FILE *f)
{
	fwrite (portalopen, sizeof(portalopen), 1, f);
}

/*
===================
CM_ReadPortalState

Reads the portal state from a savegame file
and recalculates the area connections
===================
*/
void	CM_ReadPortalState (FILE *f)
{
	FS_Read (portalopen, sizeof(portalopen), f);
	FloodAreaConnections ();
}

/*
=============
CM_HeadnodeVisible

Returns true if any leaf under headnode has a cluster that
is potentially visible
=============
*/
qboolean CM_HeadnodeVisible (int nodenum, byte *visbits)
{
	int		leafnum;
	int		cluster;
	cnode_t	*node;

	if (nodenum < 0)
	{
		leafnum = -1-nodenum;
		cluster = map_leafs[leafnum].cluster;
		if (cluster == -1)
			return false;
		if (visbits[cluster>>3] & (1<<(cluster&7)))
			return true;
		return false;
	}

	node = &map_nodes[nodenum];
	if (CM_HeadnodeVisible(node->children[0], visbits))
		return true;
	return CM_HeadnodeVisible(node->children[1], visbits);
}
"""
