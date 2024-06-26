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

# snd_loc.h -- private sound functions

# !!! if this is changed, the asm code must change !!!
class portable_samplepair_t(object):

	def __init__(self):
		self.clear()

	def clear(self):
		self.left = 0 #int			
		self.right = 0 #int

class sfxcache_t(object):
	def __init__(self):
		self.length = None #int
		self.loopstart = None #int
		self.speed = None #int, not needed, because converted on load?
		self.width = None #int
		self.stereo = None #int
		self.data = None #byte[1], variable sized

class sfx_t(object):
	def __init__(self):

		self.clear()

	def __repr__(self):
		return "sfx_t ({})".format(self.name)

	def clear(self):

		self.name = None #char 		[MAX_QPATH]
		self.registration_sequence = None #int
		self.cache = None #sfxcache_t	*
		self.truename = None #char 		*

# a playsound_t will be generated by each call to S_StartSound,
# when the mixer reaches playsound->begin, the playsound will
# be assigned to a channel

class playsound_t(object):

	def __init__(self):
		#struct playsound_s	*prev, *next
		self.sfx = None #sfx_t		*
		self.volume = None #float		
		self.attenuation = None #float		
		self.entnum = None #int			
		self.entchannel = None #int			
		self.fixed_origin = None #qboolean, use origin field instead of entnum's origin
		self.origin = None #vec3_t		
		self.begin = None #unsigned, begin on this sample

	def __repr__(self):
		return "playsound_t ({}, {})".format(self.sfx, self.begin)

class dma_t(object):
	def __init__(self):

		self.channels = None #int			
		self.samples = None #int							 mono samples in buffer
		self.submission_chunk = None #int					 don't mix less than this #
		self.samplepos = None #int							 in mono samples
		self.samplebits = None #int			
		self.speed = None #int			
		self.buffer = None #byte		*

class channel_t(object):
	def __init__(self):
		self.chan = None			# pygame mixer channel
		self.clear()

	def clear(self):
		self.sfx = None				# sfx_t		*, sfx number
		self.leftvol = 0			# int, 0-255 volume
		self.rightvol = 0			# int, 0-255 volume
		self.end = 0				# int, end time in global paintsamples
		self.pos = 0				# int, sample position in sfx
		self.looping = 0			# int, where to loop, -1 = no looping OBSOLETE?
		self.entnum = 0				# int, to allow overriding a specific sound
		self.entchannel = 0			# int
		self.origin = np.zeros((3,), dtype=np.float32)			# vec3_t, only use if fixed_origin is set
		self.dist_mult = np.zeros((3,), dtype=np.float32)		# vec_t, distance multiplier (attenuation/clipK)
		self.master_vol = 0			# int, 0-255 master volume
		self.fixed_origin = False	# qboolean, use origin instead of fetching entnum's origin
		self.autosound = False		# qboolean, from an entity->sound, cleared each frame

"""
typedef struct
{
	int			rate;
	int			width;
	int			channels;
	int			loopstart;
	int			samples;
	int			dataofs;		// chunk starts this many bytes from file start
} wavinfo_t;


/*
====================================================================

  SYSTEM SPECIFIC FUNCTIONS

====================================================================
*/

// initializes cycling through a DMA buffer and returns information on it
qboolean SNDDMA_Init(void);

// gets the current DMA position
int		SNDDMA_GetDMAPos(void);

// shutdown the DMA xfer.
void	SNDDMA_Shutdown(void);

void	SNDDMA_BeginPainting (void);

void	SNDDMA_Submit(void);

//====================================================================
"""
MAX_CHANNELS = 32
"""
extern	channel_t   channels[MAX_CHANNELS];

extern	int		paintedtime;
extern	int		s_rawend;
extern	vec3_t	listener_origin;
extern	vec3_t	listener_forward;
extern	vec3_t	listener_right;
extern	vec3_t	listener_up;
extern	dma_t	dma;
extern	playsound_t	s_pendingplays;
"""
MAX_RAW_SAMPLES = 8192
#extern	portable_samplepair_t	s_rawsamples[MAX_RAW_SAMPLES];
"""
extern cvar_t	*s_volume;
extern cvar_t	*s_nosound;
extern cvar_t	*s_loadas8bit;
extern cvar_t	*s_khz;
extern cvar_t	*s_show;
extern cvar_t	*s_mixahead;
extern cvar_t	*s_testsound;
extern cvar_t	*s_primary;

wavinfo_t GetWavinfo (char *name, byte *wav, int wavlength);

void S_InitScaletable (void);

sfxcache_t *S_LoadSound (sfx_t *s);

void S_IssuePlaysound (playsound_t *ps);

void S_PaintChannels(int endtime);

// picks a channel based on priorities, empty slots, number of channels
channel_t *S_PickChannel(int entnum, int entchannel);

// spatializes a channel
void S_Spatialize(channel_t *ch);
"""
