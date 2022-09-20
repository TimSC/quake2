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
from qcommon import cmd, cvar, common
from game import q_shared
from linux import snd_linux, q_shlinux
from client import snd_mix, snd_loc, snd_mem, cl_main
import pygame
"""
// snd_dma.c -- main control for any streaming sound output device

#include "client.h"
#include "snd_loc.h"

void S_Play(void);
void S_SoundList(void);
void S_Update_();
void S_StopAllSounds(void);


// =======================================================================
// Internal sound data & structures
// =======================================================================

// only begin attenuating sound volumes when outside the FULLVOLUME range
#define		SOUND_FULLVOLUME	80

#define		SOUND_LOOPATTENUATE	0.003
"""
s_registration_sequence = 0 #int
channels = [] #channel_t[]
for i in range(snd_loc.MAX_CHANNELS):
	channels.append(snd_loc.channel_t())

snd_initialized = False #qboolean
sound_started = False #int

dma = snd_loc.dma_t()
"""
vec3_t		listener_origin;
vec3_t		listener_forward;
vec3_t		listener_right;
vec3_t		listener_up;

"""
s_registering = False #qboolean

soundtime = None	# int, sample PAIRS
paintedtime = None 	# int, sample PAIRS

# during registration it is possible to have more sounds
# than could actually be referenced during gameplay,
# because we don't want to free anything until we are
# sure we won't need it.
MAX_SFX = (q_shared.MAX_SOUNDS*2)
known_sfx = [] #sfx_t [MAX_SFX];
for i in range(MAX_SFX):
	known_sfx.append(snd_loc.sfx_t())

num_sfx = None #int			
"""
#define		MAX_PLAYSOUNDS	128
playsound_t	s_playsounds[MAX_PLAYSOUNDS];
playsound_t	s_freeplays;
"""
s_pendingplays = [] #playsound_t (linked list)
s_beginofs = 0 #int

s_volume = None #cvar_t		*
s_testsound = None #cvar_t		*
s_loadas8bit = None #cvar_t		*
s_khz = None #cvar_t		*
s_show = None #cvar_t		*
s_mixahead = None #cvar_t		*
s_primary = None #cvar_t		*

"""

int		s_rawend;
portable_samplepair_t	s_rawsamples[MAX_RAW_SAMPLES];


// ====================================================================
// User-setable variables
// ====================================================================

"""
def S_SoundInfo_f():

	global sound_started
	pass
	"""
	if (!sound_started)
	{
		Com_Printf ("sound system not started\n");
		return;
	}
	
	Com_Printf("%5d stereo\n", dma.channels - 1);
	Com_Printf("%5d samples\n", dma.samples);
	Com_Printf("%5d samplepos\n", dma.samplepos);
	Com_Printf("%5d samplebits\n", dma.samplebits);
	Com_Printf("%5d submission_chunk\n", dma.submission_chunk);
	Com_Printf("%5d speed\n", dma.speed);
	Com_Printf("0x%x dma buffer\n", dma.buffer);

/*
================
S_Init
================
"""
def S_Init ():

	global s_volume, s_testsound, s_loadas8bit, s_khz, s_show, s_mixahead, s_primary
	global sound_started, num_sfx, soundtime, paintedtime, channels

	#cvar_t	*cv;

	common.Com_Printf("\n------- sound initialization -------\n")

	cv = cvar.Cvar_Get ("s_initsound", "1", 0)
	if not cv.value:
		common.Com_Printf ("not initializing.\n")
	else:
	
		s_volume = cvar.Cvar_Get ("s_volume", "0.7", q_shared.CVAR_ARCHIVE)
		s_khz = cvar.Cvar_Get ("s_khz", "11", q_shared.CVAR_ARCHIVE)
		s_loadas8bit = cvar.Cvar_Get ("s_loadas8bit", "1", q_shared.CVAR_ARCHIVE)
		s_mixahead = cvar.Cvar_Get ("s_mixahead", "0.2", q_shared.CVAR_ARCHIVE)
		s_show = cvar.Cvar_Get ("s_show", "0", 0)
		s_testsound = cvar.Cvar_Get ("s_testsound", "0", 0)
		s_primary = cvar.Cvar_Get ("s_primary", "0", q_shared.CVAR_ARCHIVE)	# win32 specific

		cmd.Cmd_AddCommand("play", S_Play)
		cmd.Cmd_AddCommand("stopsound", S_StopAllSounds)
		cmd.Cmd_AddCommand("soundlist", S_SoundList)
		cmd.Cmd_AddCommand("soundinfo", S_SoundInfo_f)
		
		if not snd_linux.SNDDMA_Init():
			return

		snd_mix.S_InitScaletable ()

		sound_started = 1
		num_sfx = 0

		soundtime = 0
		paintedtime = 0

		common.Com_Printf ("sound sampling rate: {}\n".format(dma.speed))

		pygame.mixer.set_num_channels(snd_loc.MAX_CHANNELS)

		maxChan = min(snd_loc.MAX_CHANNELS, pygame.mixer.get_num_channels())
		for ch_idx in range(maxChan):
			channels[ch_idx].chan = pygame.mixer.Channel(ch_idx)
		
		S_StopAllSounds ()
	
	common.Com_Printf("------------------------------------\n")


"""
// =======================================================================
// Shutdown sound engine
// =======================================================================

void S_Shutdown(void)
{
	int		i;
	sfx_t	*sfx;

	if (!sound_started)
		return;

	SNDDMA_Shutdown();

	sound_started = 0;

	Cmd_RemoveCommand("play");
	Cmd_RemoveCommand("stopsound");
	Cmd_RemoveCommand("soundlist");
	Cmd_RemoveCommand("soundinfo");

	// free all sounds
	for (i=0, sfx=known_sfx ; i < num_sfx ; i++,sfx++)
	{
		if (!sfx->name[0])
			continue;
		if (sfx->cache)
			Z_Free (sfx->cache);
		memset (sfx, 0, sizeof(*sfx));
	}

	num_sfx = 0;
}


// =======================================================================
// Load a sound
// =======================================================================

/*
==================
S_FindName

==================
"""
def S_FindName (name, create): #char *, qboolean (returns sfx_t *)

	global num_sfx, known_sfx
	#int		i;
	#sfx_t	*sfx;

	if name is None:
		common.Com_Error (q_shared.ERR_FATAL, "S_FindName: NULL\n")
	if len(name) == 0:
		common.Com_Error (q_shared.ERR_FATAL, "S_FindName: empty name\n")

	if len(name) >= q_shared.MAX_QPATH:
		common.Com_Error (q_shared.ERR_FATAL, "Sound name too long: {}".format(name))

	# see if already loaded
	for i in range(num_sfx):
		if known_sfx[i].name == name:
			return known_sfx[i]
		
	if not create:
		return None

	# find a free sfx
	i = 0
	while i < num_sfx:
		if known_sfx[i].name is None:
			##registration_sequence < s_registration_sequence)
			break;
		i+=1

	if i == num_sfx:
	
		if num_sfx == MAX_SFX:
			common.Com_Error (q_shared.ERR_FATAL, "S_FindName: out of sfx_t")
		num_sfx+=1
	
	sfx = known_sfx[i]
	sfx.name = name
	sfx.registration_sequence = s_registration_sequence
	sfx.cache = None
	sfx.truename = None
	
	return sfx;

"""

/*
==================
S_AliasName

==================
*/
sfx_t *S_AliasName (char *aliasname, char *truename)
{
	sfx_t	*sfx;
	char	*s;
	int		i;

	s = Z_Malloc (MAX_QPATH);
	strcpy (s, truename);

	// find a free sfx
	for (i=0 ; i < num_sfx ; i++)
		if (!known_sfx[i].name[0])
			break;

	if (i == num_sfx)
	{
		if (num_sfx == MAX_SFX)
			Com_Error (ERR_FATAL, "S_FindName: out of sfx_t");
		num_sfx+=1
	}
	
	sfx = &known_sfx[i];
	memset (sfx, 0, sizeof(*sfx));
	strcpy (sfx->name, aliasname);
	sfx->registration_sequence = s_registration_sequence;
	sfx->truename = s;

	return sfx;
}


/*
=====================
S_BeginRegistration

=====================
*/
void S_BeginRegistration (void)
{
	s_registration_sequence++;
	s_registering = true;
}

/*
==================
S_RegisterSound

==================
"""
def S_RegisterSound (name): #char * (returns sfx_t *)

	global sound_started
	#sfx_t	*sfx;

	if not sound_started:
		return None

	sfx = S_FindName (name, True)
	sfx.registration_sequence = s_registration_sequence

	if not s_registering:
		snd_mem.S_LoadSound (sfx)

	return sfx


"""
=====================
S_EndRegistration

=====================
*/
void S_EndRegistration (void)
{
	int		i;
	sfx_t	*sfx;
	int		size;

	// free any sounds not from this registration sequence
	for (i=0, sfx=known_sfx ; i < num_sfx ; i++,sfx++)
	{
		if (!sfx->name[0])
			continue;
		if (sfx->registration_sequence != s_registration_sequence)
		{	// don't need this sound
			if (sfx->cache)	// it is possible to have a leftover
				Z_Free (sfx->cache);	// from a server that didn't finish loading
			memset (sfx, 0, sizeof(*sfx));
		}
		else
		{	// make sure it is paged in
			if (sfx->cache)
			{
				size = sfx->cache->length*sfx->cache->width;
				Com_PageInMemory ((byte *)sfx->cache, size);
			}
		}

	}

	// load everything in
	for (i=0, sfx=known_sfx ; i < num_sfx ; i++,sfx++)
	{
		if (!sfx->name[0])
			continue;
		S_LoadSound (sfx);
	}

	s_registering = false;
}


//=============================================================================

/*
=================
S_PickChannel
=================
"""
def S_PickChannel(entnum, entchannel): #int, int (returns channel_t *)

	"""
	int			ch_idx;
	int			first_to_die;
	int			life_left;
	channel_t	*ch;
	"""
	global channels

	if entchannel<0:
		common.Com_Error (ERR_DROP, "S_PickChannel: entchannel<0")

	# Check for replacement sound, or find the best one to replace
	first_to_die = -1
	life_left = 0x7fffffff

	for ch_idx in range(snd_loc.MAX_CHANNELS):
	
		ch = channels[ch_idx]
		if ch.chan is None: continue
	
		if (entchannel != 0		# channel 0 never overrides
			and ch.entnum == entnum
			and ch.entchannel == entchannel):
		
			# always override sound from same entity
			first_to_die = ch_idx
			break
			
		# don't let monster sounds override player sounds
		if ch.entnum == cl_main.cl.playernum+1 and entnum != cl_main.cl.playernum+1 and ch.sfx:
			continue

		if ch.end - paintedtime < life_left:
		
			life_left = ch.end - paintedtime
			first_to_die = ch_idx
   
	if first_to_die == -1:
		return None

	ch = channels[first_to_die]
	ch.clear()

	return ch

"""
=================
S_SpatializeOrigin

Used for spatializing channels and autosounds
=================
*/
void S_SpatializeOrigin (vec3_t origin, float master_vol, float dist_mult, int *left_vol, int *right_vol)
{
	vec_t		dot;
	vec_t		dist;
	vec_t		lscale, rscale, scale;
	vec3_t		source_vec;

	if (cls.state != ca_active)
	{
		*left_vol = *right_vol = 255;
		return;
	}

// calculate stereo seperation and distance attenuation
	VectorSubtract(origin, listener_origin, source_vec);

	dist = VectorNormalize(source_vec);
	dist -= SOUND_FULLVOLUME;
	if (dist < 0)
		dist = 0;			// close enough to be at full volume
	dist *= dist_mult;		// different attenuation levels
	
	dot = DotProduct(listener_right, source_vec);

	if (dma.channels == 1 || !dist_mult)
	{ // no attenuation = no spatialization
		rscale = 1.0;
		lscale = 1.0;
	}
	else
	{
		rscale = 0.5 * (1.0 + dot);
		lscale = 0.5*(1.0 - dot);
	}

	// add in distance effect
	scale = (1.0 - dist) * rscale;
	*right_vol = (int) (master_vol * scale);
	if (*right_vol < 0)
		*right_vol = 0;

	scale = (1.0 - dist) * lscale;
	*left_vol = (int) (master_vol * scale);
	if (*left_vol < 0)
		*left_vol = 0;
}

/*
=================
S_Spatialize
=================
"""
def S_Spatialize(ch): #channel_t *

	#Temporary code while porting
	ch.leftvol = 255 
	ch.rightvol = 255

	"""
	vec3_t		origin;

	// anything coming from the view entity will always be full volume
	if (ch->entnum == cl.playernum+1)
	{
		ch->leftvol = ch->master_vol;
		ch->rightvol = ch->master_vol;
		return;
	}

	if (ch->fixed_origin)
	{
		VectorCopy (ch->origin, origin);
	}
	else
		CL_GetEntitySoundOrigin (ch->entnum, origin);

	S_SpatializeOrigin (origin, ch->master_vol, ch->dist_mult, &ch->leftvol, &ch->rightvol);



/*
=================
S_AllocPlaysound
=================
*/
playsound_t *S_AllocPlaysound (void)
{
	playsound_t	*ps;

	ps = s_freeplays.next;
	if (ps == &s_freeplays)
		return NULL;		// no free playsounds

	// unlink from freelist
	ps->prev->next = ps->next;
	ps->next->prev = ps->prev;
	
	return ps;
}


/*
=================
S_FreePlaysound
=================
*/
void S_FreePlaysound (playsound_t *ps)
{
	// unlink from channel
	ps->prev->next = ps->next;
	ps->next->prev = ps->prev;

	// add to free list
	ps->next = s_freeplays.next;
	s_freeplays.next->prev = ps;
	ps->prev = &s_freeplays;
	s_freeplays.next = ps;
}



/*
===============
S_IssuePlaysound

Take the next playsound and begin it on the channel
This is never called directly by S_Play*, but only
by the update loop.
===============
"""
def S_IssuePlaysound (ps): #playsound_t *

	"""
	channel_t	*ch;
	sfxcache_t	*sc;
	"""

	if s_show.value:
		common.Com_Printf ("Issue %i\n".format(ps.begin))
	# pick a channel to play on
	ch = S_PickChannel(ps.entnum, ps.entchannel)
	if ch is None:
	
		#S_FreePlaysound (ps)
		return;

	# spatialize
	if ps.attenuation == q_shared.ATTN_STATIC:
		ch.dist_mult = ps.attenuation * 0.001
	else:
		ch.dist_mult = ps.attenuation * 0.0005
	ch.master_vol = ps.volume
	ch.entnum = ps.entnum
	ch.entchannel = ps.entchannel
	ch.sfx = ps.sfx
	ps.origin = ch.origin
	ch.fixed_origin = ps.fixed_origin

	S_Spatialize(ch)
	
	ch.pos = 0;
	sc = snd_mem.S_LoadSound (ch.sfx)
	ch.end = paintedtime + sc.length

	ch.chan.set_volume(ch.master_vol/255*ch.leftvol/255, ch.master_vol/255*ch.rightvol/255)
	ch.chan.play(sc.data)

"""
struct sfx_s *S_RegisterSexedSound (entity_state_t *ent, char *base)
{
	int				n;
	char			*p;
	struct sfx_s	*sfx;
	FILE			*f;
	char			model[MAX_QPATH];
	char			sexedFilename[MAX_QPATH];
	char			maleFilename[MAX_QPATH];

	// determine what model the client is using
	model[0] = 0;
	n = CS_PLAYERSKINS + ent->number - 1;
	if (cl.configstrings[n][0])
	{
		p = strchr(cl.configstrings[n], '\\');
		if (p)
		{
			p += 1;
			strcpy(model, p);
			p = strchr(model, '/');
			if (p)
				*p = 0;
		}
	}
	// if we can't figure it out, they're male
	if (!model[0])
		strcpy(model, "male");

	// see if we already know of the model specific sound
	Com_sprintf (sexedFilename, sizeof(sexedFilename), "#players/%s/%s", model, base+1);
	sfx = S_FindName (sexedFilename, false);

	if (!sfx)
	{
		// no, so see if it exists
		FS_FOpenFile (&sexedFilename[1], &f);
		if (f)
		{
			// yes, close the file and register it
			FS_FCloseFile (f);
			sfx = S_RegisterSound (sexedFilename);
		}
		else
		{
			// no, revert to the male sound in the pak0.pak
			Com_sprintf (maleFilename, sizeof(maleFilename), "player/%s/%s", "male", base+1);
			sfx = S_AliasName (sexedFilename, maleFilename);
		}
	}

	return sfx;
}


// =======================================================================
// Start a sound effect
// =======================================================================

/*
====================
S_StartSound

Validates the parms and ques the sound up
if pos is NULL, the sound will be dynamically sourced from the entity
Entchannel 0 will never override a playing sound
====================
"""
def S_StartSound(origin, entnum, entchannel, sfx, fvol, attenuation, timeofs): #vec3_t, int, int, sfx_t *, float, float, float

	global s_beginofs, sound_started
	#common.Com_Printf("S_StartSound {}\n".format(sfx.name))

	"""
	sfxcache_t	*sc;
	int			vol;
	playsound_t	*ps, *sort;
	int			start;
	"""

	if not sound_started:
		return

	if sfx is None:
		return

	#if sfx.name[0] == '*':
	#	sfx = S_RegisterSexedSound(&cl_entities[entnum].current, sfx.name)

	# make sure the sound is loaded
	sc = snd_mem.S_LoadSound (sfx)

	if sc is None:
		return		# couldn't load the sound's data

	vol = fvol*255

	# make the playsound_t
	ps = snd_loc.playsound_t ()
	if ps is None:
		return

	if origin is not None:
		ps.origin = origin
		ps.fixed_origin = True
	else:
		ps.origin = None
		ps.fixed_origin = False

	ps.entnum = entnum
	ps.entchannel = entchannel
	ps.attenuation = attenuation
	ps.volume = vol
	ps.sfx = sfx

	"""
	# drift s_beginofs
	start = cl.frame.servertime * 0.001 * dma.speed + s_beginofs;
	if (start < paintedtime)
	{
		start = paintedtime;
		s_beginofs = start - (cl.frame.servertime * 0.001 * dma.speed);
	}
	else if (start > paintedtime + 0.3 * dma.speed)
	{
		start = paintedtime + 0.1 * dma.speed;
		s_beginofs = start - (cl.frame.servertime * 0.001 * dma.speed);
	}
	else
	{
		s_beginofs-=10;
	}
"""
	if timeofs == 0.0:
		ps.begin = paintedtime
	else:
		ps.begin = start + timeofs * dma.speed

	# sort into the pending sound list
	s_pendingplays.append(ps)
	s_pendingplays.sort(key = lambda x: x.begin)

"""
==================
S_StartLocalSound
==================
*/
void S_StartLocalSound (char *sound)
{
	sfx_t	*sfx;

	if (!sound_started)
		return;
		
	sfx = S_RegisterSound (sound);
	if (!sfx)
	{
		Com_Printf ("S_StartLocalSound: can't cache %s\n", sound);
		return;
	}
	S_StartSound (NULL, cl.playernum+1, 0, sfx, 1, 1, 0.0);
}


/*
==================
S_ClearBuffer
==================
*/
void S_ClearBuffer (void)
{
	int		clear;
		
	if (!sound_started)
		return;

	s_rawend = 0;

	if (dma.samplebits == 8)
		clear = 0x80;
	else
		clear = 0;

	SNDDMA_BeginPainting ();
	if (dma.buffer)
		memset(dma.buffer, clear, dma.samples * dma.samplebits/8);
	SNDDMA_Submit ();
}

/*
==================
S_StopAllSounds
==================
"""
def S_StopAllSounds():
	pass
	"""
	int		i;

	if (!sound_started)
		return;

	// clear all the playsounds
	memset(s_playsounds, 0, sizeof(s_playsounds));
	s_freeplays.next = s_freeplays.prev = &s_freeplays;
	s_pendingplays.next = s_pendingplays.prev = &s_pendingplays;

	for (i=0 ; i<MAX_PLAYSOUNDS ; i++)
	{
		s_playsounds[i].prev = &s_freeplays;
		s_playsounds[i].next = s_freeplays.next;
		s_playsounds[i].prev->next = &s_playsounds[i];
		s_playsounds[i].next->prev = &s_playsounds[i];
	}

	// clear all the channels
	memset(channels, 0, sizeof(channels));

	S_ClearBuffer ();
}

/*
==================
S_AddLoopSounds

Entities with a ->sound field will generated looped sounds
that are automatically started, stopped, and merged together
as the entities are sent to the client
==================
*/
void S_AddLoopSounds (void)
{
	int			i, j;
	int			sounds[MAX_EDICTS];
	int			left, right, left_total, right_total;
	channel_t	*ch;
	sfx_t		*sfx;
	sfxcache_t	*sc;
	int			num;
	entity_state_t	*ent;

	if (cl_paused->value)
		return;

	if (cls.state != ca_active)
		return;

	if (!cl.sound_prepped)
		return;

	for (i=0 ; i<cl.frame.num_entities ; i++)
	{
		num = (cl.frame.parse_entities + i)&(MAX_PARSE_ENTITIES-1);
		ent = &cl_parse_entities[num];
		sounds[i] = ent->sound;
	}

	for (i=0 ; i<cl.frame.num_entities ; i++)
	{
		if (!sounds[i])
			continue;

		sfx = cl.sound_precache[sounds[i]];
		if (!sfx)
			continue;		// bad sound effect
		sc = sfx->cache;
		if (!sc)
			continue;

		num = (cl.frame.parse_entities + i)&(MAX_PARSE_ENTITIES-1);
		ent = &cl_parse_entities[num];

		// find the total contribution of all sounds of this type
		S_SpatializeOrigin (ent->origin, 255.0, SOUND_LOOPATTENUATE,
			&left_total, &right_total);
		for (j=i+1 ; j<cl.frame.num_entities ; j++)
		{
			if (sounds[j] != sounds[i])
				continue;
			sounds[j] = 0;	// don't check this again later

			num = (cl.frame.parse_entities + j)&(MAX_PARSE_ENTITIES-1);
			ent = &cl_parse_entities[num];

			S_SpatializeOrigin (ent->origin, 255.0, SOUND_LOOPATTENUATE, 
				&left, &right);
			left_total += left;
			right_total += right;
		}

		if (left_total == 0 && right_total == 0)
			continue;		// not audible

		// allocate a channel
		ch = S_PickChannel(0, 0);
		if (!ch)
			return;

		if (left_total > 255)
			left_total = 255;
		if (right_total > 255)
			right_total = 255;
		ch->leftvol = left_total;
		ch->rightvol = right_total;
		ch->autosound = true;	// remove next frame
		ch->sfx = sfx;
		ch->pos = paintedtime % sc->length;
		ch->end = paintedtime + sc->length - ch->pos;
	}
}

//=============================================================================

/*
============
S_RawSamples

Cinematic streaming and voice over network
============
*/
void S_RawSamples (int samples, int rate, int width, int channels, byte *data)
{
	int		i;
	int		src, dst;
	float	scale;

	if (!sound_started)
		return;

	if (s_rawend < paintedtime)
		s_rawend = paintedtime;
	scale = (float)rate / dma.speed;

//Com_Printf ("%i < %i < %i\n", soundtime, paintedtime, s_rawend);
	if (channels == 2 && width == 2)
	{
		if (scale == 1.0)
		{	// optimized case
			for (i=0 ; i<samples ; i++)
			{
				dst = s_rawend&(MAX_RAW_SAMPLES-1);
				s_rawend++;
				s_rawsamples[dst].left =
					LittleShort(((short *)data)[i*2]) << 8;
				s_rawsamples[dst].right =
					LittleShort(((short *)data)[i*2+1]) << 8;
			}
		}
		else
		{
			for (i=0 ; ; i++)
			{
				src = i*scale;
				if (src >= samples)
					break;
				dst = s_rawend&(MAX_RAW_SAMPLES-1);
				s_rawend++;
				s_rawsamples[dst].left =
					LittleShort(((short *)data)[src*2]) << 8;
				s_rawsamples[dst].right =
					LittleShort(((short *)data)[src*2+1]) << 8;
			}
		}
	}
	else if (channels == 1 && width == 2)
	{
		for (i=0 ; ; i++)
		{
			src = i*scale;
			if (src >= samples)
				break;
			dst = s_rawend&(MAX_RAW_SAMPLES-1);
			s_rawend++;
			s_rawsamples[dst].left =
				LittleShort(((short *)data)[src]) << 8;
			s_rawsamples[dst].right =
				LittleShort(((short *)data)[src]) << 8;
		}
	}
	else if (channels == 2 && width == 1)
	{
		for (i=0 ; ; i++)
		{
			src = i*scale;
			if (src >= samples)
				break;
			dst = s_rawend&(MAX_RAW_SAMPLES-1);
			s_rawend++;
			s_rawsamples[dst].left =
				((char *)data)[src*2] << 16;
			s_rawsamples[dst].right =
				((char *)data)[src*2+1] << 16;
		}
	}
	else if (channels == 1 && width == 1)
	{
		for (i=0 ; ; i++)
		{
			src = i*scale;
			if (src >= samples)
				break;
			dst = s_rawend&(MAX_RAW_SAMPLES-1);
			s_rawend++;
			s_rawsamples[dst].left =
				(((byte *)data)[src]-128) << 16;
			s_rawsamples[dst].right = (((byte *)data)[src]-128) << 16;
		}
	}
}

//=============================================================================

/*
============
S_Update

Called once each time through the main loop
============
"""
def S_Update(origin, forward, right, up): #vec3_t, vec3_t, vec3_t, vec3_t

	"""
	int			i;
	int			total;
	channel_t	*ch;
	channel_t	*combine;
	"""

	global sound_started

	if not sound_started:
		return

	"""
	# if the laoding plaque is up, clear everything
	# out to make sure we aren't looping a dirty
	# dma buffer while loading
	if (cls.disable_screen)
	{
		S_ClearBuffer ();
		return;
	}

	# rebuild scale tables if volume is modified
	if (s_volume->modified)
		S_InitScaletable ();

	VectorCopy(origin, listener_origin);
	VectorCopy(forward, listener_forward);
	VectorCopy(right, listener_right);
	VectorCopy(up, listener_up);

	combine = NULL;

	# update spatialization for dynamic sounds	
	ch = channels;
	for (i=0 ; i<MAX_CHANNELS; i++, ch++)
	{
		if (!ch->sfx)
			continue;
		if (ch->autosound)
		{	// autosounds are regenerated fresh each frame
			memset (ch, 0, sizeof(*ch));
			continue;
		}
		S_Spatialize(ch);		 // respatialize channel
		if (!ch->leftvol && !ch->rightvol)
		{
			memset (ch, 0, sizeof(*ch));
			continue;
		}
	}

	# add loopsounds
	S_AddLoopSounds ();

	#
	# debugging output
	#
	if (s_show->value)
	{
		total = 0;
		ch = channels;
		for (i=0 ; i<MAX_CHANNELS; i++, ch++)
			if (ch->sfx && (ch->leftvol || ch->rightvol) )
			{
				Com_Printf ("%3i %3i %s\n", ch->leftvol, ch->rightvol, ch->sfx->name);
				total++;
			}
		
		Com_Printf ("----(%i)---- painted: %i\n", total, paintedtime);
	}
"""
	# mix some sound
	S_Update_();


def GetSoundtime():

	global soundtime
	"""
	int		samplepos;
	static	int		buffers;
	static	int		oldsamplepos;
	int		fullsamples;
	"""
	
	"""
	fullsamples = dma.samples / dma.channels;

// it is possible to miscount buffers if it has wrapped twice between
// calls to S_Update.  Oh well.
	samplepos = SNDDMA_GetDMAPos();

	if (samplepos < oldsamplepos)
	{
		buffers++;					// buffer wrapped
		
		if (paintedtime > 0x40000000)
		{	// time to chop things off to avoid 32 bit limits
			buffers = 0;
			paintedtime = fullsamples;
			S_StopAllSounds ();
		}
	}
	oldsamplepos = samplepos;

	soundtime = buffers*fullsamples + samplepos/dma.channels;
	"""
	soundtime = q_shlinux.Sys_Milliseconds() #FIXME set the real value?


def S_Update_():

	"""
	unsigned		endtime;
	int				samps;
	"""

	global sound_started, paintedtime, soundtime

	if not sound_started:
		return
	"""
	SNDDMA_BeginPainting ();

	if (!dma.buffer)
		return;
"""
	# Updates DMA time
	GetSoundtime()

	# check to make sure that we haven't overshot
	#if paintedtime < soundtime:
	
	#	common.Com_DPrintf ("S_Update_ : overflow\n")
	#	paintedtime = soundtime
	
	endtime = soundtime #FIXME is mix ahead needed?
	"""
	# mix ahead of current position
	endtime = soundtime + s_mixahead->value * dma.speed;
	##endtime = (soundtime + 4096) & ~4095;

	# mix to an even submission block size
	endtime = (endtime + dma.submission_chunk-1)
		& ~(dma.submission_chunk-1);
	samps = dma.samples >> (dma.channels-1);
	if (endtime - soundtime > samps)
		endtime = soundtime + samps;
	"""

	snd_mix.S_PaintChannels (endtime)

	#SNDDMA_Submit ()

"""
===============================================================================

console functions

===============================================================================
"""

def S_Play():

	"""
	int 	i;
	char name[256];
	sfx_t	*sfx;
	"""
	i = 1
	while i<cmd.Cmd_Argc():
	
		if cmd.Cmd_Argv(i).find('.') == -1:
		
			name = "{}.wav".format(cmd.Cmd_Argv(i))
		
		else:
			name = cmd.Cmd_Argv(i)
		sfx = S_RegisterSound(name)
		S_StartSound(None, cl_main.cl.playernum+1, 0, sfx, 1.0, 1.0, 0.0)
		i+=1

def S_SoundList():
	pass
	"""
	int		i;
	sfx_t	*sfx;
	sfxcache_t	*sc;
	int		size, total;

	total = 0;
	for (sfx=known_sfx, i=0 ; i<num_sfx ; i++, sfx++)
	{
		if (!sfx->registration_sequence)
			continue;
		sc = sfx->cache;
		if (sc)
		{
			size = sc->length*sc->width*(sc->stereo+1);
			total += size;
			if (sc->loopstart >= 0)
				Com_Printf ("L");
			else
				Com_Printf (" ");
			Com_Printf("(%2db) %6i : %s\n",sc->width*8,  size, sfx->name);
		}
		else
		{
			if (sfx->name[0] == '*')
				Com_Printf("  placeholder : %s\n", sfx->name);
			else
				Com_Printf("  not loaded  : %s\n", sfx->name);
		}
	}
	Com_Printf ("Total resident: %i\n", total);

"""