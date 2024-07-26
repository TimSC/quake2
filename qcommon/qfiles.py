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
import numpy as np
from game import q_shared
"""

//
// qfiles.h: quake file formats
// This file must be identical in the quake and utils directories
//

/*
========================================================================

The .pak files are just a linear collapse of a directory tree

========================================================================
*/
"""
IDPAKHEADER		= (ord('K')<<24)+(ord('C')<<16)+(ord('A')<<8)+ord('P')


class dpackfile_t(object):

	def __init__(self):
		self.name = None #char [56]
		self.filepos, self.filelen = None, None # int

	def read(self, fi):
		self.name = fi.read(56).decode("ascii").replace("\x00", "", -1)

		self.filepos, self.filelen = struct.unpack('<ll', fi.read(8))

	def __repr__(self):
		return "dpackfile_t ({} {} {})".format(self.name, self.filepos, self.filelen)

class dpackheader_t(object):
	def __init__(self):

		ident = None #int == IDPAKHEADER
		dirofs = None #int
		dirlen = None #int

	def read(self, fi):

		self.ident, self.dirofs, self.dirlen = struct.unpack('<lll', fi.read(12))

		if self.ident != IDPAKHEADER:
			common.Com_Error (ERR_FATAL, "{} is not a packfile".format(packfile))


MAX_FILES_IN_PACK = 4096


"""
========================================================================

PCX files are used for as many images as possible

========================================================================
"""

class pcx_t (object):

	def __init__(self):

		self.manufacturer = None #char
		self.version = None #char
		self.encoding = None #char
		self.bits_per_pixel = None #char
		self.xmin,ymin,xmax,ymax = None,None,None,None #unsigned short
		self.hres,vres = None,None #unsigned short
		self.palette=[] #unsigned char[48]
		self.reserved = None #char
		self.color_planes = None #char
		self.bytes_per_line = None #unsigned short
		self.palette_type = None #unsigned short
		self.filler = [] #char[58]
		self.data = None

	def Read(self, buff):

		self.manufacturer, self.version, self.encoding, self.bits_per_pixel = struct.unpack("<BBBB", buff[:4])
		self.xmin = struct.unpack("<H", buff[4:6])[0]
		self.ymin = struct.unpack("<H", buff[6:8])[0]
		self.xmax = struct.unpack("<H", buff[8:10])[0]
		self.ymax = struct.unpack("<H", buff[10:12])[0]
		self.hres = struct.unpack("<H", buff[12:14])[0]
		self.vres = struct.unpack("<H", buff[14:16])[0]

		self.palette = buff[16:64]

		self.reserved, self.color_planes = struct.unpack("<BB", buff[64:66])

		self.bytes_per_line = struct.unpack("<H", buff[66:68])[0]
		self.palette_type = struct.unpack("<H", buff[68:70])[0]
		
		self.filler = buff[70:128]
		self.data = buff[128:]

		if (self.manufacturer != 0x0a
			or self.version != 5
			or self.encoding != 1
			or self.bits_per_pixel != 8
			or self.xmax >= 640
			or self.ymax >= 480):
		
			return False
		return True

	def Decompress(self, buff):

		ok = self.Read(buff)
		if not ok: return None, None, None, None

		pic = bytearray((self.ymax+1) * (self.xmax+1))
		
		palette = buff[-256*3:]
		width = self.xmax+1
		height = self.ymax+1

		y = 0
		cursor = 0
		picCursor = 0
		for y in range(self.ymax+1):
			picCursor = y * (self.xmax + 1)
		
			x = 0
			while x <= self.xmax:
				
				dataByte = self.data[cursor]
				cursor += 1

				if (dataByte & 0xC0) == 0xC0:
				
					runLength = dataByte & 0x3F
					dataByte = self.data[cursor]
					cursor += 1
				
				else:
					runLength = 1

				for r in range(runLength):
					pic[picCursor + x] = dataByte
					x += 1

		return pic, palette, width, height
		
	def DecodeToPixels(self, buff):
		from PIL import Image

		pic, palette, width, height = self.Decompress(buff)
		if pic is None:
			return None

		pall = []
		for i in range(0, len(palette), 3):
			pall.append(struct.unpack("<BBB", palette[i:i+3]))

		im = Image.new("RGB", (self.xmax+1, self.ymax+1))
		px = im.load()
		for y in range(self.ymax+1):
			for x in range(self.xmax+1):
				px[x, y] = pall[pic[y*(self.xmax+1) + x]]

		return im

"""
========================================================================

.MD2 triangle model file format

========================================================================
*/
"""
IDALIASHEADER = ((ord('2')<<24)+(ord('P')<<16)+(ord('D')<<8)+ord('I'))
ALIAS_VERSION = 8
"""
#define	MAX_TRIANGLES	4096
#define MAX_VERTS		2048
#define MAX_FRAMES		512
#define MAX_MD2SKINS	32
#define	MAX_SKINNAME	64

typedef struct
{
	short	s;
	short	t;
} dstvert_t;

typedef struct 
{
	short	index_xyz[3];
	short	index_st[3];
} dtriangle_t;

typedef struct
{
	byte	v[3];			// scaled byte to fit in frame mins/maxs
	byte	lightnormalindex;
} dtrivertx_t;

#define DTRIVERTX_V0   0
#define DTRIVERTX_V1   1
#define DTRIVERTX_V2   2
#define DTRIVERTX_LNI  3
#define DTRIVERTX_SIZE 4

typedef struct
{
	float		scale[3];	// multiply byte verts by this
	float		translate[3];	// then add this
	char		name[16];	// frame name from grabbing
	dtrivertx_t	verts[1];	// variable sized
} daliasframe_t;


// the glcmd format:
// a positive integer starts a tristrip command, followed by that many
// vertex structures.
// a negative integer starts a trifan command, followed by -x vertexes
// a zero indicates the end of the command list.
// a vertex consists of a floating point s, a floating point t,
// and an integer vertex index.


typedef struct
{
	int			ident;
	int			version;

	int			skinwidth;
	int			skinheight;
	int			framesize;		// byte size of each frame

	int			num_skins;
	int			num_xyz;
	int			num_st;			// greater than num_xyz for seams
	int			num_tris;
	int			num_glcmds;		// dwords in strip/fan command list
	int			num_frames;

	int			ofs_skins;		// each skin is a MAX_SKINNAME string
	int			ofs_st;			// byte offset from start for stverts
	int			ofs_tris;		// offset for dtriangles
	int			ofs_frames;		// offset for first frame
	int			ofs_glcmds;	
	int			ofs_end;		// end of file

} dmdl_t;

/*
========================================================================

.SP2 sprite file format

========================================================================
*/
"""
IDSPRITEHEADER	= ((ord('2')<<24)+(ord('S')<<16)+(ord('D')<<8)+ord('I'))
		# little-endian "IDS2"
SPRITE_VERSION	= 2
"""
typedef struct
{
	int		width, height;
	int		origin_x, origin_y;		// raster coordinates inside pic
	char	name[MAX_SKINNAME];		// name of pcx file
} dsprframe_t;

typedef struct {
	int			ident;
	int			version;
	int			numframes;
	dsprframe_t	frames[1];			// variable sized
} dsprite_t;

/*
==============================================================================

  .WAL texture file format

==============================================================================
*/


#define	MIPLEVELS	4
typedef struct miptex_s
{
	char		name[32];
	unsigned	width, height;
	unsigned	offsets[MIPLEVELS];		// four mip maps stored
	char		animname[32];			// next frame in animation chain
	int			flags;
	int			contents;
	int			value;
} miptex_t;



/*
==============================================================================

  .BSP file format

==============================================================================
*/
"""
IDBSPHEADER	= ((ord('P')<<24)+(ord('S')<<16)+(ord('B')<<8)+ord('I'))
		# little-endian "IBSP"
BSPVERSION = 38


# upper design bounds
# leaffaces, leafbrushes, planes, and verts are still bounded by
# 16 bit short limits
MAX_MAP_MODELS		= 1024
MAX_MAP_BRUSHES		= 8192
MAX_MAP_ENTITIES	= 2048
MAX_MAP_ENTSTRING	= 0x40000
MAX_MAP_TEXINFO		= 8192

MAX_MAP_AREAS		= 256
MAX_MAP_AREAPORTALS	= 1024
MAX_MAP_PLANES		= 65536
MAX_MAP_NODES		= 65536
MAX_MAP_BRUSHSIDES	= 65536
MAX_MAP_LEAFS		= 65536
MAX_MAP_VERTS		= 65536
MAX_MAP_FACES		= 65536
MAX_MAP_LEAFFACES	= 65536
MAX_MAP_LEAFBRUSHES = 65536
MAX_MAP_PORTALS		= 65536
MAX_MAP_EDGES		= 128000
MAX_MAP_SURFEDGES	= 256000
MAX_MAP_LIGHTING	= 0x200000
MAX_MAP_VISIBILITY	= 0x100000
"""
// key / value pair sizes

#define	MAX_KEY		32
#define	MAX_VALUE	1024

//=============================================================================
"""
class lump_t(object):
	def __init__(self, fileofsIn=None, filelenIn=None):
		self.fileofs = fileofsIn # int
		self.filelen = filelenIn

	@classmethod
	def packed_size(cls):
		return 8

	def __repr__(self):

		return "lumpt({}, {})".format(self.fileofs, self.filelen)


LUMP_ENTITIES		= 0
LUMP_PLANES			= 1
LUMP_VERTEXES		= 2
LUMP_VISIBILITY		= 3
LUMP_NODES			= 4
LUMP_TEXINFO		= 5
LUMP_FACES			= 6
LUMP_LIGHTING		= 7
LUMP_LEAFS			= 8
LUMP_LEAFFACES		= 9
LUMP_LEAFBRUSHES	= 10
LUMP_EDGES			= 11
LUMP_SURFEDGES		= 12
LUMP_MODELS			= 13
LUMP_BRUSHES		= 14
LUMP_BRUSHSIDES		= 15
LUMP_POP			= 16
LUMP_AREAS			= 17
LUMP_AREAPORTALS	= 18
HEADER_LUMPS = 19

class dheader_t(object):

	def __init__(self):

		self.ident = None #int			
		self.version = None #int			
		self.lumps = None # lump_t[HEADER_LUMPS]

	@classmethod
	def packed_size(cls):
		return 8 * lump_t.packed_size() * HEADER_LUMPS

	def parse(self, buf: bytes|bytearray):
		
		self.ident = struct.unpack("<I", buf[:4])[0]
		self.version = struct.unpack("<I", buf[4:8])[0] #int
		self.lumps = [] # lump_t[HEADER_LUMPS]
		cursor = 8
		for i in range(HEADER_LUMPS):
			self.lumps.append(lump_t(*struct.unpack("<II", buf[cursor:cursor+8])))
			cursor += 8


class dmodel_t(object):

	def __init__(self):

		self.mins = np.zeros((3,), dtype=np.float32) # float[3]
		self.maxs = np.zeros((3,), dtype=np.float32) # float[3]
		self.origin = np.zeros((3,), dtype=np.float32) # float[3], for sounds or lights
		self.headnode = None # int
		self.firstface = None # int, submodels just draw faces
				  # without walking the bsp tree
		self.numfaces = None # int

	@classmethod
	def packed_size(cls):
		return 48

	def load(self, buff):

		c = 0
		for j in range(3):
			self.mins[j] = q_shared.LittleFloat (buff[c:c+4])
			c += 4

		for j in range(3):
			self.maxs[j] = q_shared.LittleFloat (buff[c:c+4])
			c += 4

		for j in range(3):
			self.origin[j] = q_shared.LittleFloat (buff[c:c+4])
			c += 4

		self.headnode = q_shared.LittleSLong (buff[c:c+4])
		c += 4


class dvertex_t(object):

	def __init__(self):
		self.point = np.zeros((3,), dtype=np.float32) #float[3]

	@classmethod
	def packed_size(cls):
		return 12

	def load(self, buff):

		self.point[0] = q_shared.LittleFloat(buff[:4])
		self.point[1] = q_shared.LittleFloat(buff[4:8])
		self.point[2] = q_shared.LittleFloat(buff[8:])

"""
// 0-2 are axial planes
#define	PLANE_X			0
#define	PLANE_Y			1
#define	PLANE_Z			2

// 3-5 are non-axial planes snapped to the nearest
#define	PLANE_ANYX		3
#define	PLANE_ANYY		4
#define	PLANE_ANYZ		5
"""
# planes (x&~1) and (x&~1)+1 are always opposites

class dplane_t(object):

	def __init__(self):

		self.normal = np.zeros((3,), dtype=np.float32) # float[3]
		self.dist = None # float
		self.type = None # int, PLANE_X - PLANE_ANYZ ?remove? trivial to regenerate

	@classmethod
	def packed_size(cls):
		return 20

	def load(self, buff):

		self.normal[0] = q_shared.LittleFloat(buff[:4])
		self.normal[1] = q_shared.LittleFloat(buff[4:8])
		self.normal[2] = q_shared.LittleFloat(buff[8:12])
		self.dist = q_shared.LittleFloat(buff[12:16])
		self.type = q_shared.LittleLong(buff[16:])

# contents flags are seperate bits
# a given brush can contribute multiple content bits
# multiple brushes can be in a single leaf

# these definitions also need to be in q_shared.h!

# lower bits are stronger, and will eat weaker brushes completely
CONTENTS_SOLID			= 1		# an eye is never valid in a solid
CONTENTS_WINDOW			= 2		# translucent, but not watery
CONTENTS_AUX			= 4
CONTENTS_LAVA			= 8
CONTENTS_SLIME			= 16
CONTENTS_WATER			= 32
CONTENTS_MIST			= 64
LAST_VISIBLE_CONTENTS	= 64
"""
// remaining contents are non-visible, and don't eat brushes

#define	CONTENTS_AREAPORTAL		0x8000

#define	CONTENTS_PLAYERCLIP		0x10000
#define	CONTENTS_MONSTERCLIP	0x20000

// currents can be added to any other contents, and may be mixed
#define	CONTENTS_CURRENT_0		0x40000
#define	CONTENTS_CURRENT_90		0x80000
#define	CONTENTS_CURRENT_180	0x100000
#define	CONTENTS_CURRENT_270	0x200000
#define	CONTENTS_CURRENT_UP		0x400000
#define	CONTENTS_CURRENT_DOWN	0x800000

#define	CONTENTS_ORIGIN			0x1000000	// removed before bsping an entity

#define	CONTENTS_MONSTER		0x2000000	// should never be on a brush, only in game
#define	CONTENTS_DEADMONSTER	0x4000000
#define	CONTENTS_DETAIL			0x8000000	// brushes to be added after vis leafs
#define	CONTENTS_TRANSLUCENT	0x10000000	// auto set if any surface has trans
#define	CONTENTS_LADDER			0x20000000



#define	SURF_LIGHT		0x1		// value will hold the light strength

#define	SURF_SLICK		0x2		// effects game physics

#define	SURF_SKY		0x4		// don't draw, but add to skybox
#define	SURF_WARP		0x8		// turbulent water warp
#define	SURF_TRANS33	0x10
#define	SURF_TRANS66	0x20
#define	SURF_FLOWING	0x40	// scroll towards angle
#define	SURF_NODRAW		0x80	// don't bother referencing the texture

"""


class dnode_t(object):

	def __init__(self):

		self.planenum: int = None
		self.children = [None, None] # int[2], negative numbers are -(leafs+1), not nodes
		self.mins = np.zeros((3,), dtype=np.int16) # short[3]		# for frustom culling
		self.maxs = np.zeros((3,), dtype=np.int16) # short[3]
		self.firstface = None # unsigned short
		self.numfaces = None # unsigned short, counting both sides

	@classmethod
	def packed_size(cls):
		return 28

	def load(self, buff):

		self.planenum = q_shared.LittleLong(buff[:4])
		self.children[0] = q_shared.LittleLong(buff[4:8])
		self.children[1] = q_shared.LittleLong(buff[8:12])


class texinfo_t(object):

	def __init__(self):

		self.vecs = np.zeros((2,4), dtype=np.float32) # float[2][4], [s/t][xyz offset]
		self.flags = None # int, miptex flags + overrides
		self.value = None # int, light emission, etc
		self.texture = None # char[32],	texture name (textures/*.wal)
		self.nexttexinfo = None # int, for animations, -1 = end of chain
 
	@classmethod
	def packed_size(cls):
		return 76

	def load(self, buff):

		c = 0
		for j in range(8):
			self.vecs[j%2,j//2] = q_shared.LittleFloat (buff[c:c+4])
			c+=4

		self.flags = q_shared.LittleSLong(buff[32:36])
		self.value = q_shared.LittleSLong(buff[36:40])
		self.texture = buff[40:72].decode("ascii").rstrip('\x00')
		self.nexttexinfo = q_shared.LittleSLong(buff[72:])


# note that edge 0 is never used, because negative edge nums are used for
# counterclockwise use of the edge in a face
class dedge_t(object):

	def __init__(self):

		self.v = np.zeros((2,), dtype=np.uint16)

	@classmethod
	def packed_size(cls):
		return 4

	def load(self, buff):

		self.v[0] = q_shared.LittleShort(buff[:2])
		self.v[1] = q_shared.LittleShort(buff[2:])

"""
#define	MAXLIGHTMAPS	4
typedef struct
{
	unsigned short	planenum;
	short		side;

	int			firstedge;		// we must support > 64k edges
	short		numedges;	
	short		texinfo;

// lighting info
	byte		styles[MAXLIGHTMAPS];
	int			lightofs;		// start of [numstyles*surfsize] samples
} dface_t;
"""

class dleaf_t(object):

	def __init__(self):

		self.contents = None # int, OR of all brushes (not needed?)

		self.cluster = None # short
		self.area = None # short

		self.mins = np.zeros((3,), dtype=np.int16) # short[3]			# for frustum culling
		self.maxs = np.zeros((3,), dtype=np.int16) # short[3]

		self.firstleafface = None # unsigned short
		self.numleaffaces = None # unsigned short

		self.firstleafbrush = None # unsigned short
		self.numleafbrushes = None # unsigned short

	@classmethod
	def packed_size(cls):
		return 28

	def load(self, buff):

		self.contents = q_shared.LittleLong(buff[:4])
		self.cluster = q_shared.LittleShort (buff[4:6])
		self.area = q_shared.LittleShort (buff[6:8])
		self.firstleafbrush = q_shared.LittleShort (buff[24:26])
		self.numleafbrushes = q_shared.LittleShort (buff[26:])


class dbrushside_t(object):

	def __init__(self):

		self.planenum = None # unsigned short, facing out of the leaf
		self.texinfo = None # short

	@classmethod
	def packed_size(cls):
		return 4

	def load(self, buff):

		self.planenum = q_shared.LittleShort (buff[:2])
		self.texinfo = q_shared.LittleSShort (buff[2:])

class dbrush_t(object):

	def __init__(self):

		self.firstside = None # int
		self.numsides = None # int
		self.contents = None # int

	@classmethod
	def packed_size(cls):
		return 12

	def load(self, buff):

		self.firstside = q_shared.LittleLong (buff[:4])
		self.numsides = q_shared.LittleLong (buff[4:8])
		self.contents = q_shared.LittleLong (buff[8:])

ANGLE_UP   = -1
ANGLE_DOWN = -2


# the visibility lump consists of a header with a count, then
# byte offsets for the PVS and PHS of each cluster, then the raw
# compressed bit vectors
DVIS_PVS	= 0
DVIS_PHS	= 1
class dvis_t(object):

	def __init__(self):

		self.numclusters = None # int
		self.bitofs = np.zeros((8,2), dtype=np.int32) # int[8][2], bitofs[numclusters][2]

	@classmethod
	def packed_size(cls):
		return 68

	def load(self, buff):

		self.numclusters = q_shared.LittleSLong (buff[:4])
		if self.numclusters > 8: self.numclusters = 8 # Prevent over-read
		c = 4

		for i in range(self.numclusters):
		
			self.bitofs[i][0] = q_shared.LittleLong (buff[c:c+4])
			c += 4
			self.bitofs[i][1] = q_shared.LittleLong (buff[c:c+4])
			c += 4

# each area has a list of portals that lead into other areas
# when portals are closed, other areas may not be visible or
# hearable even if the vis info says that it should be
class dareaportal_t(object):

	def __init__(self):
		self.portalnum = 0 # int		
		self.otherarea = 0 # int

	@classmethod
	def packed_size(cls):
		return 8

	def load(self, buff):

		self.portalnum = q_shared.LittleSLong (buff[:4])
		self.otherarea = q_shared.LittleSLong (buff[4:])

class darea_t(object):

	def __init__(self):

		self.numareaportals = None # int
		self.firstareaportal = None # int

	@classmethod
	def packed_size(cls):
		return 8

	def load(self, buff):

		self.numareaportals = q_shared.LittleSLong (buff[:4])
		self.firstareaportal = q_shared.LittleSLong (buff[4:])

