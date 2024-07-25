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
import io
import math
import struct
import OpenGL.GL as GL
import OpenGL.GL.ARB.multitexture as GLmt
import pygame
from enum import Enum
from game import q_shared
from ref_gl import gl_rmain, gl_model
from qcommon import qfiles, qcommon
from linux import qgl_linux

class imagetype_t(Enum):

	it_skin = 0
	it_sprite = 1
	it_wall = 2
	it_pic = 3
	it_sky = 4

class image_t(object):

	def __init__(self):

		self.name = None #char	[MAX_QPATH], game path, including extension
		self.type = imagetype_t.it_skin #imagetype_t
		self.width, self.height = None, None #int, source image
		self.upload_width, self.upload_height = None, None #int, after power of two and picmip
		self.registration_sequence = None #int, 0 = free
		self.texturechain = None #struct msurface_s	*, for sort-by-texture world drawing
		self.texnum = None #int, gl texture binding
		self.sl, self.tl, self.sh, self.th = 0.0, 0.0, 0.0, 0.0 #float, 0,0 - 1,1 unless part of the scrap
		self.scrap = False #qboolean
		self.has_alpha = False #qboolean

		self.paletted = False #qboolean

TEXNUM_LIGHTMAPS	= 1024
TEXNUM_SCRAPS		= 1152
TEXNUM_IMAGES		= 1153

MAX_GLTEXTURES	= 1024

#include "gl_local.h"

gltextures = [] #image_t[MAX_GLTEXTURES];
for i in range(MAX_GLTEXTURES):
	gltextures.append(image_t())

numgltextures = 0 #int

"""
int			base_textureid;		// gltextures[i] = base_textureid+i
"""
intensitytable = bytearray(256) #static byte[256]
gammatable = bytearray(256) #static unsigned char[256]
"""
cvar_t		*intensity;
"""
d_8to24table = [] #unsigned [256];
for i in range(256):
	d_8to24table.append(None)
"""
qboolean GL_Upload8 (byte *data, int width, int height,  qboolean mipmap, qboolean is_sky );
qboolean GL_Upload32 (unsigned *data, int width, int height,  qboolean mipmap);

"""
gl_solid_format = 3 #int
gl_alpha_format = 4 #int

gl_tex_solid_format = 3 #int
gl_tex_alpha_format = 4 #int


gl_filter_min = GL.GL_LINEAR_MIPMAP_NEAREST #int
gl_filter_max = GL.GL_LINEAR #int


def GL_SetTexturePalette(palette): #unsigned palette[256]

	"""
	int i;
	unsigned char temptable[768];
	"""

	if qgl_linux.qglColorTableEXT and gl_ext_palettedtexture.value:

		raise NotImplementedError()

		"""	
		for ( i = 0; i < 256; i++ )
		{
			temptable[i*3+0] = ( palette[i] >> 0 ) & 0xff;
			temptable[i*3+1] = ( palette[i] >> 8 ) & 0xff;
			temptable[i*3+2] = ( palette[i] >> 16 ) & 0xff;
		}

		qglColorTableEXT( GL_SHARED_TEXTURE_PALETTE_EXT,
						   GL_RGB,
						   256,
						   GL_RGB,
						   GL_UNSIGNED_BYTE,
						   temptable );
	
		"""


def GL_EnableMultitexture( enable ):

	if not qgl_linux.qglSelectTextureSGIS and not qgl_linux.qglActiveTextureARB:
		return

	if enable :
	
		GL_SelectTexture( GL.GL_TEXTURE1 )
		GL.glEnable( GL.GL_TEXTURE_2D )
		GL_TexEnv( GL.GL_REPLACE )
	
	else:
	
		GL_SelectTexture( GL.GL_TEXTURE1 )
		GL.glDisable( GL.GL_TEXTURE_2D )
		GL_TexEnv( GL.GL_REPLACE )
	
	GL_SelectTexture( GL.GL_TEXTURE0 )
	GL_TexEnv( GL.GL_REPLACE )


def GL_SelectTexture( texture ): #GLenum

	#int tmu;

	if not qgl_linux.qglSelectTextureSGIS and not qgl_linux.qglActiveTextureARB:
		return

	if texture == GL.GL_TEXTURE0:
		tmu = 0
	
	else:
		tmu = 1
	
	if tmu == gl_rmain.gl_state.currenttmu:
		return
	
	gl_rmain.gl_state.currenttmu = tmu

	if qgl_linux.qglSelectTextureSGIS:
	
		GLmt.glSelectTextureSGIS( texture )
	
	elif qgl_linux.qglActiveTextureARB:
	
		GLmt.glActiveTextureARB( texture )
		GLmt.glClientActiveTextureARB( texture )
	

lastmodes = [-1, -1] # int[2]

def GL_TexEnv( mode ): #GLenum
	global lastmodes

	if mode != lastmodes[gl_rmain.gl_state.currenttmu]:
	
		GL.glTexEnvf( GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, mode )
		lastmodes[gl_rmain.gl_state.currenttmu] = mode
	
def GL_Bind (texnum): #int

	#extern	image_t	*draw_chars;

	if gl_rmain.gl_nobind.value and gl_draw.draw_chars is not None:		# performance evaluation option
		texnum = gl_draw.draw_chars.texnum
	if gl_rmain.gl_state.currenttextures[gl_rmain.gl_state.currenttmu] == texnum:
		return
	gl_rmain.gl_state.currenttextures[gl_rmain.gl_state.currenttmu] = texnum
	GL.glBindTexture (GL.GL_TEXTURE_2D, texnum)

"""
void GL_MBind( GLenum target, int texnum )
{
	GL_SelectTexture( target );
	if ( target == GL_TEXTURE0 )
	{
		if ( gl_rmain.gl_state.currenttextures[0] == texnum )
			return;
	}
	else
	{
		if ( gl_rmain.gl_state.currenttextures[1] == texnum )
			return;
	}
	GL_Bind( texnum );
}
"""

class glmode_t(object):
	def __init__(self, nameIn=None, minimizeIn=None, maximizeIn=None):

		self.name = nameIn #char *
		self.minimize, self.maximize = minimizeIn, maximizeIn #int

modes = [
	glmode_t("GL_NEAREST", GL.GL_NEAREST, GL.GL_NEAREST),
	glmode_t("GL_LINEAR", GL.GL_LINEAR, GL.GL_LINEAR),
	glmode_t("GL_NEAREST_MIPMAP_NEAREST", GL.GL_NEAREST_MIPMAP_NEAREST, GL.GL_NEAREST),
	glmode_t("GL_LINEAR_MIPMAP_NEAREST", GL.GL_LINEAR_MIPMAP_NEAREST, GL.GL_LINEAR),
	glmode_t("GL_NEAREST_MIPMAP_LINEAR", GL.GL_NEAREST_MIPMAP_LINEAR, GL.GL_NEAREST),
	glmode_t("GL_LINEAR_MIPMAP_LINEAR", GL.GL_LINEAR_MIPMAP_LINEAR, GL.GL_LINEAR)
] #glmode_t[]

NUM_GL_MODES = len(modes)
"""
typedef struct
{
	char *name;
	int mode;
} gltmode_t;

gltmode_t gl_alpha_modes[] = {
	{"default", 4},
	{"GL_RGBA", GL_RGBA},
	{"GL_RGBA8", GL_RGBA8},
	{"GL_RGB5_A1", GL_RGB5_A1},
	{"GL_RGBA4", GL_RGBA4},
	{"GL_RGBA2", GL_RGBA2},
};

#define NUM_GL_ALPHA_MODES (sizeof(gl_alpha_modes) / sizeof (gltmode_t))

gltmode_t gl_solid_modes[] = {
	{"default", 3},
	{"GL_RGB", GL_RGB},
	{"GL_RGB8", GL_RGB8},
	{"GL_RGB5", GL_RGB5},
	{"GL_RGB4", GL_RGB4},
	{"GL_R3_G3_B2", GL_R3_G3_B2},
#ifdef GL_RGB2_EXT
	{"GL_RGB2", GL_RGB2_EXT},
#endif
};

#define NUM_GL_SOLID_MODES (sizeof(gl_solid_modes) / sizeof (gltmode_t))

/*
===============
GL_TextureMode
===============
"""
def GL_TextureMode( string ): #char *

	#int		i;
	#image_t	*glt;

	foundMode = None
	for mode in modes:
	
		if mode.name == string:
			foundMode = mode
			break;
	
	if foundMode is None:
	
		gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "bad filter name\n")
		return
	
	gl_filter_min = foundMode.minimize
	gl_filter_max = foundMode.maximize

	# change all the existing mipmap texture objects
	for i in range(numgltextures):
		glt = gltextures[i]
	
		if glt.type != imagetype_t.it_pic and glt.type != imagetype_t.it_sky:
		
			GL_Bind (glt.texnum)
			GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, gl_filter_min)
			GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, gl_filter_max)

"""
===============
GL_TextureAlphaMode
===============
"""
def GL_TextureAlphaMode( string ): #char *

	pass
	"""
	int		i;

	for (i=0 ; i< NUM_GL_ALPHA_MODES ; i++)
	{
		if ( !Q_stricmp( gl_alpha_modes[i].name, string ) )
			break;
	}

	if (i == NUM_GL_ALPHA_MODES)
	{
		gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "bad alpha texture mode name\n");
		return;
	}

	gl_tex_alpha_format = gl_alpha_modes[i].mode;



===============
GL_TextureSolidMode
===============
"""
def GL_TextureSolidMode( string ): #char *

	pass
	"""
	int		i;

	for (i=0 ; i< NUM_GL_SOLID_MODES ; i++)
	{
		if ( !Q_stricmp( gl_solid_modes[i].name, string ) )
			break;
	}

	if (i == NUM_GL_SOLID_MODES)
	{
		gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "bad solid texture mode name\n");
		return;
	}

	gl_tex_solid_format = gl_solid_modes[i].mode;


===============
GL_ImageList_f
===============
"""
def GL_ImageList_f ():

	"""
	int		i;
	image_t	*image;
	int		texels;
	"""
	palstrings = ["RGB", "PAL"]

	gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "------------------\n")
	texels = 0

	for i in range(numgltextures):
	
		image=gltextures[i]
		if image.texnum <= 0:
			continue
		texels += image.upload_width*image.upload_height;
		if image.type == imagetype_t.it_skin:
			gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "M");

		elif image.type == imagetype_t.it_sprite:
			gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "S");

		elif image.type == imagetype_t.it_wall:
			gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "W");

		elif image.type == imagetype_t.it_pic:
			gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "P");

		else:
			gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, " ");

		gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL,  " {:3d} {:3d} {}: {}\n".format(
			image.upload_width, image.upload_height, palstrings[image.paletted], image.name))
	
	gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "Total texel count (not counting mipmaps): {}\n".format(texels))



"""
=============================================================================

  scrap allocation

  Allocate all the little status bar obejcts into a single texture
  to crutch up inefficient hardware / drivers

=============================================================================
*/

#define	MAX_SCRAPS		1
#define	BLOCK_WIDTH		256
#define	BLOCK_HEIGHT	256

int			scrap_allocated[MAX_SCRAPS][BLOCK_WIDTH];
byte		scrap_texels[MAX_SCRAPS][BLOCK_WIDTH*BLOCK_HEIGHT];
"""
scrap_dirty = False #qboolean
"""
// returns a texture number and the position inside it
int Scrap_AllocBlock (int w, int h, int *x, int *y)
{
	int		i, j;
	int		best, best2;
	int		texnum;

	for (texnum=0 ; texnum<MAX_SCRAPS ; texnum++)
	{
		best = BLOCK_HEIGHT;

		for (i=0 ; i<BLOCK_WIDTH-w ; i++)
		{
			best2 = 0;

			for (j=0 ; j<w ; j++)
			{
				if (scrap_allocated[texnum][i+j] >= best)
					break;
				if (scrap_allocated[texnum][i+j] > best2)
					best2 = scrap_allocated[texnum][i+j];
			}
			if (j == w)
			{	// this is a valid spot
				*x = i;
				*y = best = best2;
			}
		}

		if (best + h > BLOCK_HEIGHT)
			continue;

		for (i=0 ; i<w ; i++)
			scrap_allocated[texnum][*x + i] = best + h;

		return texnum;
	}

	return -1;
//	Sys_Error ("Scrap_AllocBlock: full");
}

int	scrap_uploads;

"""
def Scrap_Upload ():

	#scrap_uploads++;
	#GL_Bind(TEXNUM_SCRAPS);
	#GL_Upload8 (scrap_texels[0], BLOCK_WIDTH, BLOCK_HEIGHT, false, false );
	scrap_dirty = False

"""
=================================================================

PCX LOADING

=================================================================
*/


/*
==============
LoadPCX
==============
"""
def LoadPCX (filename): #char *, byte **, byte **, int *, int *

	#
	# load the file
	#
	length, raw = gl_rmain.ri.FS_LoadFile (filename)
	if raw is None:
	
		gl_rmain.ri.Con_Printf (qcommon.PRINT_DEVELOPER, "Bad pcx file {}\n".format(filename))
		return None, None, None, None
	
	#
	# parse the PCX file
	#
	pcx = qfiles.pcx_t()
	pcx.DecodeToPixels(raw)
	
	try:
		pic, palette, width, height = pcx.Decompress(raw)
	except IndexError:
		pic = None
		gl_rmain.ri.Con_Printf (q_shared.PRINT_DEVELOPER, "PCX file {} was malformed".format(filename))

	if pic is None:
		gl_rmain.ri.Con_Printf (q_shared.q_shared.PRINT_ALL, "Bad pcx file {}\n".format(filename))
		return None, None, None, None

	return pic, palette, width, height

"""
=========================================================

TARGA LOADING

=========================================================
*/

typedef struct _TargaHeader {
	unsigned char 	id_length, colormap_type, image_type;
	unsigned short	colormap_index, colormap_length;
	unsigned char	colormap_size;
	unsigned short	x_origin, y_origin, width, height;
	unsigned char	pixel_size, attributes;
} TargaHeader;


/*
=============
LoadTGA
=============
*/
void LoadTGA (char *name, byte **pic, int *width, int *height)
{
	int		columns, rows, numPixels;
	byte	*pixbuf;
	int		row, column;
	byte	*buf_p;
	byte	*buffer;
	int		length;
	TargaHeader		targa_header;
	byte			*targa_rgba;
	byte tmp[2];

	*pic = NULL;

	//
	// load the file
	//
	length = gl_rmain.ri.FS_LoadFile (name, (void **)&buffer);
	if (!buffer)
	{
		gl_rmain.ri.Con_Printf (PRINT_DEVELOPER, "Bad tga file %s\n", name);
		return;
	}

	buf_p = buffer;

	targa_header.id_length = *buf_p++;
	targa_header.colormap_type = *buf_p++;
	targa_header.image_type = *buf_p++;
	
	tmp[0] = buf_p[0];
	tmp[1] = buf_p[1];
	targa_header.colormap_index = LittleShort ( *((short *)tmp) );
	buf_p+=2;
	tmp[0] = buf_p[0];
	tmp[1] = buf_p[1];
	targa_header.colormap_length = LittleShort ( *((short *)tmp) );
	buf_p+=2;
	targa_header.colormap_size = *buf_p++;
	targa_header.x_origin = LittleShort ( *((short *)buf_p) );
	buf_p+=2;
	targa_header.y_origin = LittleShort ( *((short *)buf_p) );
	buf_p+=2;
	targa_header.width = LittleShort ( *((short *)buf_p) );
	buf_p+=2;
	targa_header.height = LittleShort ( *((short *)buf_p) );
	buf_p+=2;
	targa_header.pixel_size = *buf_p++;
	targa_header.attributes = *buf_p++;

	if (targa_header.image_type!=2 
		&& targa_header.image_type!=10) 
		gl_rmain.ri.Sys_Error (ERR_DROP, "LoadTGA: Only type 2 and 10 targa RGB images supported\n");

	if (targa_header.colormap_type !=0 
		|| (targa_header.pixel_size!=32 && targa_header.pixel_size!=24))
		gl_rmain.ri.Sys_Error (ERR_DROP, "LoadTGA: Only 32 or 24 bit images supported (no colormaps)\n");

	columns = targa_header.width;
	rows = targa_header.height;
	numPixels = columns * rows;

	if (width)
		*width = columns;
	if (height)
		*height = rows;

	targa_rgba = malloc (numPixels*4);
	*pic = targa_rgba;

	if (targa_header.id_length != 0)
		buf_p += targa_header.id_length;  // skip TARGA image comment
	
	if (targa_header.image_type==2) {  // Uncompressed, RGB images
		for(row=rows-1; row>=0; row--) {
			pixbuf = targa_rgba + row*columns*4;
			for(column=0; column<columns; column++) {
				unsigned char red,green,blue,alphabyte;
				switch (targa_header.pixel_size) {
					case 24:
							
							blue = *buf_p++;
							green = *buf_p++;
							red = *buf_p++;
							*pixbuf++ = red;
							*pixbuf++ = green;
							*pixbuf++ = blue;
							*pixbuf++ = 255;
							break;
					case 32:
							blue = *buf_p++;
							green = *buf_p++;
							red = *buf_p++;
							alphabyte = *buf_p++;
							*pixbuf++ = red;
							*pixbuf++ = green;
							*pixbuf++ = blue;
							*pixbuf++ = alphabyte;
							break;
				}
			}
		}
	}
	else if (targa_header.image_type==10) {   // Runlength encoded RGB images
		unsigned char red,green,blue,alphabyte,packetHeader,packetSize,j;
		for(row=rows-1; row>=0; row--) {
			pixbuf = targa_rgba + row*columns*4;
			for(column=0; column<columns; ) {
				packetHeader= *buf_p++;
				packetSize = 1 + (packetHeader & 0x7f);
				if (packetHeader & 0x80) {        // run-length packet
					switch (targa_header.pixel_size) {
						case 24:
								blue = *buf_p++;
								green = *buf_p++;
								red = *buf_p++;
								alphabyte = 255;
								break;
						case 32:
								blue = *buf_p++;
								green = *buf_p++;
								red = *buf_p++;
								alphabyte = *buf_p++;
								break;
					}
	
					for(j=0;j<packetSize;j++) {
						*pixbuf++=red;
						*pixbuf++=green;
						*pixbuf++=blue;
						*pixbuf++=alphabyte;
						column++;
						if (column==columns) { // run spans across rows
							column=0;
							if (row>0)
								row--;
							else
								goto breakOut;
							pixbuf = targa_rgba + row*columns*4;
						}
					}
				}
				else {                            // non run-length packet
					for(j=0;j<packetSize;j++) {
						switch (targa_header.pixel_size) {
							case 24:
									blue = *buf_p++;
									green = *buf_p++;
									red = *buf_p++;
									*pixbuf++ = red;
									*pixbuf++ = green;
									*pixbuf++ = blue;
									*pixbuf++ = 255;
									break;
							case 32:
									blue = *buf_p++;
									green = *buf_p++;
									red = *buf_p++;
									alphabyte = *buf_p++;
									*pixbuf++ = red;
									*pixbuf++ = green;
									*pixbuf++ = blue;
									*pixbuf++ = alphabyte;
									break;
						}
						column++;
						if (column==columns) { // pixel packet run spans across rows
							column=0;
							if (row>0)
								row--;
							else
								goto breakOut;
							pixbuf = targa_rgba + row*columns*4;
						}						
					}
				}
			}
			breakOut:;
		}
	}

	gl_rmain.ri.FS_FreeFile (buffer);
}


/*
====================================================================

IMAGE FLOOD FILLING

====================================================================
*/


/*
=================
Mod_FloodFillSkin

Fill background pixels so mipmapping doesn't have haloes
=================
*/

typedef struct
{
	short		x, y;
} floodfill_t;

// must be a power of 2
#define FLOODFILL_FIFO_SIZE 0x1000
#define FLOODFILL_FIFO_MASK (FLOODFILL_FIFO_SIZE - 1)

#define FLOODFILL_STEP( off, dx, dy ) \
{ \
	if (pos[off] == fillcolor) \
	{ \
		pos[off] = 255; \
		fifo[inpt].x = x + (dx), fifo[inpt].y = y + (dy); \
		inpt = (inpt + 1) & FLOODFILL_FIFO_MASK; \
	} \
	else if (pos[off] != 255) fdc = pos[off]; \
}

void R_FloodFillSkin( byte *skin, int skinwidth, int skinheight )
{
	byte				fillcolor = *skin; // assume this is the pixel to fill
	floodfill_t			fifo[FLOODFILL_FIFO_SIZE];
	int					inpt = 0, outpt = 0;
	int					filledcolor = -1;
	int					i;

	if (filledcolor == -1)
	{
		filledcolor = 0;
		// attempt to find opaque black
		for (i = 0; i < 256; ++i)
			if (d_8to24table[i] == (255 << 0)) // alpha 1.0
			{
				filledcolor = i;
				break;
			}
	}

	// can't fill to filled color or to transparent color (used as visited marker)
	if ((fillcolor == filledcolor) || (fillcolor == 255))
	{
		//printf( "not filling skin from %d to %d\n", fillcolor, filledcolor );
		return;
	}

	fifo[inpt].x = 0, fifo[inpt].y = 0;
	inpt = (inpt + 1) & FLOODFILL_FIFO_MASK;

	while (outpt != inpt)
	{
		int			x = fifo[outpt].x, y = fifo[outpt].y;
		int			fdc = filledcolor;
		byte		*pos = &skin[x + skinwidth * y];

		outpt = (outpt + 1) & FLOODFILL_FIFO_MASK;

		if (x > 0)				FLOODFILL_STEP( -1, -1, 0 );
		if (x < skinwidth - 1)	FLOODFILL_STEP( 1, 1, 0 );
		if (y > 0)				FLOODFILL_STEP( -skinwidth, 0, -1 );
		if (y < skinheight - 1)	FLOODFILL_STEP( skinwidth, 0, 1 );
		skin[x + skinwidth * y] = fdc;
	}
}

//=======================================================


/*
================
GL_ResampleTexture
================
"""
def GL_ResampleTexture (inPic, inwidth, inheight, outwidth, outheight): #unsigned *, int, int, unsigned *, int, int

	"""
	int		i, j;
	unsigned	*inrow, *inrow2;
	unsigned	frac, fracstep;
	unsigned	p1[1024], p2[1024];
	byte		*pix1, *pix2, *pix3, *pix4;
	"""

	if inwidth*inheight*4 != len(inPic):
		raise ValueError("img parameters don't match buffer size")

	p1, p2 = [], []

	fracstep = inwidth * 0x10000 // outwidth

	frac = fracstep>>2
	for i in range(outwidth):
	
		p1.append(4*(frac>>16))
		frac += fracstep
	
	frac = 3*(fracstep>>2)
	for i in range(outwidth):
	
		p2.append(4*(frac>>16))
		frac += fracstep

	out = bytearray(outwidth*outheight*4)
	outCursor = 0
	for i in range(outheight):
	
		inrow = 4*inwidth*int(((i+0.25)*inheight/outheight))
		inrow2 = 4*inwidth*int(((i+0.75)*inheight/outheight))
		#frac = fracstep >> 1

		for j in range(outwidth):
		
			pix1 = inrow + p1[j]
			pix2 = inrow + p2[j]
			pix3 = inrow2 + p1[j]
			pix4 = inrow2 + p2[j]
			outPxOffset = outCursor + j*4
			out[outPxOffset+0] = (inPic[pix1+0] + inPic[pix2+0] + inPic[pix3+0] + inPic[pix4+0])>>2
			out[outPxOffset+1] = (inPic[pix1+1] + inPic[pix2+1] + inPic[pix3+1] + inPic[pix4+1])>>2
			out[outPxOffset+2] = (inPic[pix1+2] + inPic[pix2+2] + inPic[pix3+2] + inPic[pix4+2])>>2
			out[outPxOffset+3] = (inPic[pix1+3] + inPic[pix2+3] + inPic[pix3+3] + inPic[pix4+3])>>2
		
		outCursor += outwidth*4

	return out

"""
================
GL_LightScaleTexture

Scale up the pixel values in a texture to increase the
lighting range
================
"""
def GL_LightScaleTexture (inPic, inwidth, inheight, only_gamma ): #unsigned *, int, int, qboolean

	global gammatable, intensitytable

	if only_gamma:
	
		#int		i, c;
		#byte	*p;

		p = 0
		c = inwidth*inheight
		for i in range(c):
		
			inPic[p+0] = gammatable[inPic[p+0]]
			inPic[p+1] = gammatable[inPic[p+1]]
			inPic[p+2] = gammatable[inPic[p+2]]
			p+=4
	
	else:
	
		#int		i, c;
		#byte	*p;

		p = 0
		c = inwidth*inheight
		for i in range(c):
		
			inPic[p+0] = gammatable[intensitytable[inPic[p+0]]]
			inPic[p+1] = gammatable[intensitytable[inPic[p+1]]]
			inPic[p+2] = gammatable[intensitytable[inPic[p+2]]]
			p+=4
	


"""
================
GL_MipMap

Operates in place, quartering the size of the texture
================
"""
def GL_MipMap (pic, width, height): #byte *, int, int

	#int		i, j;
	#byte	*out;

	width <<=2
	height >>= 1
	c = 0
	out = 0
	for i in range(height):
	
		for j in range(0, width, 8):
		
			pic[out+0] = (pic[c+0] + pic[c+4] + pic[c+width+0] + pic[c+width+4])>>2
			pic[out+1] = (pic[c+1] + pic[c+5] + pic[c+width+1] + pic[c+width+5])>>2
			pic[out+2] = (pic[c+2] + pic[c+6] + pic[c+width+2] + pic[c+width+6])>>2
			pic[out+3] = (pic[c+3] + pic[c+7] + pic[c+width+3] + pic[c+width+7])>>2

			out += 4
			c += 8
		
		c += width
	


"""
===============
GL_Upload32

Returns has_alpha
===============
*/
void GL_BuildPalettedTexture( unsigned char *paletted_texture, unsigned char *scaled, int scaled_width, int scaled_height )
{
	int i;

	for ( i = 0; i < scaled_width * scaled_height; i++ )
	{
		unsigned int r, g, b, c;

		r = ( scaled[0] >> 3 ) & 31;
		g = ( scaled[1] >> 2 ) & 63;
		b = ( scaled[2] >> 3 ) & 31;

		c = r | ( g << 5 ) | ( b << 11 );

		paletted_texture[i] = gl_rmain.gl_state.d_16to8table[c];

		scaled += 4;
	}
}

int		upload_width, upload_height;
qboolean uploaded_paletted;
"""
def GL_Upload32 (data, width, height, mipmap): #unsigned *, int, int, qboolean (returns qboolean)

	scaledSize = 256*256
	"""
	int			samples;
	unsigned	scaled[256*256];
	unsigned char paletted_texture[256*256];
	int			scaled_width, scaled_height;
	int			i, c;
	byte		*scan;
	int comp;
	"""
	uploaded_paletted = False

	if width*height*4 != len(data):
		raise ValueError("img parameters don't match buffer size")

	# round to power of 2 pixels
	scaled_width = 1
	while scaled_width < width: scaled_width<<=1
	if gl_rmain.gl_round_down.value and scaled_width > width and mipmap:
		scaled_width >>= 1
	scaled_height = 1
	while scaled_height < height: scaled_height<<=1
	if gl_rmain.gl_round_down.value and scaled_height > height and mipmap:
		scaled_height >>= 1

	# let people sample down the world textures for speed
	if mipmap:
	
		scaled_width >>= int(gl_rmain.gl_picmip.value)
		scaled_height >>= int(gl_rmain.gl_picmip.value)
	
	# don't ever bother with >256 textures
	if scaled_width > 256:
		scaled_width = 256
	if scaled_height > 256:
		scaled_height = 256

	if scaled_width < 1:
		scaled_width = 1
	if scaled_height < 1:
		scaled_height = 1

	upload_width = scaled_width
	upload_height = scaled_height

	if scaled_width * scaled_height > scaledSize:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "GL_Upload32: too big")

	# scan the texture for any non-255 alpha
	c = width*height
	scan = 3
	samples = gl_solid_format
	for i in range(c):
	
		if data[scan] != 255:
		
			samples = gl_alpha_format
			break

		scan += 4
	
	
	if samples == gl_solid_format:
	    comp = gl_tex_solid_format
	elif samples == gl_alpha_format:
	    comp = gl_tex_alpha_format
	else:
	    gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL,
			   "Unknown number of texture components {}\n".format(
			   samples))
	    comp = samples
	
	"""
	#if 0
	if (mipmap)
		gluBuild2DMipmaps (GL_TEXTURE_2D, samples, width, height, GL_RGBA, GL_UNSIGNED_BYTE, trans);
	else if (scaled_width == width && scaled_height == height)
		qglTexImage2D (GL_TEXTURE_2D, 0, comp, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, trans);
	else
	{
		gluScaleImage (GL_RGBA, width, height, GL_UNSIGNED_BYTE, trans,
			scaled_width, scaled_height, GL_UNSIGNED_BYTE, scaled);
		qglTexImage2D (GL_TEXTURE_2D, 0, comp, scaled_width, scaled_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, scaled);
	}
	#else
	"""

	if scaled_width == width and scaled_height == height:
		
		if not mipmap:
		
			if qgl_linux.qglColorTableEXT and gl_rmain.gl_ext_palettedtexture.value and samples == gl_solid_format \
				and False: #FIXME Disable for now, reintroduce later in porting
			
				uploaded_paletted = True
				paletted_texture = GL_BuildPalettedTexture( data, scaled_width, scaled_height )
				GL.glTexImage2D( GL.GL_TEXTURE_2D,
							  0,
							  GL.GL_COLOR_INDEX8_EXT,
							  scaled_width,
							  scaled_height,
							  0,
							  GL.GL_COLOR_INDEX,
							  GL.GL_UNSIGNED_BYTE,
							  paletted_texture )
			
			else:
			
				GL.glTexImage2D (GL.GL_TEXTURE_2D, 0, comp, scaled_width, scaled_height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, data)
			
			GL_Upload32Finish(mipmap)
			has_alpha = samples == gl_alpha_format
			return has_alpha, upload_width, upload_height, uploaded_paletted

		else:
			scaled = data
	
	else:
		scaled = GL_ResampleTexture (data, width, height, scaled_width, scaled_height)

	GL_LightScaleTexture (scaled, scaled_width, scaled_height, not mipmap )

	if qgl_linux.qglColorTableEXT and gl_rmain.gl_ext_palettedtexture.value and samples == gl_solid_format \
		and False: #FIXME Disable for now, reintroduce later in porting
	
		uploaded_paletted = True
		GL_BuildPalettedTexture( paletted_texture, scaled, scaled_width, scaled_height )
		GL.glTexImage2D( GL.GL_TEXTURE_2D,
					  0,
					  GL.GL_COLOR_INDEX8_EXT,
					  scaled_width,
					  scaled_height,
					  0,
					  GL.GL_COLOR_INDEX,
					  GL.GL_UNSIGNED_BYTE,
					  paletted_texture )
	
	else:
	
		GL.glTexImage2D( GL.GL_TEXTURE_2D, 0, comp, scaled_width, scaled_height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, scaled )
	

	if mipmap:

		#int		miplevel;

		miplevel = 0
		while scaled_width > 1 or scaled_height > 1:
		
			GL_MipMap (scaled, scaled_width, scaled_height)
			scaled_width >>= 1
			scaled_height >>= 1
			if scaled_width < 1:
				scaled_width = 1
			if scaled_height < 1:
				scaled_height = 1
			miplevel+=1
			if qgl_linux.qglColorTableEXT and gl_rmain.gl_ext_palettedtexture.value and samples == gl_solid_format \
				and False: #FIXME Disable for now, reintroduce later in porting

				uploaded_paletted = True
				GL_BuildPalettedTexture( paletted_texture, scaled, scaled_width, scaled_height )
				GL.glTexImage2D( GL.GL_TEXTURE_2D,
							  miplevel,
							  GL.GL_COLOR_INDEX8_EXT,
							  scaled_width,
							  scaled_height,
							  0,
							  GL.GL_COLOR_INDEX,
							  GL.GL_UNSIGNED_BYTE,
							  paletted_texture )
			
			else:
			
				GL.glTexImage2D (GL.GL_TEXTURE_2D, miplevel, comp, scaled_width, scaled_height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, scaled);
			
	#endif #from original c code

	GL_Upload32Finish(mipmap)
	has_alpha = samples == gl_alpha_format
	return has_alpha, upload_width, upload_height, uploaded_paletted

def GL_Upload32Finish(mipmap):

	global gl_filter_min, gl_filter_max

	if mipmap:
	
		GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, gl_filter_min)
		GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, gl_filter_max)
	
	else:
	
		GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, gl_filter_max)
		GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, gl_filter_max)
	

"""
===============
GL_Upload8

Returns has_alpha
===============
*/
/*
static qboolean IsPowerOf2( int value )
{
	int i = 1;


	while ( 1 )
	{
		if ( value == i )
			return true;
		if ( i > value )
			return false;
		i <<= 1;
	}
}
*/
"""
def GL_Upload8 (data, width, height, mipmap, is_sky ): #byte *, int, int, qboolean, qboolean (returns qboolean)

	sizeTrans = 512*256
	#trans = []
	#for i in range(sizeTrans):
	#	trans.append(0)
	"""
	unsigned	trans[512*256];
	int			i, s;
	int			p;
	"""

	s = width*height

	if s > sizeTrans:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "GL_Upload8: too large")

	if ( qgl_linux.qglColorTableEXT and 
		 gl_rmain.gl_ext_palettedtexture.value and 
		 is_sky ):
	
		GL.glTexImage2D( GL.GL_TEXTURE_2D,
					  0,
					  GL.GL_COLOR_INDEX8_EXT,
					  width,
					  height,
					  0,
					  GL.GL_COLOR_INDEX,
					  GL.GL_UNSIGNED_BYTE,
					  data )

		GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, gl_filter_max)
		GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, gl_filter_max)
	
		return False, width, height, True #has_alpha, upload_width, upload_height, paletted

	else:
		trans = bytearray(s*4)

		for i in range (s):

			p = data[i]
			transOffset = i*4
			col = bytearray(d_8to24table[p])
			trans[transOffset+0] = col[0]
			trans[transOffset+1] = col[1]
			trans[transOffset+2] = col[2]
			trans[transOffset+3] = col[3]

			if p == 255:
				# transparent, so scan around for another color
				# to avoid alpha fringes
				# FIXME: do a full flood fill so mips work...
				if i > width and data[i-width] != 255:
					p = data[i-width]
				elif i < s-width and data[i+width] != 255:
					p = data[i+width]
				elif i > 0 and data[i-1] != 255:
					p = data[i-1]
				elif i < s-1 and data[i+1] != 255:
					p = data[i+1]
				else:
					p = 0
				# copy rgb components
				pcol = d_8to24table[p]
				trans[transOffset+0] = pcol[0]
				trans[transOffset+1] = pcol[1]
				trans[transOffset+2] = pcol[2]

			assert len(trans) == s*4

		return GL_Upload32 (trans, width, height, mipmap)


"""
================
GL_LoadPic

This is also used as an entry point for the generated r_notexture
================
"""
def GL_LoadPic (name, pic, width, height, imgType, bits): #char *, byte *, int, int, imagetype_t, int (returns image_t *)

	global gltextures, numgltextures, TEXNUM_IMAGES
	#image_t		*image;
	#int			i;

	# find a free image_t
	i = 0
	while i < numgltextures:
	
		image = gltextures[i]
		if image.texnum == 0:
			break
		i += 1
	
	if i == numgltextures:
	
		if numgltextures == MAX_GLTEXTURES:
			gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "MAX_GLTEXTURES")
		numgltextures+=1
	
	image = gltextures[i]

	if len(name) >= q_shared.MAX_QPATH:
		gl_rmain.ri.Sys_Error (q_shared.ERR_DROP, "Draw_LoadPic: \"{}\" is too long".format(name))
	image.name = name
	image.registration_sequence = gl_model.registration_sequence

	image.width = width
	image.height = height
	image.type = imgType

	if imgType == imagetype_t.it_skin and bits == 8:
		R_FloodFillSkin(pic, width, height)

	# load little pics into the scrap
	if (image.type == imagetype_t.it_pic and bits == 8
		and image.width < 64 and image.height < 64
		and False): #FIXME disabled for now, port later
	
		pass
		"""
		#int		x, y;
		#int		i, j, k;
		#int		texnum;

		texnum = Scrap_AllocBlock (image->width, image->height, &x, &y)
		if (texnum == -1)
			goto nonscrap
		scrap_dirty = true

		# copy the texels into the scrap block
		k = 0
		for (i=0 ; i<image->height ; i++)
			for (j=0 ; j<image->width ; j++, k++)
				scrap_texels[texnum][(y+i)*BLOCK_WIDTH + x + j] = pic[k]
		image->texnum = TEXNUM_SCRAPS + texnum
		image->scrap = true
		image->has_alpha = true
		image->sl = (x+0.01)/(float)BLOCK_WIDTH
		image->sh = (x+image->width-0.01)/(float)BLOCK_WIDTH
		image->tl = (y+0.01)/(float)BLOCK_WIDTH
		image->th = (y+image->height-0.01)/(float)BLOCK_WIDTH
		"""
	
	else:
	
		#nonscrap:
		image.scrap = False
		image.texnum = TEXNUM_IMAGES + i
		GL_Bind(image.texnum)

		if bits == 8:
			image.has_alpha, image.upload_width, image.upload_height, image.paletted = \
				GL_Upload8 (pic, width, height, (image.type != imagetype_t.it_pic and image.type != imagetype_t.it_sky), image.type == imagetype_t.it_sky )
		else:
			image.has_alpha, image.upload_width, image.upload_height, image.paletted = \
				GL_Upload32 (pic, width, height, (image.type != imagetype_t.it_pic and image.type != imagetype_t.it_sky) )

		image.sl = 0
		image.sh = 1
		image.tl = 0
		image.th = 1
	
	return image

"""
================
GL_LoadWal
================
"""
def GL_LoadWal (name): #char * (returns image_t *)
	pass
	"""
	miptex_t	*mt;
	int			width, height, ofs;
	image_t		*image;

	gl_rmain.ri.FS_LoadFile (name, (void **)&mt);
	if (!mt)
	{
		gl_rmain.ri.Con_Printf (q_shared.PRINT_ALL, "GL_FindImage: can't load %s\n", name);
		return r_notexture;
	}

	width = LittleLong (mt->width);
	height = LittleLong (mt->height);
	ofs = LittleLong (mt->offsets[0]);

	image = GL_LoadPic (name, (byte *)mt + ofs, width, height, it_wall, 8);

	gl_rmain.ri.FS_FreeFile ((void *)mt);

	return image;
}

/*
===============
GL_FindImage

Finds or loads the given image
===============
"""
def GL_FindImage (name, imgType): #char *, imagetype_t (returns image_t *)

	global numgltextures, gltextures

	"""
	image_t	*image;
	int		i, len;
	byte	*pic, *palette;
	int		width, height;
	"""

	if name is None:
		return None	##	gl_rmain.ri.Sys_Error (ERR_DROP, "GL_FindImage: NULL name");
	if len(name)<5:
		return None	##	gl_rmain.ri.Sys_Error (ERR_DROP, "GL_FindImage: bad name: %s", name);

	# look for it
	for i in range(numgltextures):
		image = gltextures[i]

		if name == image.name:
		
			image.registration_sequence = gl_model.registration_sequence
			return image

	#
	# load the pic from disk
	#
	if name[-4:] == ".pcx":
	
		pic, pal, width, height = LoadPCX (name)
		if pic is None:
			return None ## gl_rmain.ri.Sys_Error (ERR_DROP, "GL_FindImage: can't load %s", name);
		image = GL_LoadPic (name, pic, width, height, imgType, 8)
	
	elif name[-4:] == ".wal":
	
		image = GL_LoadWal (name)
	
	elif name[-4:] == ".tga":

		# use some help from pygame
		length, raw = gl_rmain.ri.FS_LoadFile (name)
		if raw is None:
		
			gl_rmain.ri.Con_Printf (q_shared.PRINT_DEVELOPER, "Bad tga file {}\n".format(name))
			return
		
		pgimg = pygame.image.load(io.BytesIO(raw), "x.tga")
		width, height = pgimg.get_size()
		pgpix = bytearray(pgimg.get_view("0"))
		image = GL_LoadPic (name, pgpix, width, height, imgType, 8)

		# this is the original quake 2 approach:
		#LoadTGA (name, &pic, &width, &height);
		#if (!pic)
		#	return None ## gl_rmain.ri.Sys_Error (ERR_DROP, "GL_FindImage: can't load %s", name);
		#image = GL_LoadPic (name, pic, width, height, type, 32);
	
	else:
		return None	##	gl_rmain.ri.Sys_Error (ERR_DROP, "GL_FindImage: bad extension on: %s", name)

	return image


"""
===============
R_RegisterSkin
===============
"""
def R_RegisterSkin (name): #char * (returns struct image_s *)

	return GL_FindImage (name, imagetype_t.it_skin)



"""
================
GL_FreeUnusedImages

Any image that was not touched on this registration sequence
will be freed.
================
*/
void GL_FreeUnusedImages (void)
{
	int		i;
	image_t	*image;

	// never free r_notexture or particle texture
	r_notexture->registration_sequence = registration_sequence;
	r_particletexture->registration_sequence = registration_sequence;

	for (i=0, image=gltextures ; i<numgltextures ; i++, image++)
	{
		if (image->registration_sequence == registration_sequence)
			continue;		// used this sequence
		if (!image->registration_sequence)
			continue;		// free image_t slot
		if (image->type == it_pic)
			continue;		// don't free pics
		// free it
		qglDeleteTextures (1, &image->texnum);
		memset (image, 0, sizeof(*image));
	}
}


/*
===============
Draw_GetPalette
===============
"""
def Draw_GetPalette ():

	"""
	int		i;
	int		r, g, b;
	unsigned	v;
	byte	*pic, *pal;
	int		width, height;
	"""

	# get the palette

	pic, pal, width, height = LoadPCX ("pics/colormap.pcx")
	if pal is None:
		gl_rmain.ri.Sys_Error (q_shared.ERR_FATAL, "Couldn't load pics/colormap.pcx")

	for i in range(256):
	
		r, g, b = struct.unpack("<BBB", pal[i*3:i*3+3])

		if i != 255:
			d_8to24table[i] = (r, g, b, 255)
		else:
			d_8to24table[i] = (r, g, b, 0) # 255 is transparent

	return 0

"""
===============
GL_InitImages
===============
"""
def GL_InitImages ():
	
	global gammatable, intensitytable
	"""
	int		i, j;
	float	g
	"""
	g = gl_rmain.vid_gamma.value

	gl_model.registration_sequence = 1
	
	# init intensity conversions
	intensity = gl_rmain.ri.Cvar_Get ("intensity", "2", 0)

	if intensity.value <= 1:
		gl_rmain.ri.Cvar_Set( "intensity", "1" )

	gl_rmain.gl_state.inverse_intensity = 1 / intensity.value

	Draw_GetPalette ()

	"""
	if ( qglColorTableEXT )
	{
		gl_rmain.ri.FS_LoadFile( "pics/16to8.dat", &gl_rmain.gl_state.d_16to8table );
		if ( !gl_rmain.gl_state.d_16to8table )
			gl_rmain.ri.Sys_Error( ERR_FATAL, "Couldn't load pics/16to8.pcx");
	}
	

	if ( gl_config.renderer & ( GL_RENDERER_VOODOO | GL_RENDERER_VOODOO2 ) )
	{
		g = 1.0F;
	}
	"""
	
	for i in range(256):
	
		if g == 1.0:
		
			gammatable[i] = i
		
		else:
		
			#float inf

			inf = 255 * math.pow ( (i+0.5)/255.5 , g ) + 0.5
			if inf < 0:
				inf = 0
			if inf > 255:
				inf = 255
			gammatable[i] = inf
		
	for i in range(256):
	
		j = int(i*intensity.value)
		if j > 255:
			j = 255
		intensitytable[i] = j
	
"""
===============
GL_ShutdownImages
===============
*/
void	GL_ShutdownImages (void)
{
	int		i;
	image_t	*image;

	for (i=0, image=gltextures ; i<numgltextures ; i++, image++)
	{
		if (!image->registration_sequence)
			continue;		// free image_t slot
		// free it
		qglDeleteTextures (1, &image->texnum);
		memset (image, 0, sizeof(*image));
	}
}
"""
