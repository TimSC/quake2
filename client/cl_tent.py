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

*/
"""
import math
import random
import numpy as np
from enum import Enum
from qcommon import common, net_chan
from game import q_shared
from client import cl_fx, snd_dma, ref, cl_main
from linux import vid_so
"""
// cl_tent.c -- client side temporary entities

#include "client.h"
"""
class exptype_t(Enum):

	ex_free = 0
	ex_explosion = 1
	ex_misc = 2
	ex_flash = 3
	ex_mflash = 4
	ex_poly = 5
	ex_poly2 = 6

class explosion_t(object):

	def __init__(self):
		self.clear()

	def clear(self):
		self.typeval = exptype_t.ex_free #exptype_t	
		self.ent = ref.entity_t() #entity_t

		self.frames = None # int			
		self.light = None # float		
		self.lightcolor = np.zeros((3,), dtype=np.float32) # vec3_t		
		self.start = None # float
		self.baseframe = None # int




MAX_EXPLOSIONS = 32
cl_explosions = []
for ex in range(MAX_EXPLOSIONS):
	cl_explosions.append(explosion_t())

"""
#define	MAX_BEAMS	32
typedef struct
{
	int		entity;
	int		dest_entity;
	struct model_s	*model;
	int		endtime;
	vec3_t	offset;
	vec3_t	start, end;
} beam_t;
beam_t		cl_beams[MAX_BEAMS];
//PMM - added this for player-linked beams.  Currently only used by the plasma beam
beam_t		cl_playerbeams[MAX_BEAMS];


#define	MAX_LASERS	32
typedef struct
{
	entity_t	ent;
	int			endtime;
} laser_t;
laser_t		cl_lasers[MAX_LASERS];

//ROGUE
cl_sustain_t	cl_sustains[MAX_SUSTAINS];
//ROGUE

//PGM
extern void CL_TeleportParticles (vec3_t org);
//PGM

void CL_BlasterParticles (vec3_t org, vec3_t dir);
void cl_fx.CL_ExplosionParticles (vec3_t org);
void CL_BFGExplosionParticles (vec3_t org);
// RAFAEL
void CL_BlueBlasterParticles (vec3_t org, vec3_t dir);
"""
cl_sfx_ric1 = None #struct sfx_s	*
cl_sfx_ric2 = None
cl_sfx_ric3 = None 
cl_sfx_lashit = None
cl_sfx_spark5 = None
cl_sfx_spark6 = None 
cl_sfx_spark7 = None 
cl_sfx_railg = None
cl_sfx_rockexp = None
cl_sfx_grenexp = None 
cl_sfx_watrexp = None 
# RAFAEL
cl_sfx_plasexp = None 
cl_sfx_footsteps = [None, None, None, None] # struct sfx_s	*[4]


cl_mod_explode = None #struct model_s	*;
"""
struct model_s	*cl_mod_smoke;
struct model_s	*cl_mod_flash;
struct model_s	*cl_mod_parasite_segment;
struct model_s	*cl_mod_grapple_cable;
struct model_s	*cl_mod_parasite_tip;
"""
cl_mod_explo4 = None
"""
struct model_s	*cl_mod_bfg_explo;
struct model_s	*cl_mod_powerscreen;
// RAFAEL
struct model_s	*cl_mod_plasmaexplo;

//ROGUE
struct sfx_s	*cl_sfx_lightning;
struct sfx_s	*cl_sfx_disrexp;
struct model_s	*cl_mod_lightning;
struct model_s	*cl_mod_heatbeam;
struct model_s	*cl_mod_monster_heatbeam;
struct model_s	*cl_mod_explo4_big;

//ROGUE
/*
=================
CL_RegisterTEntSounds
=================
"""
def CL_RegisterTEntSounds ():

	global cl_sfx_ric1, cl_sfx_ric2, cl_sfx_ric3
	global cl_sfx_lashit
	global cl_sfx_spark5, cl_sfx_spark6, cl_sfx_spark7
	global cl_sfx_railg, cl_sfx_rockexp, cl_sfx_grenexp, cl_sfx_watrexp
	global cl_sfx_footsteps, cl_sfx_lightning, cl_sfx_disrexp

	"""
	int		i;
	char	name[MAX_QPATH];

	// PMM - version stuff
//	Com_Printf ("%s\n", ROGUE_VERSION_STRING);
	// PMM
	"""
	cl_sfx_ric1 = snd_dma.S_RegisterSound ("world/ric1.wav")
	cl_sfx_ric2 = snd_dma.S_RegisterSound ("world/ric2.wav")
	cl_sfx_ric3 = snd_dma.S_RegisterSound ("world/ric3.wav")
	cl_sfx_lashit = snd_dma.S_RegisterSound("weapons/lashit.wav")
	cl_sfx_spark5 = snd_dma.S_RegisterSound ("world/spark5.wav")
	cl_sfx_spark6 = snd_dma.S_RegisterSound ("world/spark6.wav")
	cl_sfx_spark7 = snd_dma.S_RegisterSound ("world/spark7.wav")
	cl_sfx_railg = snd_dma.S_RegisterSound ("weapons/railgf1a.wav")
	cl_sfx_rockexp = snd_dma.S_RegisterSound ("weapons/rocklx1a.wav")
	cl_sfx_grenexp = snd_dma.S_RegisterSound ("weapons/grenlx1a.wav")
	cl_sfx_watrexp = snd_dma.S_RegisterSound ("weapons/xpld_wat.wav")
	# RAFAEL
	# cl_sfx_plasexp = S_RegisterSound ("weapons/plasexpl.wav");
	snd_dma.S_RegisterSound ("player/land1.wav")

	snd_dma.S_RegisterSound ("player/fall2.wav")
	snd_dma.S_RegisterSound ("player/fall1.wav")

	for i in range(4):
	
		name = "player/step{}.wav".format(i+1)
		cl_sfx_footsteps[i] = snd_dma.S_RegisterSound (name)
	

#PGM
	cl_sfx_lightning = snd_dma.S_RegisterSound ("weapons/tesla.wav")
	cl_sfx_disrexp = snd_dma.S_RegisterSound ("weapons/disrupthit.wav")
	# version stuff
#	sprintf (name, "weapons/sound%d.wav", ROGUE_VERSION_ID);
#	if (name[0] == 'w')
#		name[0] = 'W';
#PGM
	

"""
=================
CL_RegisterTEntModels
=================
"""
def CL_RegisterTEntModels ():

	global cl_mod_explode, cl_mod_smoke, cl_mod_flash
	global cl_mod_parasite_segment, cl_mod_grapple_cable, cl_mod_parasite_tip
	global cl_mod_explo4, cl_mod_bfg_explo,cl_mod_powerscreen
	global cl_mod_explo4_big, cl_mod_lightning, cl_mod_heatbeam, cl_mod_monster_heatbeam

	cl_mod_explode = vid_so.re.RegisterModel ("models/objects/explode/tris.md2")
	cl_mod_smoke = vid_so.re.RegisterModel ("models/objects/smoke/tris.md2")
	cl_mod_flash = vid_so.re.RegisterModel ("models/objects/flash/tris.md2")
	cl_mod_parasite_segment = vid_so.re.RegisterModel ("models/monsters/parasite/segment/tris.md2")
	cl_mod_grapple_cable = vid_so.re.RegisterModel ("models/ctf/segment/tris.md2")
	cl_mod_parasite_tip = vid_so.re.RegisterModel ("models/monsters/parasite/tip/tris.md2")
	cl_mod_explo4 = vid_so.re.RegisterModel ("models/objects/r_explode/tris.md2")
	cl_mod_bfg_explo = vid_so.re.RegisterModel ("sprites/s_bfg2.sp2")
	cl_mod_powerscreen = vid_so.re.RegisterModel ("models/items/armor/effect/tris.md2")

	vid_so.re.RegisterModel ("models/objects/laser/tris.md2")
	vid_so.re.RegisterModel ("models/objects/grenade2/tris.md2")
	vid_so.re.RegisterModel ("models/weapons/v_machn/tris.md2")
	vid_so.re.RegisterModel ("models/weapons/v_handgr/tris.md2")
	vid_so.re.RegisterModel ("models/weapons/v_shotg2/tris.md2")
	vid_so.re.RegisterModel ("models/objects/gibs/bone/tris.md2")
	vid_so.re.RegisterModel ("models/objects/gibs/sm_meat/tris.md2")
	vid_so.re.RegisterModel ("models/objects/gibs/bone2/tris.md2")
	# RAFAEL
	# vid_so.re.RegisterModel ("models/objects/blaser/tris.md2");

	vid_so.re.RegisterPic ("w_machinegun")
	vid_so.re.RegisterPic ("a_bullets")
	vid_so.re.RegisterPic ("i_health")
	vid_so.re.RegisterPic ("a_grenades")

#ROGUE
	cl_mod_explo4_big = vid_so.re.RegisterModel ("models/objects/r_explode2/tris.md2")
	cl_mod_lightning = vid_so.re.RegisterModel ("models/proj/lightning/tris.md2")
	cl_mod_heatbeam = vid_so.re.RegisterModel ("models/proj/beam/tris.md2")
	cl_mod_monster_heatbeam = vid_so.re.RegisterModel ("models/proj/widowbeam/tris.md2")
#ROGUE
	

"""
=================
CL_ClearTEnts
=================
"""
def CL_ClearTEnts ():

	print ("CL_ClearTEnts")
	"""
	memset (cl_beams, 0, sizeof(cl_beams))
	"""
	for ex in cl_explosions:
		ex.clear()
	"""
	memset (cl_lasers, 0, sizeof(cl_lasers))

# ROGUE
	memset (cl_playerbeams, 0, sizeof(cl_playerbeams))
	memset (cl_sustains, 0, sizeof(cl_sustains))
# ROGUE
	"""

"""
=================
CL_AllocExplosion
=================
"""
def CL_AllocExplosion () -> explosion_t:

	"""
	int		i;
	int		time;
	int		index;
	"""
	
	for ex in cl_explosions:
	
		if ex.typeval == exptype_t.ex_free:
		
			ex.clear()
			return ex
	
# find the oldest explosion
	time = cl_main.cl.time
	index = 0

	for i in range(len(cl_explosions)):
		if cl_explosions[i].start < time:
		
			time = cl_explosions[i].start
			index = i

	cl_explosions[index].clear()
	return cl_explosions[index]


"""
=================
CL_SmokeAndFlash
=================
"""
def CL_SmokeAndFlash(origin):
	pass
	"""
	explosion_t	*ex;

	ex = CL_AllocExplosion ();
	q_shared.VectorCopy (origin, ex.ent.origin);
	ex.typeval = ex_misc;
	ex.frames = 4;
	ex.ent.flags = q_shared.RF_TRANSLUCENT;
	ex.start = cl_main.cl.frame.servertime - 100;
	ex.ent.model = cl_mod_smoke;

	ex = CL_AllocExplosion ();
	q_shared.VectorCopy (origin, ex.ent.origin);
	ex.typeval = ex_flash;
	ex.ent.flags = q_shared.RF_FULLBRIGHT;
	ex.frames = 2;
	ex.start = cl_main.cl.frame.servertime - 100;
	ex.ent.model = cl_mod_flash;
}

/*
=================
CL_ParseParticles
=================
*/
void CL_ParseParticles (void)
{
	int		color, count;
	vec3_t	pos, dir;

	MSG_ReadPos (&net_chan.net_message, pos);
	MSG_ReadDir (&net_chan.net_message, dir);

	color = MSG_ReadByte (&net_chan.net_message);

	count = MSG_ReadByte (&net_chan.net_message);

	cl_fx.CL_ParticleEffect (pos, dir, color, count);
}

/*
=================
CL_ParseBeam
=================
*/
int CL_ParseBeam (struct model_s *model)
{
	int		ent;
	vec3_t	start, end;
	beam_t	*b;
	int		i;
	
	ent = MSG_ReadShort (&net_chan.net_message);
	
	MSG_ReadPos (&net_chan.net_message, start);
	MSG_ReadPos (&net_chan.net_message, end);

// override any beam with the same entity
	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
		if (b->entity == ent)
		{
			b->entity = ent;
			b->model = model;
			b->endtime = cl.time + 200;
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			VectorClear (b->offset);
			return ent;
		}

// find a free beam
	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
	{
		if (!b->model || b->endtime < cl.time)
		{
			b->entity = ent;
			b->model = model;
			b->endtime = cl.time + 200;
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			VectorClear (b->offset);
			return ent;
		}
	}
	Com_Printf ("beam list overflow!\n");	
	return ent;
}

/*
=================
CL_ParseBeam2
=================
*/
int CL_ParseBeam2 (struct model_s *model)
{
	int		ent;
	vec3_t	start, end, offset;
	beam_t	*b;
	int		i;
	
	ent = MSG_ReadShort (&net_chan.net_message);
	
	MSG_ReadPos (&net_chan.net_message, start);
	MSG_ReadPos (&net_chan.net_message, end);
	MSG_ReadPos (&net_chan.net_message, offset);

//	Com_Printf ("end- %f %f %f\n", end[0], end[1], end[2]);

// override any beam with the same entity

	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
		if (b->entity == ent)
		{
			b->entity = ent;
			b->model = model;
			b->endtime = cl.time + 200;
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			q_shared.VectorCopy (offset, b->offset);
			return ent;
		}

// find a free beam
	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
	{
		if (!b->model || b->endtime < cl.time)
		{
			b->entity = ent;
			b->model = model;
			b->endtime = cl.time + 200;	
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			q_shared.VectorCopy (offset, b->offset);
			return ent;
		}
	}
	Com_Printf ("beam list overflow!\n");	
	return ent;
}

// ROGUE
/*
=================
CL_ParsePlayerBeam
  - adds to the cl_playerbeam array instead of the cl_beams array
=================
*/
int CL_ParsePlayerBeam (struct model_s *model)
{
	int		ent;
	vec3_t	start, end, offset;
	beam_t	*b;
	int		i;
	
	ent = MSG_ReadShort (&net_chan.net_message);
	
	MSG_ReadPos (&net_chan.net_message, start);
	MSG_ReadPos (&net_chan.net_message, end);
	// PMM - network optimization
	if (model == cl_mod_heatbeam)
		VectorSet(offset, 2, 7, -3);
	else if (model == cl_mod_monster_heatbeam)
	{
		model = cl_mod_heatbeam;
		VectorSet(offset, 0, 0, 0);
	}
	else
		MSG_ReadPos (&net_chan.net_message, offset);

//	Com_Printf ("end- %f %f %f\n", end[0], end[1], end[2]);

// override any beam with the same entity
// PMM - For player beams, we only want one per player (entity) so..
	for (i=0, b=cl_playerbeams ; i< MAX_BEAMS ; i++, b++)
	{
		if (b->entity == ent)
		{
			b->entity = ent;
			b->model = model;
			b->endtime = cl.time + 200;
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			q_shared.VectorCopy (offset, b->offset);
			return ent;
		}
	}

// find a free beam
	for (i=0, b=cl_playerbeams ; i< MAX_BEAMS ; i++, b++)
	{
		if (!b->model || b->endtime < cl.time)
		{
			b->entity = ent;
			b->model = model;
			b->endtime = cl.time + 100;		// PMM - this needs to be 100 to prevent multiple heatbeams
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			q_shared.VectorCopy (offset, b->offset);
			return ent;
		}
	}
	Com_Printf ("beam list overflow!\n");	
	return ent;
}
//rogue

/*
=================
CL_ParseLightning
=================
*/
int CL_ParseLightning (struct model_s *model)
{
	int		srcEnt, destEnt;
	vec3_t	start, end;
	beam_t	*b;
	int		i;
	
	srcEnt = MSG_ReadShort (&net_chan.net_message);
	destEnt = MSG_ReadShort (&net_chan.net_message);

	MSG_ReadPos (&net_chan.net_message, start);
	MSG_ReadPos (&net_chan.net_message, end);

// override any beam with the same source AND destination entities
	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
		if (b->entity == srcEnt && b->dest_entity == destEnt)
		{
//			Com_Printf("%d: OVERRIDE  %d -> %d\n", cl.time, srcEnt, destEnt);
			b->entity = srcEnt;
			b->dest_entity = destEnt;
			b->model = model;
			b->endtime = cl.time + 200;
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			VectorClear (b->offset);
			return srcEnt;
		}

// find a free beam
	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
	{
		if (!b->model || b->endtime < cl.time)
		{
//			Com_Printf("%d: NORMAL  %d -> %d\n", cl.time, srcEnt, destEnt);
			b->entity = srcEnt;
			b->dest_entity = destEnt;
			b->model = model;
			b->endtime = cl.time + 200;
			q_shared.VectorCopy (start, b->start);
			q_shared.VectorCopy (end, b->end);
			VectorClear (b->offset);
			return srcEnt;
		}
	}
	Com_Printf ("beam list overflow!\n");	
	return srcEnt;
}

/*
=================
CL_ParseLaser
=================
*/
void CL_ParseLaser (int colors)
{
	vec3_t	start;
	vec3_t	end;
	laser_t	*l;
	int		i;

	MSG_ReadPos (&net_chan.net_message, start);
	MSG_ReadPos (&net_chan.net_message, end);

	for (i=0, l=cl_lasers ; i< MAX_LASERS ; i++, l++)
	{
		if (l->endtime < cl.time)
		{
			l->ent.flags = q_shared.RF_TRANSLUCENT | RF_BEAM;
			q_shared.VectorCopy (start, l->ent.origin);
			q_shared.VectorCopy (end, l->ent.oldorigin);
			l->ent.alpha = 0.30;
			l->ent.skinnum = (colors >> ((rand() % 4)*8)) & 0xff;
			l->ent.model = NULL;
			l->ent.frame = 4;
			l->endtime = cl.time + 100;
			return;
		}
	}
}

//=============
//ROGUE
void CL_ParseSteam (void)
{
	vec3_t	pos, dir;
	int		id, i;
	int		r;
	int		cnt;
	int		color;
	int		magnitude;
	cl_sustain_t	*s, *free_sustain;

	id = MSG_ReadShort (&net_chan.net_message);		// an id of -1 is an instant effect
	if (id != -1) // sustains
	{
//			Com_Printf ("Sustain effect id %d\n", id);
		free_sustain = NULL;
		for (i=0, s=cl_sustains; i<MAX_SUSTAINS; i++, s++)
		{
			if (s->id == 0)
			{
				free_sustain = s;
				break;
			}
		}
		if (free_sustain)
		{
			s->id = id;
			s->count = MSG_ReadByte (&net_chan.net_message);
			MSG_ReadPos (&net_chan.net_message, s->org);
			MSG_ReadDir (&net_chan.net_message, s->dir);
			r = MSG_ReadByte (&net_chan.net_message);
			s->color = r & 0xff;
			s->magnitude = MSG_ReadShort (&net_chan.net_message);
			s->endtime = cl.time + MSG_ReadLong (&net_chan.net_message);
			s->think = CL_ParticleSteamEffect2;
			s->thinkinterval = 100;
			s->nextthink = cl.time;
		}
		else
		{
//				Com_Printf ("No free sustains!\n");
			// FIXME - read the stuff anyway
			cnt = MSG_ReadByte (&net_chan.net_message);
			MSG_ReadPos (&net_chan.net_message, pos);
			MSG_ReadDir (&net_chan.net_message, dir);
			r = MSG_ReadByte (&net_chan.net_message);
			magnitude = MSG_ReadShort (&net_chan.net_message);
			magnitude = MSG_ReadLong (&net_chan.net_message); // really interval
		}
	}
	else // instant
	{
		cnt = MSG_ReadByte (&net_chan.net_message);
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		r = MSG_ReadByte (&net_chan.net_message);
		magnitude = MSG_ReadShort (&net_chan.net_message);
		color = r & 0xff;
		CL_ParticleSteamEffect (pos, dir, color, cnt, magnitude);
//		snd_dma.S_StartSound (pos,  0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
	}
}

void CL_ParseWidow (void)
{
	vec3_t	pos;
	int		id, i;
	cl_sustain_t	*s, *free_sustain;

	id = MSG_ReadShort (&net_chan.net_message);

	free_sustain = NULL;
	for (i=0, s=cl_sustains; i<MAX_SUSTAINS; i++, s++)
	{
		if (s->id == 0)
		{
			free_sustain = s;
			break;
		}
	}
	if (free_sustain)
	{
		s->id = id;
		MSG_ReadPos (&net_chan.net_message, s->org);
		s->endtime = cl.time + 2100;
		s->think = CL_Widowbeamout;
		s->thinkinterval = 1;
		s->nextthink = cl.time;
	}
	else // no free sustains
	{
		// FIXME - read the stuff anyway
		MSG_ReadPos (&net_chan.net_message, pos);
	}
}

void CL_ParseNuke (void)
{
	vec3_t	pos;
	int		i;
	cl_sustain_t	*s, *free_sustain;

	free_sustain = NULL;
	for (i=0, s=cl_sustains; i<MAX_SUSTAINS; i++, s++)
	{
		if (s->id == 0)
		{
			free_sustain = s;
			break;
		}
	}
	if (free_sustain)
	{
		s->id = 21000;
		MSG_ReadPos (&net_chan.net_message, s->org);
		s->endtime = cl.time + 1000;
		s->think = CL_Nukeblast;
		s->thinkinterval = 1;
		s->nextthink = cl.time;
	}
	else // no free sustains
	{
		// FIXME - read the stuff anyway
		MSG_ReadPos (&net_chan.net_message, pos);
	}
}

//ROGUE
//=============


/*
=================
CL_ParseTEnt
=================
"""
splash_color = [0x00, 0xe0, 0xb0, 0x50, 0xd0, 0xe0, 0xe8] #static byte[]

def CL_ParseTEnt ():

	"""
	int		type;
	vec3_t	pos, pos2, dir;
	explosion_t	*ex;
	int		cnt;
	int		color;
	int		r;
	int		ent;
	int		magnitude;
	"""

	typeIn = common.MSG_ReadByte (net_chan.net_message)

	typeIn = q_shared.temp_event_t(typeIn)

	#switch (type)
	
	if typeIn == q_shared.temp_event_t.TE_BLOOD:			# bullet hitting flesh
		pos = common.MSG_ReadPos (net_chan.net_message)
		readdir = common.MSG_ReadDir (net_chan.net_message)
		cl_fx.CL_ParticleEffect (pos, readdir, 0xe8, 60)


	elif typeIn in [q_shared.temp_event_t.TE_GUNSHOT,			# bullet hitting wall
		q_shared.temp_event_t.TE_SPARKS,
		q_shared.temp_event_t.TE_BULLET_SPARKS]:

		pos = common.MSG_ReadPos (net_chan.net_message)
		readdir = common.MSG_ReadDir (net_chan.net_message)
		if typeIn == q_shared.temp_event_t.TE_GUNSHOT:
			cl_fx.CL_ParticleEffect (pos, readdir, 0, 40)
		else:
			cl_fx.CL_ParticleEffect (pos, readdir, 0xe0, 6)

		if typeIn != q_shared.temp_event_t.TE_SPARKS:
		
			CL_SmokeAndFlash(pos)
			
			# impact sound
			cnt = random.randint(0, 14)
			if cnt == 1:
				snd_dma.S_StartSound (pos, 0, 0, cl_sfx_ric1, 1, q_shared.ATTN_NORM, 0)
			elif cnt == 2:
				snd_dma.S_StartSound (pos, 0, 0, cl_sfx_ric2, 1, q_shared.ATTN_NORM, 0)
			elif cnt == 3:
				snd_dma.S_StartSound (pos, 0, 0, cl_sfx_ric3, 1, q_shared.ATTN_NORM, 0)
		
		"""		
	case TE_SCREEN_SPARKS:
	case TE_SHIELD_SPARKS:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		if (type == TE_SCREEN_SPARKS)
			cl_fx.CL_ParticleEffect (pos, dir, 0xd0, 40);
		else
			cl_fx.CL_ParticleEffect (pos, dir, 0xb0, 40);
		//FIXME : replace or remove this sound
		snd_dma.S_StartSound (pos, 0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
		break;
	"""
	elif typeIn == q_shared.temp_event_t.TE_SHOTGUN: # bullet hitting wall
		pos = common.MSG_ReadPos (net_chan.net_message)
		readdir = common.MSG_ReadDir (net_chan.net_message)
		cl_fx.CL_ParticleEffect (pos, readdir, 0, 20)
		CL_SmokeAndFlash(pos)


	elif typeIn == q_shared.temp_event_t.TE_SPLASH:			# bullet hitting water
		cnt = common.MSG_ReadByte (net_chan.net_message)
		pos = common.MSG_ReadPos (net_chan.net_message)
		readdir = common.MSG_ReadDir (net_chan.net_message)
		r = common.MSG_ReadByte (net_chan.net_message)
		if r > 6:
			color = 0x00
		else:
			color = splash_color[r]
		cl_fx.CL_ParticleEffect (pos, readdir, color, cnt)

		if r == q_shared.SPLASH_SPARKS:
		
			r = random.randint(0, 2)
			if r == 0:
				snd_dma.S_StartSound (pos, 0, 0, cl_sfx_spark5, 1, q_shared.ATTN_STATIC, 0)
			elif r == 1:
				snd_dma.S_StartSound (pos, 0, 0, cl_sfx_spark6, 1, q_shared.ATTN_STATIC, 0)
			else:
				snd_dma.S_StartSound (pos, 0, 0, cl_sfx_spark7, 1, q_shared.ATTN_STATIC, 0)
		

		"""
	case TE_LASER_SPARKS:
		cnt = MSG_ReadByte (&net_chan.net_message);
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		color = MSG_ReadByte (&net_chan.net_message);
		cl_fx.CL_ParticleEffect2 (pos, dir, color, cnt);
		break;

	// RAFAEL
	case TE_BLUEHYPERBLASTER:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadPos (&net_chan.net_message, dir);
		CL_BlasterParticles (pos, dir);
		break;
	"""
	elif typeIn == q_shared.temp_event_t.TE_BLASTER:			# blaster hitting wall
		pos = common.MSG_ReadPos (net_chan.net_message)
		readdir = common.MSG_ReadDir (net_chan.net_message)
		cl_fx.CL_BlasterParticles (pos, readdir)

		ex = CL_AllocExplosion ()
		q_shared.VectorCopy (pos, ex.ent.origin)
		ex.ent.angles[0] = math.acos(readdir[2])/math.pi*180.0
	# PMM - fixed to correct for pitch of 0
		if readdir[0]:
			ex.ent.angles[1] = math.atan2(readdir[1], readdir[0])/math.pi*180.0
		elif readdir[1] > 0:
			ex.ent.angles[1] = 90
		elif readdir[1] < 0:
			ex.ent.angles[1] = 270
		else:
			ex.ent.angles[1] = 0

		ex.typeval = exptype_t.ex_misc
		ex.ent.flags = q_shared.RF_FULLBRIGHT|q_shared.RF_TRANSLUCENT
		ex.start = cl_main.cl.frame.servertime - 100
		ex.light = 150
		ex.lightcolor[0] = 1
		ex.lightcolor[1] = 1
		ex.ent.model = cl_mod_explode
		ex.frames = 4
		snd_dma.S_StartSound (pos,  0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0)


	elif typeIn == q_shared.temp_event_t.TE_RAILTRAIL:			# railgun effect
		pos = common.MSG_ReadPos (net_chan.net_message)
		pos2 = common.MSG_ReadPos (net_chan.net_message)
		cl_fx.CL_RailTrail (pos, pos2)
		snd_dma.S_StartSound (pos2, 0, 0, cl_sfx_railg, 1, q_shared.ATTN_NORM, 0);

		
	elif typeIn in [q_shared.temp_event_t.TE_EXPLOSION2,
		q_shared.temp_event_t.TE_GRENADE_EXPLOSION,
		q_shared.temp_event_t.TE_GRENADE_EXPLOSION_WATER]:

		pos = common.MSG_ReadPos (net_chan.net_message)

		ex = CL_AllocExplosion ()
		q_shared.VectorCopy (pos, ex.ent.origin)
		ex.typeval = exptype_t.ex_poly
		ex.ent.flags = q_shared.RF_FULLBRIGHT
		ex.start = cl_main.cl.frame.servertime - 100
		ex.light = 350
		ex.lightcolor[0] = 1.0
		ex.lightcolor[1] = 0.5
		ex.lightcolor[2] = 0.5
		ex.ent.model = cl_mod_explo4
		ex.frames = 19
		ex.baseframe = 30
		ex.ent.angles[1] = random.randint(0, 359)
		cl_fx.CL_ExplosionParticles (pos)
		if typeIn == q_shared.temp_event_t.TE_GRENADE_EXPLOSION_WATER:
			snd_dma.S_StartSound (pos, 0, 0, cl_sfx_watrexp, 1, q_shared.ATTN_NORM, 0)
		else:
			snd_dma.S_StartSound (pos, 0, 0, cl_sfx_grenexp, 1, q_shared.ATTN_NORM, 0)

		"""
	// RAFAEL
	case TE_PLASMA_EXPLOSION:
		MSG_ReadPos (&net_chan.net_message, pos);
		ex = CL_AllocExplosion ();
		q_shared.VectorCopy (pos, ex.ent.origin);
		ex.typeval = exptype_t.ex_poly;
		ex.ent.flags = q_shared.RF_FULLBRIGHT;
		ex.start = cl_main.cl.frame.servertime - 100;
		ex.light = 350;
		ex.lightcolor[0] = 1.0; 
		ex.lightcolor[1] = 0.5;
		ex.lightcolor[2] = 0.5;
		ex.ent.angles[1] = rand() % 360;
		ex.ent.model = cl_mod_explo4;
		if (frand() < 0.5)
			ex.baseframe = 15;
		ex.frames = 15;
		cl_fx.CL_ExplosionParticles (pos);
		snd_dma.S_StartSound (pos, 0, 0, cl_sfx_rockexp, 1, q_shared.ATTN_NORM, 0);
		break;
	"""	
	elif typeIn in [q_shared.temp_event_t.TE_EXPLOSION1,
		q_shared.temp_event_t.TE_EXPLOSION1_BIG,
		q_shared.temp_event_t.TE_ROCKET_EXPLOSION,
		q_shared.temp_event_t.TE_ROCKET_EXPLOSION_WATER,
		q_shared.temp_event_t.TE_EXPLOSION1_NP]:

		pos = common.MSG_ReadPos (net_chan.net_message)

		ex = CL_AllocExplosion ()
		q_shared.VectorCopy (pos, ex.ent.origin)
		ex.typeval = exptype_t.ex_poly
		ex.ent.flags = q_shared.RF_FULLBRIGHT
		ex.start = cl_main.cl.frame.servertime - 100
		ex.light = 350
		ex.lightcolor[0] = 1.0
		ex.lightcolor[1] = 0.5
		ex.lightcolor[2] = 0.5
		ex.ent.angles[1] = random.randint(0, 359)
		if typeIn != q_shared.temp_event_t.TE_EXPLOSION1_BIG:				# PMM
			ex.ent.model = cl_mod_explo4			# PMM
		else:
			ex.ent.model = cl_mod_explo4_big
		if random.uniform(0, 1) < 0.5:
			ex.baseframe = 15
		ex.frames = 15
		if (typeIn != q_shared.temp_event_t.TE_EXPLOSION1_BIG) and (typeIn != q_shared.temp_event_t.TE_EXPLOSION1_NP):		# PMM
			cl_fx.CL_ExplosionParticles (pos)								# PMM
		if typeIn == q_shared.temp_event_t.TE_ROCKET_EXPLOSION_WATER:
			snd_dma.S_StartSound (pos, 0, 0, cl_sfx_watrexp, 1, q_shared.ATTN_NORM, 0)
		else:
			snd_dma.S_StartSound (pos, 0, 0, cl_sfx_rockexp, 1, q_shared.ATTN_NORM, 0)


		"""
	case TE_BFG_EXPLOSION:
		MSG_ReadPos (&net_chan.net_message, pos);
		ex = CL_AllocExplosion ();
		q_shared.VectorCopy (pos, ex.ent.origin);
		ex.typeval = exptype_t.ex_poly;
		ex.ent.flags = q_shared.RF_FULLBRIGHT;
		ex.start = cl_main.cl.frame.servertime - 100;
		ex.light = 350;
		ex.lightcolor[0] = 0.0;
		ex.lightcolor[1] = 1.0;
		ex.lightcolor[2] = 0.0;
		ex.ent.model = cl_mod_bfg_explo;
		ex.ent.flags |= q_shared.RF_TRANSLUCENT;
		ex.ent.alpha = 0.30;
		ex.frames = 4;
		break;

	case TE_BFG_BIGEXPLOSION:
		MSG_ReadPos (&net_chan.net_message, pos);
		CL_BFGExplosionParticles (pos);
		break;

	case TE_BFG_LASER:
		CL_ParseLaser (0xd0d1d2d3);
		break;

	case TE_BUBBLETRAIL:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadPos (&net_chan.net_message, pos2);
		CL_BubbleTrail (pos, pos2);
		break;

	case TE_PARASITE_ATTACK:
	case TE_MEDIC_CABLE_ATTACK:
		ent = CL_ParseBeam (cl_mod_parasite_segment);
		break;

	case TE_BOSSTPORT:			// boss teleporting to station
		MSG_ReadPos (&net_chan.net_message, pos);
		CL_BigTeleportParticles (pos);
		snd_dma.S_StartSound (pos, 0, 0, S_RegisterSound ("misc/bigtele.wav"), 1, ATTN_NONE, 0);
		break;

	case TE_GRAPPLE_CABLE:
		ent = CL_ParseBeam2 (cl_mod_grapple_cable);
		break;

	// RAFAEL
	case TE_WELDING_SPARKS:
		cnt = MSG_ReadByte (&net_chan.net_message);
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		color = MSG_ReadByte (&net_chan.net_message);
		cl_fx.CL_ParticleEffect2 (pos, dir, color, cnt);

		ex = CL_AllocExplosion ();
		q_shared.VectorCopy (pos, ex.ent.origin);
		ex.typeval = ex_flash;
		// note to self
		// we need a better no draw flag
		ex.ent.flags = RF_BEAM;
		ex.start = cl_main.cl.frame.servertime - 0.1;
		ex.light = 100 + (rand()%75);
		ex.lightcolor[0] = 1.0;
		ex.lightcolor[1] = 1.0;
		ex.lightcolor[2] = 0.3;
		ex.ent.model = cl_mod_flash;
		ex.frames = 2;
		break;

	case TE_GREENBLOOD:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		cl_fx.CL_ParticleEffect2 (pos, dir, 0xdf, 30);
		break;

	// RAFAEL
	case TE_TUNNEL_SPARKS:
		cnt = MSG_ReadByte (&net_chan.net_message);
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		color = MSG_ReadByte (&net_chan.net_message);
		cl_fx.CL_ParticleEffect3 (pos, dir, color, cnt);
		break;

//=============
//PGM
		// PMM -following code integrated for flechette (different color)
	case TE_BLASTER2:			// green blaster hitting wall
	case TE_FLECHETTE:			// flechette
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		
		// PMM
		if (type == TE_BLASTER2)
			CL_BlasterParticles2 (pos, dir, 0xd0);
		else
			CL_BlasterParticles2 (pos, dir, 0x6f); // 75

		ex = CL_AllocExplosion ();
		q_shared.VectorCopy (pos, ex.ent.origin);
		ex.ent.angles[0] = acos(dir[2])/M_PI*180;
	// PMM - fixed to correct for pitch of 0
		if (dir[0])
			ex.ent.angles[1] = math.atan2(dir[1], dir[0])/M_PI*180;
		else if (dir[1] > 0)
			ex.ent.angles[1] = 90;
		else if (dir[1] < 0)
			ex.ent.angles[1] = 270;
		else
			ex.ent.angles[1] = 0;

		ex.typeval = ex_misc;
		ex.ent.flags = q_shared.RF_FULLBRIGHT|q_shared.RF_TRANSLUCENT;

		// PMM
		if (type == TE_BLASTER2)
			ex.ent.skinnum = 1;
		else // flechette
			ex.ent.skinnum = 2;

		ex.start = cl_main.cl.frame.servertime - 100;
		ex.light = 150;
		// PMM
		if (type == TE_BLASTER2)
			ex.lightcolor[1] = 1;
		else // flechette
		{
			ex.lightcolor[0] = 0.19;
			ex.lightcolor[1] = 0.41;
			ex.lightcolor[2] = 0.75;
		}
		ex.ent.model = cl_mod_explode;
		ex.frames = 4;
		snd_dma.S_StartSound (pos,  0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
		break;


	case TE_LIGHTNING:
		ent = CL_ParseLightning (cl_mod_lightning);
		snd_dma.S_StartSound (NULL, ent, CHAN_WEAPON, cl_sfx_lightning, 1, q_shared.ATTN_NORM, 0);
		break;

	case TE_DEBUGTRAIL:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadPos (&net_chan.net_message, pos2);
		CL_DebugTrail (pos, pos2);
		break;

	case TE_PLAIN_EXPLOSION:
		MSG_ReadPos (&net_chan.net_message, pos);

		ex = CL_AllocExplosion ();
		q_shared.VectorCopy (pos, ex.ent.origin);
		ex.typeval = exptype_t.ex_poly;
		ex.ent.flags = q_shared.RF_FULLBRIGHT;
		ex.start = cl_main.cl.frame.servertime - 100;
		ex.light = 350;
		ex.lightcolor[0] = 1.0;
		ex.lightcolor[1] = 0.5;
		ex.lightcolor[2] = 0.5;
		ex.ent.angles[1] = rand() % 360;
		ex.ent.model = cl_mod_explo4;
		if (frand() < 0.5)
			ex.baseframe = 15;
		ex.frames = 15;
		if (type == TE_ROCKET_EXPLOSION_WATER)
			snd_dma.S_StartSound (pos, 0, 0, cl_sfx_watrexp, 1, q_shared.ATTN_NORM, 0);
		else
			snd_dma.S_StartSound (pos, 0, 0, cl_sfx_rockexp, 1, q_shared.ATTN_NORM, 0);
		break;

	case TE_FLASHLIGHT:
		MSG_ReadPos(&net_chan.net_message, pos);
		ent = MSG_ReadShort(&net_chan.net_message);
		CL_Flashlight(ent, pos);
		break;

	case TE_FORCEWALL:
		MSG_ReadPos(&net_chan.net_message, pos);
		MSG_ReadPos(&net_chan.net_message, pos2);
		color = MSG_ReadByte (&net_chan.net_message);
		CL_ForceWall(pos, pos2, color);
		break;

	case TE_HEATBEAM:
		ent = CL_ParsePlayerBeam (cl_mod_heatbeam);
		break;

	case TE_MONSTER_HEATBEAM:
		ent = CL_ParsePlayerBeam (cl_mod_monster_heatbeam);
		break;

	case TE_HEATBEAM_SPARKS:
//		cnt = MSG_ReadByte (&net_chan.net_message);
		cnt = 50;
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
//		r = MSG_ReadByte (&net_chan.net_message);
//		magnitude = MSG_ReadShort (&net_chan.net_message);
		r = 8;
		magnitude = 60;
		color = r & 0xff;
		CL_ParticleSteamEffect (pos, dir, color, cnt, magnitude);
		snd_dma.S_StartSound (pos,  0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
		break;
	
	case TE_HEATBEAM_STEAM:
//		cnt = MSG_ReadByte (&net_chan.net_message);
		cnt = 20;
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
//		r = MSG_ReadByte (&net_chan.net_message);
//		magnitude = MSG_ReadShort (&net_chan.net_message);
//		color = r & 0xff;
		color = 0xe0;
		magnitude = 60;
		CL_ParticleSteamEffect (pos, dir, color, cnt, magnitude);
		snd_dma.S_StartSound (pos,  0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
		break;

	case TE_STEAM:
		CL_ParseSteam();
		break;

	case TE_BUBBLETRAIL2:
//		cnt = MSG_ReadByte (&net_chan.net_message);
		cnt = 8;
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadPos (&net_chan.net_message, pos2);
		CL_BubbleTrail2 (pos, pos2, cnt);
		snd_dma.S_StartSound (pos,  0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
		break;

	case TE_MOREBLOOD:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
		cl_fx.CL_ParticleEffect (pos, dir, 0xe8, 250);
		break;

	case TE_CHAINFIST_SMOKE:
		dir[0]=0; dir[1]=0; dir[2]=1;
		MSG_ReadPos(&net_chan.net_message, pos);
		CL_ParticleSmokeEffect (pos, dir, 0, 20, 20);
		break;

	case TE_ELECTRIC_SPARKS:
		MSG_ReadPos (&net_chan.net_message, pos);
		MSG_ReadDir (&net_chan.net_message, dir);
//		cl_fx.CL_ParticleEffect (pos, dir, 109, 40);
		cl_fx.CL_ParticleEffect (pos, dir, 0x75, 40);
		//FIXME : replace or remove this sound
		snd_dma.S_StartSound (pos, 0, 0, cl_sfx_lashit, 1, q_shared.ATTN_NORM, 0);
		break;

	case TE_TRACKER_EXPLOSION:
		MSG_ReadPos (&net_chan.net_message, pos);
		CL_ColorFlash (pos, 0, 150, -1, -1, -1);
		CL_ColorExplosionParticles (pos, 0, 1);
//		CL_Tracker_Explode (pos);
		snd_dma.S_StartSound (pos, 0, 0, cl_sfx_disrexp, 1, q_shared.ATTN_NORM, 0);
		break;

	case TE_TELEPORT_EFFECT:
	case TE_DBALL_GOAL:
		MSG_ReadPos (&net_chan.net_message, pos);
		CL_TeleportParticles (pos);
		break;

	case TE_WIDOWBEAMOUT:
		CL_ParseWidow ();
		break;

	case TE_NUKEBLAST:
		CL_ParseNuke ();
		break;

	case TE_WIDOWSPLASH:
		MSG_ReadPos (&net_chan.net_message, pos);
		CL_WidowSplash (pos);
		break;
//PGM
//==============
	"""
	else:
		print (typeIn)
		common.Com_Error (q_shared.ERR_DROP, "CL_ParseTEnt: bad type")



"""
=================
CL_AddBeams
=================
*/
void CL_AddBeams (void)
{
	int			i,j;
	beam_t		*b;
	vec3_t		dist, org;
	float		d;
	entity_t	ent;
	float		yaw, pitch;
	float		forward;
	float		len, steps;
	float		model_length;
	
// update beams
	for (i=0, b=cl_beams ; i< MAX_BEAMS ; i++, b++)
	{
		if (!b->model || b->endtime < cl.time)
			continue;

		// if coming from the player, update the start position
		if (b->entity == cl.playernum+1)	// entity 0 is the world
		{
			q_shared.VectorCopy (cl.refdef.vieworg, b->start);
			b->start[2] -= 22;	// adjust for view height
		}
		VectorAdd (b->start, b->offset, org);

	// calculate pitch and yaw
		VectorSubtract (b->end, org, dist);

		if (dist[1] == 0 && dist[0] == 0)
		{
			yaw = 0;
			if (dist[2] > 0)
				pitch = 90;
			else
				pitch = 270;
		}
		else
		{
	// PMM - fixed to correct for pitch of 0
			if (dist[0])
				yaw = (math.atan2(dist[1], dist[0]) * 180 / M_PI);
			else if (dist[1] > 0)
				yaw = 90;
			else
				yaw = 270;
			if (yaw < 0)
				yaw += 360;
	
			forward = sqrt (dist[0]*dist[0] + dist[1]*dist[1]);
			pitch = (math.atan2(dist[2], forward) * -180.0 / M_PI);
			if (pitch < 0)
				pitch += 360.0;
		}

	// add new entities for the beams
		d = VectorNormalize(dist);

		memset (&ent, 0, sizeof(ent));
		if (b->model == cl_mod_lightning)
		{
			model_length = 35.0;
			d-= 20.0;  // correction so it doesn't end in middle of tesla
		}
		else
		{
			model_length = 30.0;
		}
		steps = ceil(d/model_length);
		len = (d-model_length)/(steps-1);

		// PMM - special case for lightning model .. if the real length is shorter than the model,
		// flip it around & draw it from the end to the start.  This prevents the model from going
		// through the tesla mine (instead it goes through the target)
		if ((b->model == cl_mod_lightning) && (d <= model_length))
		{
//			Com_Printf ("special case\n");
			q_shared.VectorCopy (b->end, ent.origin);
			// offset to push beam outside of tesla model (negative because dist is from end to start
			// for this beam)
//			for (j=0 ; j<3 ; j++)
//				ent.origin[j] -= dist[j]*10.0;
			ent.model = b->model;
			ent.flags = q_shared.RF_FULLBRIGHT;
			ent.angles[0] = pitch;
			ent.angles[1] = yaw;
			ent.angles[2] = rand()%360;
			V_AddEntity (&ent);			
			return;
		}
		while (d > 0)
		{
			q_shared.VectorCopy (org, ent.origin);
			ent.model = b->model;
			if (b->model == cl_mod_lightning)
			{
				ent.flags = q_shared.RF_FULLBRIGHT;
				ent.angles[0] = -pitch;
				ent.angles[1] = yaw + 180.0;
				ent.angles[2] = rand()%360;
			}
			else
			{
				ent.angles[0] = pitch;
				ent.angles[1] = yaw;
				ent.angles[2] = rand()%360;
			}
			
//			Com_Printf("B: %d -> %d\n", b->entity, b->dest_entity);
			V_AddEntity (&ent);

			for (j=0 ; j<3 ; j++)
				org[j] += dist[j]*len;
			d -= model_length;
		}
	}
}


/*
//				Com_Printf ("Endpoint:  %f %f %f\n", b->end[0], b->end[1], b->end[2]);
//				Com_Printf ("Pred View Angles:  %f %f %f\n", cl.predicted_angles[0], cl.predicted_angles[1], cl.predicted_angles[2]);
//				Com_Printf ("Act View Angles: %f %f %f\n", cl.refdef.viewangles[0], cl.refdef.viewangles[1], cl.refdef.viewangles[2]);
//				q_shared.VectorCopy (cl.predicted_origin, b->start);
//				b->start[2] += 22;	// adjust for view height
//				if (fabs(cl.refdef.vieworg[2] - b->start[2]) >= 10) {
//					b->start[2] = cl.refdef.vieworg[2];
//				}

//				Com_Printf ("Time:  %d %d %f\n", cl.time, cls.realtime, cls.frametime);
*/

extern cvar_t *hand;

/*
=================
ROGUE - draw player locked beams
CL_AddPlayerBeams
=================
*/
void CL_AddPlayerBeams (void)
{
	int			i,j;
	beam_t		*b;
	vec3_t		dist, org;
	float		d;
	entity_t	ent;
	float		yaw, pitch;
	float		forward;
	float		len, steps;
	int			framenum;
	float		model_length;
	
	float		hand_multiplier;
	frame_t		*oldframe;
	player_state_t	*ps, *ops;

//PMM
	if (hand)
	{
		if (hand->value == 2)
			hand_multiplier = 0;
		else if (hand->value == 1)
			hand_multiplier = -1;
		else
			hand_multiplier = 1;
	}
	else 
	{
		hand_multiplier = 1;
	}
//PMM

// update beams
	for (i=0, b=cl_playerbeams ; i< MAX_BEAMS ; i++, b++)
	{
		vec3_t		f,r,u;
		if (!b->model || b->endtime < cl.time)
			continue;

		if(cl_mod_heatbeam && (b->model == cl_mod_heatbeam))
		{

			// if coming from the player, update the start position
			if (b->entity == cl.playernum+1)	// entity 0 is the world
			{	
				// set up gun position
				// code straight out of CL_AddViewWeapon
				ps = &cl_main.cl.frame.playerstate;
				j = (cl_main.cl.frame.serverframe - 1) & UPDATE_MASK;
				oldframe = &cl.frames[j];
				if (oldframe->serverframe != cl_main.cl.frame.serverframe-1 || !oldframe->valid)
					oldframe = &cl.frame;		// previous frame was dropped or involid
				ops = &oldframe->playerstate;
				for (j=0 ; j<3 ; j++)
				{
					b->start[j] = cl.refdef.vieworg[j] + ops->gunoffset[j]
						+ cl.lerpfrac * (ps->gunoffset[j] - ops->gunoffset[j]);
				}
				VectorMA (b->start, (hand_multiplier * b->offset[0]), cl.v_right, org);
				VectorMA (     org, b->offset[1], cl.v_forward, org);
				VectorMA (     org, b->offset[2], cl.v_up, org);
				if ((hand) && (hand->value == 2)) {
					VectorMA (org, -1, cl.v_up, org);
				}
				// FIXME - take these out when final
				q_shared.VectorCopy (cl.v_right, r);
				q_shared.VectorCopy (cl.v_forward, f);
				q_shared.VectorCopy (cl.v_up, u);

			}
			else
				q_shared.VectorCopy (b->start, org);
		}
		else
		{
			// if coming from the player, update the start position
			if (b->entity == cl.playernum+1)	// entity 0 is the world
			{
				q_shared.VectorCopy (cl.refdef.vieworg, b->start);
				b->start[2] -= 22;	// adjust for view height
			}
			VectorAdd (b->start, b->offset, org);
		}

	// calculate pitch and yaw
		VectorSubtract (b->end, org, dist);

//PMM
		if(cl_mod_heatbeam && (b->model == cl_mod_heatbeam) && (b->entity == cl.playernum+1))
		{
			vec_t len;

			len = VectorLength (dist);
			VectorScale (f, len, dist);
			VectorMA (dist, (hand_multiplier * b->offset[0]), r, dist);
			VectorMA (dist, b->offset[1], f, dist);
			VectorMA (dist, b->offset[2], u, dist);
			if ((hand) && (hand->value == 2)) {
				VectorMA (org, -1, cl.v_up, org);
			}
		}
//PMM

		if (dist[1] == 0 && dist[0] == 0)
		{
			yaw = 0;
			if (dist[2] > 0)
				pitch = 90;
			else
				pitch = 270;
		}
		else
		{
	// PMM - fixed to correct for pitch of 0
			if (dist[0])
				yaw = (math.atan2(dist[1], dist[0]) * 180 / M_PI);
			else if (dist[1] > 0)
				yaw = 90;
			else
				yaw = 270;
			if (yaw < 0)
				yaw += 360;
	
			forward = sqrt (dist[0]*dist[0] + dist[1]*dist[1]);
			pitch = (math.atan2(dist[2], forward) * -180.0 / M_PI);
			if (pitch < 0)
				pitch += 360.0;
		}
		
		if (cl_mod_heatbeam && (b->model == cl_mod_heatbeam))
		{
			if (b->entity != cl.playernum+1)
			{
				framenum = 2;
//				Com_Printf ("Third person\n");
				ent.angles[0] = -pitch;
				ent.angles[1] = yaw + 180.0;
				ent.angles[2] = 0;
//				Com_Printf ("%f %f - %f %f %f\n", -pitch, yaw+180.0, b->offset[0], b->offset[1], b->offset[2]);
				AngleVectors(ent.angles, f, r, u);
					
				// if it's a non-origin offset, it's a player, so use the hardcoded player offset
				if (!VectorCompare (b->offset, vec3_origin))
				{
					VectorMA (org, -(b->offset[0])+1, r, org);
					VectorMA (org, -(b->offset[1]), f, org);
					VectorMA (org, -(b->offset[2])-10, u, org);
				}
				else
				{
					// if it's a monster, do the particle effect
					CL_MonsterPlasma_Shell(b->start);
				}
			}
			else
			{
				framenum = 1;
			}
		}

		// if it's the heatbeam, draw the particle effect
		if ((cl_mod_heatbeam && (b->model == cl_mod_heatbeam) && (b->entity == cl.playernum+1)))
		{
			CL_Heatbeam (org, dist);
		}

	// add new entities for the beams
		d = VectorNormalize(dist);

		memset (&ent, 0, sizeof(ent));
		if (b->model == cl_mod_heatbeam)
		{
			model_length = 32.0;
		}
		else if (b->model == cl_mod_lightning)
		{
			model_length = 35.0;
			d-= 20.0;  // correction so it doesn't end in middle of tesla
		}
		else
		{
			model_length = 30.0;
		}
		steps = ceil(d/model_length);
		len = (d-model_length)/(steps-1);

		// PMM - special case for lightning model .. if the real length is shorter than the model,
		// flip it around & draw it from the end to the start.  This prevents the model from going
		// through the tesla mine (instead it goes through the target)
		if ((b->model == cl_mod_lightning) && (d <= model_length))
		{
//			Com_Printf ("special case\n");
			q_shared.VectorCopy (b->end, ent.origin);
			// offset to push beam outside of tesla model (negative because dist is from end to start
			// for this beam)
//			for (j=0 ; j<3 ; j++)
//				ent.origin[j] -= dist[j]*10.0;
			ent.model = b->model;
			ent.flags = q_shared.RF_FULLBRIGHT;
			ent.angles[0] = pitch;
			ent.angles[1] = yaw;
			ent.angles[2] = rand()%360;
			V_AddEntity (&ent);			
			return;
		}
		while (d > 0)
		{
			q_shared.VectorCopy (org, ent.origin);
			ent.model = b->model;
			if(cl_mod_heatbeam && (b->model == cl_mod_heatbeam))
			{
//				ent.flags = q_shared.RF_FULLBRIGHT|q_shared.RF_TRANSLUCENT;
//				ent.alpha = 0.3;
				ent.flags = q_shared.RF_FULLBRIGHT;
				ent.angles[0] = -pitch;
				ent.angles[1] = yaw + 180.0;
				ent.angles[2] = (cl.time) % 360;
//				ent.angles[2] = rand()%360;
				ent.frame = framenum;
			}
			else if (b->model == cl_mod_lightning)
			{
				ent.flags = q_shared.RF_FULLBRIGHT;
				ent.angles[0] = -pitch;
				ent.angles[1] = yaw + 180.0;
				ent.angles[2] = rand()%360;
			}
			else
			{
				ent.angles[0] = pitch;
				ent.angles[1] = yaw;
				ent.angles[2] = rand()%360;
			}
			
//			Com_Printf("B: %d -> %d\n", b->entity, b->dest_entity);
			V_AddEntity (&ent);

			for (j=0 ; j<3 ; j++)
				org[j] += dist[j]*len;
			d -= model_length;
		}
	}
}

/*
=================
CL_AddExplosions
=================
*/
void CL_AddExplosions (void)
{
	entity_t	*ent;
	int			i;
	explosion_t	*ex;
	float		frac;
	int			f;

	memset (&ent, 0, sizeof(ent));

	for (i=0, ex=cl_explosions ; i< MAX_EXPLOSIONS ; i++, ex++)
	{
		if (ex.typeval == ex_free)
			continue;
		frac = (cl.time - ex.start)/100.0;
		f = floor(frac);

		ent = &ex.ent;

		switch (ex.type)
		{
		case ex_mflash:
			if (f >= ex.frames-1)
				ex.typeval = ex_free;
			break;
		case ex_misc:
			if (f >= ex.frames-1)
			{
				ex.typeval = ex_free;
				break;
			}
			ent->alpha = 1.0 - frac/(ex.frames-1);
			break;
		case ex_flash:
			if (f >= 1)
			{
				ex.typeval = ex_free;
				break;
			}
			ent->alpha = 1.0;
			break;
		case exptype_t.ex_poly:
			if (f >= ex.frames-1)
			{
				ex.typeval = ex_free;
				break;
			}

			ent->alpha = (16.0 - (float)f)/16.0;

			if (f < 10)
			{
				ent->skinnum = (f>>1);
				if (ent->skinnum < 0)
					ent->skinnum = 0;
			}
			else
			{
				ent->flags |= q_shared.RF_TRANSLUCENT;
				if (f < 13)
					ent->skinnum = 5;
				else
					ent->skinnum = 6;
			}
			break;
		case exptype_t.ex_poly2:
			if (f >= ex.frames-1)
			{
				ex.typeval = ex_free;
				break;
			}

			ent->alpha = (5.0 - (float)f)/5.0;
			ent->skinnum = 0;
			ent->flags |= q_shared.RF_TRANSLUCENT;
			break;
		}

		if (ex.typeval == ex_free)
			continue;
		if (ex.light)
		{
			V_AddLight (ent->origin, ex.light*ent->alpha,
				ex.lightcolor[0], ex.lightcolor[1], ex.lightcolor[2]);
		}

		q_shared.VectorCopy (ent->origin, ent->oldorigin);

		if (f < 0)
			f = 0;
		ent->frame = ex.baseframe + f + 1;
		ent->oldframe = ex.baseframe + f;
		ent->backlerp = 1.0 - cl.lerpfrac;

		V_AddEntity (ent);
	}
}


/*
=================
CL_AddLasers
=================
*/
void CL_AddLasers (void)
{
	laser_t		*l;
	int			i;

	for (i=0, l=cl_lasers ; i< MAX_LASERS ; i++, l++)
	{
		if (l->endtime >= cl.time)
			V_AddEntity (&l->ent);
	}
}

/* PMM - CL_Sustains */
void CL_ProcessSustain ()
{
	cl_sustain_t	*s;
	int				i;

	for (i=0, s=cl_sustains; i< MAX_SUSTAINS; i++, s++)
	{
		if (s->id)
			if ((s->endtime >= cl.time) && (cl.time >= s->nextthink))
			{
//				Com_Printf ("think %d %d %d\n", cl.time, s->nextthink, s->thinkinterval);
				s->think (s);
			}
			else if (s->endtime < cl.time)
				s->id = 0;
	}
}

/*
=================
CL_AddTEnts
=================
"""
def CL_AddTEnts ():

	print ("CL_AddTEnts")
	"""
	CL_AddBeams ()
	// PMM - draw plasma beams
	CL_AddPlayerBeams ()
	CL_AddExplosions ()
	CL_AddLasers ()
	// PMM - set up sustain
	CL_ProcessSustain()

	"""
