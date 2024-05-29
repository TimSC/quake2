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
import os
from client import cl_main, cl_scrn, client
from qcommon import files, cvar, common, qcommon
from game import q_shared
from linux import q_shlinux
"""
#include "client.h"

typedef struct
{
	byte	*data;
	int		count;
} cblock_t;
"""
class cinematics_t(object):
	def __init__(self):

		self.restart_sound=False # qboolean
		self.s_rate = None #int
		self.s_width = None #int
		self.s_channels = None #int

		self.width = None #int
		self.height = None #int

		self.pic = None #byte *
		self.pic_pending = None #byte *

		# order 1 huffman stuff
		self.hnodes1 = None #int * // [256][256][2]
		self.numhnodes1 = None #int[256]

		self.h_used = None #int[512]
		self.h_count = None #int[512]


cin = cinematics_t()

"""
=================================================================

PCX LOADING

=================================================================
"""


"""
==============
SCR_LoadPCX
==============
*/
void SCR_LoadPCX (char *filename, byte **pic, byte **palette, int *width, int *height)
{
	byte	*raw;
	pcx_t	*pcx;
	int		x, y;
	int		len;
	int		dataByte, runLength;
	byte	*out, *pix;

	*pic = NULL;

	//
	// load the file
	//
	len = FS_LoadFile (filename, (void **)&raw);
	if (!raw)
		return;	// Com_Printf ("Bad pcx file %s\n", filename);

	//
	// parse the PCX file
	//
	pcx = (pcx_t *)raw;
	raw = &pcx->data;

	if (pcx->manufacturer != 0x0a
		|| pcx->version != 5
		|| pcx->encoding != 1
		|| pcx->bits_per_pixel != 8
		|| pcx->xmax >= 640
		|| pcx->ymax >= 480)
	{
		Com_Printf ("Bad pcx file %s\n", filename);
		return;
	}

	out = Z_Malloc ( (pcx->ymax+1) * (pcx->xmax+1) );

	*pic = out;

	pix = out;

	if (palette)
	{
		*palette = Z_Malloc(768);
		memcpy (*palette, (byte *)pcx + len - 768, 768);
	}

	if (width)
		*width = pcx->xmax+1;
	if (height)
		*height = pcx->ymax+1;

	for (y=0 ; y<=pcx->ymax ; y++, pix += pcx->xmax+1)
	{
		for (x=0 ; x<=pcx->xmax ; )
		{
			dataByte = *raw++;

			if((dataByte & 0xC0) == 0xC0)
			{
				runLength = dataByte & 0x3F;
				dataByte = *raw++;
			}
			else
				runLength = 1;

			while(runLength-- > 0)
				pix[x++] = dataByte;
		}

	}

	if ( raw - (byte *)pcx > len)
	{
		Com_Printf ("PCX file %s was malformed", filename);
		Z_Free (*pic);
		*pic = NULL;
	}

	FS_FreeFile (pcx);
}

//=============================================================

/*
==================
SCR_StopCinematic
==================
"""
def SCR_StopCinematic ():
	
	global cin
	
	cl_main.cl.cinematictime = 0	# done
	"""
	if (cin.pic)
	{
		Z_Free (cin.pic);
		cin.pic = NULL;
	}
	if (cin.pic_pending)
	{
		Z_Free (cin.pic_pending);
		cin.pic_pending = NULL;
	}
	if (cl_main.cl.cinematicpalette_active)
	{
		re.CinematicSetPalette(NULL);
		cl_main.cl.cinematicpalette_active = false;
	}
	if (cl_main.cl.cinematic_file)
	{
		fclose (cl_main.cl.cinematic_file);
		cl_main.cl.cinematic_file = NULL;
	}
	if (cin.hnodes1)
	{
		Z_Free (cin.hnodes1);
		cin.hnodes1 = NULL;
	}

	// switch back down to 11 khz sound if necessary
	if (cin.restart_sound)
	{
		cin.restart_sound = false;
		CL_Snd_Restart_f ();
	}

}

/*
====================
SCR_FinishCinematic

Called when either the cinematic completes, or it is aborted
====================
"""
def SCR_FinishCinematic ():

	# tell the server to advance to the next map / cinematic
	common.MSG_WriteByte (cl_main.cls.netchan.message, qcommon.clc_ops_e.clc_stringcmd.value.to_bytes(1, 'big'))
	common.SZ_Print (cl_main.cls.netchan.message, "nextserver {}\n".format(cl_main.cl.servercount))


"""
//==========================================================================

/*
==================
SmallestNode1
==================
"""
def	SmallestNode1 (numhnodes): #int

	#int		i;
	#int		best, bestnode;

	best = 99999999
	bestnode = -1
	for i in range(numhnodes):
	
		if cin.h_used[i]:
			continue
		if not cin.h_count[i]:
			continue
		if cin.h_count[i] < best:
		
			best = cin.h_count[i]
			bestnode = i

	if bestnode == -1:
		return -1

	cin.h_used[bestnode] = True
	return bestnode



"""
==================
Huff1TableInit

Reads the 64k counts table and initializes the node trees
==================
"""
def Huff1TableInit ():

	global cin
	"""
	int		prev;
	int		j;
	int		*node, *nodebase;
	byte	counts[256];
	int		numhnodes;
	"""

	cin.hnodes1 = [0] * (256*256*2*4)
	cin.numhnodes1 = [0]*256 #int[256]

	for prev in range(256):
	
		cin.h_count = [0]*512
		cin.h_used = [0]*512

		# read a row of counts
		counts = files.FS_Read (256, cl_main.cl.cinematic_file)
		for j in range(256):
			cin.h_count[j] = counts[j]

		# build the nodes
		numhnodes = 256
		nodebase = prev * 256 * 2

		while numhnodes != 511:
		
			node = nodebase + (numhnodes - 256) * 2

			# pick two lowest counts
			v1 = SmallestNode1(numhnodes)
			cin.hnodes1[node+0] = v1
			if v1 == -1:
				break	# no more

			v2 = SmallestNode1(numhnodes)
			cin.hnodes1[node+1] = v2
			if v2 == -1:
				break

			cin.h_count[numhnodes] = cin.h_count[v1] + cin.h_count[v2]
			numhnodes+=1
		

		cin.numhnodes1[prev] = numhnodes-1
	
"""
==================
Huff1Decompress
==================
*/
cblock_t Huff1Decompress (cblock_t in)
{
	byte		*input;
	byte		*out_p;
	int			nodenum;
	int			count;
	cblock_t	out;
	int			inbyte;
	int			*hnodes, *hnodesbase;
//int		i;

	// get decompressed count
	count = in.data[0] + (in.data[1]<<8) + (in.data[2]<<16) + (in.data[3]<<24);
	input = in.data + 4;
	out_p = out.data = Z_Malloc (count);

	// read bits

	hnodesbase = cin.hnodes1 - 256*2;	// nodes 0-255 aren't stored

	hnodes = hnodesbase;
	nodenum = cin.numhnodes1[0];
	while (count)
	{
		inbyte = *input++;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
		//-----------
		if (nodenum < 256)
		{
			hnodes = hnodesbase + (nodenum<<9);
			*out_p++ = nodenum;
			if (!--count)
				break;
			nodenum = cin.numhnodes1[nodenum];
		}
		nodenum = hnodes[nodenum*2 + (inbyte&1)];
		inbyte >>=1;
	}

	if (input - in.data != in.count && input - in.data != in.count+1)
	{
		Com_Printf ("Decompression overread by %i", (input - in.data) - in.count);
	}
	out.count = out_p - out.data;

	return out;
}

/*
==================
SCR_ReadNextFrame
==================
"""
def SCR_ReadNextFrame (): #byte *

	print ("SCR_ReadNextFrame")
	"""
	int		r;
	int		command;
	byte	samples[22050/14*4];
	byte	compressed[0x20000];
	int		size;
	byte	*pic;
	cblock_t	in, huf1;
	int		start, end, count;

	// read the next frame
	r = fread (&command, 4, 1, cl_main.cl.cinematic_file);
	if (r == 0)		// we'll give it one more chance
		r = fread (&command, 4, 1, cl_main.cl.cinematic_file);

	if (r != 1)
		return NULL;
	command = LittleLong(command);
	if (command == 2)
		return NULL;	// last frame marker

	if (command == 1)
	{	// read palette
		FS_Read (cl_main.cl.cinematicpalette, sizeof(cl_main.cl.cinematicpalette), cl_main.cl.cinematic_file);
		cl_main.cl.cinematicpalette_active=0;	// dubious....  exposes an edge case
	}

	// decompress the next frame
	FS_Read (&size, 4, cl_main.cl.cinematic_file);
	size = LittleLong(size);
	if (size > sizeof(compressed) || size < 1)
		Com_Error (ERR_DROP, "Bad compressed frame size");
	FS_Read (compressed, size, cl_main.cl.cinematic_file);

	// read sound
	start = cl_main.cl.cinematicframe*cin.s_rate/14;
	end = (cl_main.cl.cinematicframe+1)*cin.s_rate/14;
	count = end - start;

	FS_Read (samples, count*cin.s_width*cin.s_channels, cl_main.cl.cinematic_file);

	S_RawSamples (count, cin.s_rate, cin.s_width, cin.s_channels, samples);

	in.data = compressed;
	in.count = size;

	huf1 = Huff1Decompress (in);

	pic = huf1.data;

	cl_main.cl.cinematicframe++;

	return pic;
}


/*
==================
SCR_RunCinematic

==================
"""
def SCR_RunCinematic ():

	global cin
	#int		frame;

	if cl_main.cl.cinematictime <= 0:
	
		SCR_StopCinematic ()
		return
	
	"""

	if (cl_main.cl.cinematicframe == -1)
		return;		// static image

	if (cl_main.cls.key_dest != key_game)
	{	// pause if menu or console is up
		cl_main.cl.cinematictime = cl_main.cls.realtime - cl_main.cl.cinematicframe*1000/14;
		return;
	}

	frame = (cl_main.cls.realtime - cl_main.cl.cinematictime)*14.0/1000;
	if (frame <= cl_main.cl.cinematicframe)
		return;
	if (frame > cl_main.cl.cinematicframe+1)
	{
		Com_Printf ("Dropped frame: %i > %i\n", frame, cl_main.cl.cinematicframe+1);
		cl_main.cl.cinematictime = cl_main.cls.realtime - cl_main.cl.cinematicframe*1000/14;
	}
	if (cin.pic)
		Z_Free (cin.pic);
	"""
	cin.pic = cin.pic_pending
	cin.pic_pending = None
	cin.pic_pending = SCR_ReadNextFrame ()

	cin.pic_pending = False
	if not cin.pic_pending:
	
		SCR_StopCinematic ()
		SCR_FinishCinematic ()
		cl_main.cl.cinematictime = 1	# hack to get the black screen behind loading
		cl_scrn.SCR_BeginLoadingPlaque ()
		cl_main.cl.cinematictime = 0
		return
	


"""
==================
SCR_DrawCinematic

Returns true if a cinematic is active, meaning the view rendering
should be skipped
==================
*/
qboolean SCR_DrawCinematic (void)
{
	if (cl_main.cl.cinematictime <= 0)
	{
		return false;
	}

	if (cl_main.cls.key_dest == key_menu)
	{	// blank screen and pause if menu is up
		re.CinematicSetPalette(NULL);
		cl_main.cl.cinematicpalette_active = false;
		return true;
	}

	if (!cl_main.cl.cinematicpalette_active)
	{
		re.CinematicSetPalette(cl_main.cl.cinematicpalette);
		cl_main.cl.cinematicpalette_active = true;
	}

	if (!cin.pic)
		return true;

	re.DrawStretchRaw (0, 0, viddef.width, viddef.height,
		cin.width, cin.height, cin.pic);

	return true;
}

/*
==================
SCR_PlayCinematic

==================
"""
def SCR_PlayCinematic (arg): # char *

	global cin
	"""
	int		width, height;
	byte	*palette;
	char	name[MAX_OSPATH], *dot;
	int		old_khz;
	"""
	# make sure CD isn't playing music
	#CDAudio_Stop()

	cl_main.cl.cinematicframe = 0
	#dot = strstr (arg, ".")
	arg_split = os.path.splitext(arg)
	if len(arg_split) >= 2:
		dot = arg_split[1]
	else:
		dot = None

	
	if dot == ".pcx":
		"""
		# static pcx image
		Com_sprintf (name, sizeof(name), "pics/%s", arg)
		cl_scrn.SCR_LoadPCX (name, &cin.pic, &palette, &cin.width, &cin.height)
		cl_main.cl.cinematicframe = -1
		cl_main.cl.cinematictime = 1
		cl_scrn.SCR_EndLoadingPlaque ()
		cl_main.cls.state = ca_active
		if !cin.pic:
		
			Com_Printf ("%s not found.\n", name)
			cl_main.cl.cinematictime = 0
		
		else:
		
			memcpy (cl_main.cl.cinematicpalette, palette, sizeof(cl_main.cl.cinematicpalette))
			Z_Free (palette)
			"""
		return


	name = "video/{}".format(arg)
	file_length, cl_main.cl.cinematic_file = files.FS_FOpenFile (name)
	if cl_main.cl.cinematic_file is None:
	
#		Com_Error (ERR_DROP, "Cinematic %s not found.\n", name);
		SCR_FinishCinematic ()
		cl_main.cl.cinematictime = 0	# done
		return
	

	cl_scrn.SCR_EndLoadingPlaque ()

	cl_main.cls.state = client.connstate_t.ca_active

	width = files.FS_Read (4, cl_main.cl.cinematic_file)
	height = files.FS_Read (4, cl_main.cl.cinematic_file)
	cin.width = q_shared.LittleLong(width)
	cin.height = q_shared.LittleLong(height)

	cin.s_rate = files.FS_Read (4, cl_main.cl.cinematic_file)
	cin.s_rate = q_shared.LittleLong(cin.s_rate)
	cin.s_width = files.FS_Read (4, cl_main.cl.cinematic_file)
	cin.s_width = q_shared.LittleLong(cin.s_width)
	cin.s_channels = files.FS_Read (4, cl_main.cl.cinematic_file)
	cin.s_channels = q_shared.LittleLong(cin.s_channels)

	Huff1TableInit ()

	# switch up to 22 khz sound if necessary
	old_khz = cvar.Cvar_VariableValue ("s_khz")
	if old_khz != cin.s_rate//1000:
	
		cin.restart_sound = True
		cvar.Cvar_SetValue ("s_khz", cin.s_rate//1000)
		cl_main.CL_Snd_Restart_f ()
		cvar.Cvar_SetValue ("s_khz", old_khz)
	

	cl_main.cl.cinematicframe = 0
	cin.pic = SCR_ReadNextFrame ()
	cl_main.cl.cinematictime = q_shlinux.Sys_Milliseconds ()

