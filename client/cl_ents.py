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
import copy
from qcommon import common, net_chan, qcommon
from game import q_shared
from client import cl_main, cl_parse, client, cl_pred
"""
// cl_ents.c -- entity parsing and management

#include "client.h"


extern	struct model_s	*cl_mod_powerscreen;

//PGM
int	vidref_val;
//PGM

/*
=========================================================================

FRAME PARSING

=========================================================================
*/

#if 0

typedef struct
{
	int		modelindex;
	int		num; // entity number
	int		effects;
	vec3_t	origin;
	vec3_t	oldorigin;
	vec3_t	angles;
	qboolean present;
} projectile_t;

#define	MAX_PROJECTILES	64
projectile_t	cl_projectiles[MAX_PROJECTILES];

void CL_ClearProjectiles (void)
{
	int i;

	for (i = 0; i < MAX_PROJECTILES; i++) {
//		if (cl_projectiles[i].present)
//			Com_DPrintf("PROJ: %d CLEARED\n", cl_projectiles[i].num);
		cl_projectiles[i].present = false;
	}
}

/*
=====================
CL_ParseProjectiles

Flechettes are passed as efficient temporary entities
=====================
*/
void CL_ParseProjectiles (void)
{
	int		i, c, j;
	byte	bits[8];
	byte	b;
	projectile_t	pr;
	int lastempty = -1;
	qboolean old = false;

	c = MSG_ReadByte (&net_chan.net_message);
	for (i=0 ; i<c ; i++)
	{
		bits[0] = MSG_ReadByte (&net_chan.net_message);
		bits[1] = MSG_ReadByte (&net_chan.net_message);
		bits[2] = MSG_ReadByte (&net_chan.net_message);
		bits[3] = MSG_ReadByte (&net_chan.net_message);
		bits[4] = MSG_ReadByte (&net_chan.net_message);
		pr.origin[0] = ( ( bits[0] + ((bits[1]&15)<<8) ) <<1) - 4096;
		pr.origin[1] = ( ( (bits[1]>>4) + (bits[2]<<4) ) <<1) - 4096;
		pr.origin[2] = ( ( bits[3] + ((bits[4]&15)<<8) ) <<1) - 4096;
		q_shared.VectorCopy(pr.origin, pr.oldorigin);

		if (bits[4] & 64)
			pr.effects = EF_BLASTER;
		else
			pr.effects = 0;

		if (bits[4] & 128) {
			old = true;
			bits[0] = MSG_ReadByte (&net_chan.net_message);
			bits[1] = MSG_ReadByte (&net_chan.net_message);
			bits[2] = MSG_ReadByte (&net_chan.net_message);
			bits[3] = MSG_ReadByte (&net_chan.net_message);
			bits[4] = MSG_ReadByte (&net_chan.net_message);
			pr.oldorigin[0] = ( ( bits[0] + ((bits[1]&15)<<8) ) <<1) - 4096;
			pr.oldorigin[1] = ( ( (bits[1]>>4) + (bits[2]<<4) ) <<1) - 4096;
			pr.oldorigin[2] = ( ( bits[3] + ((bits[4]&15)<<8) ) <<1) - 4096;
		}

		bits[0] = MSG_ReadByte (&net_chan.net_message);
		bits[1] = MSG_ReadByte (&net_chan.net_message);
		bits[2] = MSG_ReadByte (&net_chan.net_message);

		pr.angles[0] = 360*bits[0]/256;
		pr.angles[1] = 360*bits[1]/256;
		pr.modelindex = bits[2];

		b = MSG_ReadByte (&net_chan.net_message);
		pr.num = (b & 0x7f);
		if (b & 128) // extra entity number byte
			pr.num |= (MSG_ReadByte (&net_chan.net_message) << 7);

		pr.present = true;

		// find if this projectile already exists from previous frame 
		for (j = 0; j < MAX_PROJECTILES; j++) {
			if (cl_projectiles[j].modelindex) {
				if (cl_projectiles[j].num == pr.num) {
					// already present, set up oldorigin for interpolation
					if (!old)
						q_shared.VectorCopy(cl_projectiles[j].origin, pr.oldorigin);
					cl_projectiles[j] = pr;
					break;
				}
			} else
				lastempty = j;
		}

		// not present previous frame, add it
		if (j == MAX_PROJECTILES) {
			if (lastempty != -1) {
				cl_projectiles[lastempty] = pr;
			}
		}
	}
}

/*
=============
CL_LinkProjectiles

=============
*/
void CL_AddProjectiles (void)
{
	int		i, j;
	projectile_t	*pr;
	entity_t		ent;

	memset (&ent, 0, sizeof(ent));

	for (i=0, pr=cl_projectiles ; i < MAX_PROJECTILES ; i++, pr++)
	{
		// grab an entity to fill in
		if (pr.modelindex < 1)
			continue;
		if (!pr.present) {
			pr.modelindex = 0;
			continue; // not present this frame (it was in the previous frame)
		}

		ent.model = cl_main.cl.model_draw[pr.modelindex];

		// interpolate origin
		for (j=0 ; j<3 ; j++)
		{
			ent.origin[j] = ent.oldorigin[j] = pr.oldorigin[j] + cl_main.cl.lerpfrac * 
				(pr.origin[j] - pr.oldorigin[j]);

		}

		if (pr.effects & EF_BLASTER)
			CL_BlasterTrail (pr.oldorigin, ent.origin);
		V_AddLight (pr.origin, 200, 1, 1, 0);

		q_shared.VectorCopy (pr.angles, ent.angles);
		V_AddEntity (&ent);
	}
}
#endif

/*
=================
CL_ParseEntityBits

Returns the entity number and the header bits
=================
"""
bitcounts = [] #int[32], just for protocol profilingf
for i in range(32):
	bitcounts.append(0)

def CL_ParseEntityBits (): # (unsigned *bits)

	"""
	unsigned	b, total;
	int			i;
	int			number;
	"""

	total = common.MSG_ReadByte (net_chan.net_message)
	if total & qcommon.U_MOREBITS1:
	
		b = common.MSG_ReadByte (net_chan.net_message)
		total |= b<<8
	
	if total & qcommon.U_MOREBITS2:
	
		b = common.MSG_ReadByte (net_chan.net_message)
		total |= b<<16
	
	if total & qcommon.U_MOREBITS3:
	
		b = common.MSG_ReadByte (net_chan.net_message)
		total |= b<<24
	

	# count the bits for net profiling
	for i in range(32):
		if total&(1<<i):
			bitcounts[i]+=1

	if total & qcommon.U_NUMBER16:
		number = common.MSG_ReadShort (net_chan.net_message)
	else:
		number = common.MSG_ReadByte (net_chan.net_message)

	return number, total


"""
==================
CL_ParseDelta

Can go from either a baseline or a previous packet_entity
==================
"""
def CL_ParseDelta (fromEnt, toEnt, number, bits): #entity_state_t *from, entity_state_t *to, int number, int bits

	# set everything to the state we are delta'ing from
	
	toEnt.copy(fromEnt)

	q_shared.VectorCopy (fromEnt.origin, toEnt.old_origin)
	toEnt.number = number

	if bits & qcommon.U_MODEL:
		toEnt.modelindex = common.MSG_ReadByte (net_chan.net_message)
	if bits & qcommon.U_MODEL2:
		toEnt.modelindex2 = common.MSG_ReadByte (net_chan.net_message)
	if bits & qcommon.U_MODEL3:
		toEnt.modelindex3 = common.MSG_ReadByte (net_chan.net_message)
	if bits & qcommon.U_MODEL4:
		toEnt.modelindex4 = common.MSG_ReadByte (net_chan.net_message)
		
	if bits & qcommon.U_FRAME8:
		toEnt.frame = common.MSG_ReadByte (net_chan.net_message)
	if bits & qcommon.U_FRAME16:
		toEnt.frame = common.MSG_ReadShort (net_chan.net_message)

	if (bits & qcommon.U_SKIN8) and (bits & qcommon.U_SKIN16):		# used for laser colors
		toEnt.skinnum = common.MSG_ReadLong(net_chan.net_message)
	elif bits & qcommon.U_SKIN8:
		toEnt.skinnum = common.MSG_ReadByte(net_chan.net_message)
	elif bits & qcommon.U_SKIN16:
		toEnt.skinnum = common.MSG_ReadShort(net_chan.net_message)

	if (bits & (qcommon.U_EFFECTS8|qcommon.U_EFFECTS16)) == (qcommon.U_EFFECTS8|qcommon.U_EFFECTS16):
		toEnt.effects = common.MSG_ReadLong(net_chan.net_message)
	elif bits & qcommon.U_EFFECTS8:
		toEnt.effects = common.MSG_ReadByte(net_chan.net_message)
	elif bits & qcommon.U_EFFECTS16:
		toEnt.effects = common.MSG_ReadShort(net_chan.net_message)

	if (bits & (qcommon.U_RENDERFX8|qcommon.U_RENDERFX16)) == (qcommon.U_RENDERFX8|qcommon.U_RENDERFX16):
		toEnt.renderfx = common.MSG_ReadLong(net_chan.net_message)
	elif bits & qcommon.U_RENDERFX8:
		toEnt.renderfx = common.MSG_ReadByte(net_chan.net_message)
	elif bits & qcommon.U_RENDERFX16:
		toEnt.renderfx = common.MSG_ReadShort(net_chan.net_message)

	if bits & qcommon.U_ORIGIN1:
		toEnt.origin[0] = common.MSG_ReadCoord (net_chan.net_message)
	if bits & qcommon.U_ORIGIN2:
		toEnt.origin[1] = common.MSG_ReadCoord (net_chan.net_message)
	if bits & qcommon.U_ORIGIN3:
		toEnt.origin[2] = common.MSG_ReadCoord (net_chan.net_message)
		
	if bits & qcommon.U_ANGLE1:
		toEnt.angles[0] = common.MSG_ReadAngle(net_chan.net_message)
	if bits & qcommon.U_ANGLE2:
		toEnt.angles[1] = common.MSG_ReadAngle(net_chan.net_message)
	if bits & qcommon.U_ANGLE3:
		toEnt.angles[2] = common.MSG_ReadAngle(net_chan.net_message)

	if bits & qcommon.U_OLDORIGIN:
		toEnt.old_origin = common.MSG_ReadPos (net_chan.net_message)

	if bits & qcommon.U_SOUND:
		toEnt.sound = common.MSG_ReadByte (net_chan.net_message)

	if bits & qcommon.U_EVENT:
		toEnt.event = common.MSG_ReadByte (net_chan.net_message)
	else:
		toEnt.event = 0

	if bits & qcommon.U_SOLID:
		toEnt.solid = common.MSG_ReadShort (net_chan.net_message)


"""
==================
CL_DeltaEntity

Parses deltas from the given base and adds the resulting entity
to the current frame
==================
"""
def CL_DeltaEntity (frame, newnum, old, bits): #frame_t *, int, entity_state_t *, int

	"""
	centity_t	*ent;
	entity_state_t	*state;
	"""

	ent = cl_main.cl_entities[newnum]

	state = cl_main.cl_parse_entities[cl_main.cl.parse_entities & (client.MAX_PARSE_ENTITIES-1)]
	cl_main.cl.parse_entities+=1
	frame.num_entities+=1

	CL_ParseDelta (old, state, newnum, bits)

	# some data changes will force no lerping
	if (state.modelindex != ent.current.modelindex
		or state.modelindex2 != ent.current.modelindex2
		or state.modelindex3 != ent.current.modelindex3
		or state.modelindex4 != ent.current.modelindex4
		or abs(state.origin[0] - ent.current.origin[0]) > 512
		or abs(state.origin[1] - ent.current.origin[1]) > 512
		or abs(state.origin[2] - ent.current.origin[2]) > 512
		or state.event == q_shared.entity_event_t.EV_PLAYER_TELEPORT
		or state.event == q_shared.entity_event_t.EV_OTHER_TELEPORT
		):
	
		ent.serverframe = -99
	

	if ent.serverframe != cl_main.cl.frame.serverframe - 1:
		# wasn't in last update, so initialize some things
		ent.trailcount = 1024		# for diminishing rocket / grenade trails
		# duplicate the current state so lerping doesn't hurt anything
		ent.prev = copy.copy(state)
		if state.event == q_shared.entity_event_t.EV_OTHER_TELEPORT:
		
			q_shared.VectorCopy (state.origin, ent.prev.origin)
			q_shared.VectorCopy (state.origin, ent.lerp_origin)
		
		else:
		
			q_shared.VectorCopy (state.old_origin, ent.prev.origin)
			q_shared.VectorCopy (state.old_origin, ent.lerp_origin)
		
	
	else:
		# shuffle the last state to previous
		ent.prev = ent.current
	

	ent.serverframe = cl_main.cl.frame.serverframe
	ent.current = copy.copy(state)


"""
==================
CL_ParsePacketEntities

An svc_packetentities has just been parsed, deal with the
rest of the data stream.
==================
"""
def CL_ParsePacketEntities (oldframe, newframe): #frame_t *, frame_t *

	"""
	int			newnum;
	int			bits;
	entity_state_t	*oldstate;
	int			oldindex, oldnum;
	"""

	newframe.parse_entities = cl_main.cl.parse_entities
	newframe.num_entities = 0

	# delta from the entities present in oldframe
	oldindex = 0
	oldnum = 0
	oldstate = None
	if oldframe is None:
		oldnum = 99999
	else:
	
		if oldindex >= oldframe.num_entities:
			oldnum = 99999
		else:
			oldstate = cl_main.cl_parse_entities[(oldframe.parse_entities+oldindex) & (client.MAX_PARSE_ENTITIES-1)]
			oldnum = oldstate.number

	while 1:

		newnum, bits = CL_ParseEntityBits ()

		if newnum >= q_shared.MAX_EDICTS:
			common.Com_Error (q_shared.ERR_DROP,"CL_ParsePacketEntities: bad number:{}".format(newnum))

		if net_chan.net_message.readcount > net_chan.net_message.cursize:
			common.Com_Error (q_shared.ERR_DROP,"CL_ParsePacketEntities: end of message")

		if newnum==0:
			break

		while oldnum < newnum:

			# one or more entities from the old packet are unchanged
			if cl_main.cl_shownet.value == 3:
				common.Com_Printf ("   unchanged: {}\n".format(oldnum))

			CL_DeltaEntity (newframe, oldnum, oldstate, 0)
			
			oldindex+=1

			if oldindex >= oldframe.num_entities:
				oldnum = 99999
			else:
			
				oldstate = cl_main.cl_parse_entities[(oldframe.parse_entities+oldindex) & (client.MAX_PARSE_ENTITIES-1)]
				oldnum = oldstate.number
		

		if bits & qcommon.U_REMOVE:
			# the entity present in oldframe is not in the current frame
			if cl_main.cl_shownet.value == 3:
				common.Com_Printf ("   remove: {}\n".format(newnum))

			if oldnum != newnum:
				common.Com_Printf ("U_REMOVE: oldnum != newnum\n")

			oldindex+=1

			if oldindex >= oldframe.num_entities:
				oldnum = 99999
			else:
			
				oldstate = cl_main.cl_parse_entities[(oldframe.parse_entities+oldindex) & (client.MAX_PARSE_ENTITIES-1)]
				oldnum = oldstate.number
			
			continue
		

		if oldnum == newnum:
			# delta from previous state
			if cl_main.cl_shownet.value == 3:
				common.Com_Printf ("   delta: {}\n".format(newnum))

			CL_DeltaEntity (newframe, newnum, oldstate, bits)

			oldindex+=1

			if oldindex >= oldframe.num_entities:
				oldnum = 99999
			else:
			
				oldstate = cl_main.cl_parse_entities[(oldframe.parse_entities+oldindex) & (client.MAX_PARSE_ENTITIES-1)]
				oldnum = oldstate.number
			
			continue;
		

		if oldnum > newnum:
			# delta from baseline
			if cl_main.cl_shownet.value == 3:
				common.Com_Printf ("   baseline: {}\n".format(newnum))
			CL_DeltaEntity (newframe, newnum, cl_main.cl_entities[newnum].baseline, bits)
			continue

	# any remaining entities in the old frame are copied over
	while oldnum != 99999:

		# one or more entities from the old packet are unchanged
		if cl_main.cl_shownet.value == 3:
			common.Com_Printf ("   unchanged: {}\n".format(oldnum))

		CL_DeltaEntity (newframe, oldnum, oldstate, 0)
		
		oldindex+=1

		if oldindex >= oldframe.num_entities:
			oldnum = 99999
		else:
		
			oldstate = cl_main.cl_parse_entities[(oldframe.parse_entities+oldindex) & (client.MAX_PARSE_ENTITIES-1)]
			oldnum = oldstate.number
		




"""
===================
CL_ParsePlayerstate
===================
"""
def CL_ParsePlayerstate (oldframe, newframe): #frame_t *, frame_t *

	"""
	int			flags;
	player_state_t	*state;
	int			i;
	int			statbits;
	"""

	state = newframe.playerstate

	# clear to old value before delta parsing
	if oldframe:
		state = oldframe.playerstate
	else:
		state.clear()

	flags = common.MSG_ReadShort (net_chan.net_message)

	#
	# parse the pmove_state_t
	#
	if flags & qcommon.PS_M_TYPE:
		state.pmove.pm_type = common.MSG_ReadByte (net_chan.net_message)

	
	if flags & qcommon.PS_M_ORIGIN:
	
		state.pmove.origin[0] = common.MSG_ReadShort (net_chan.net_message)
		state.pmove.origin[1] = common.MSG_ReadShort (net_chan.net_message)
		state.pmove.origin[2] = common.MSG_ReadShort (net_chan.net_message)
	
	
	if flags & qcommon.PS_M_VELOCITY:
	
		state.pmove.velocity[0] = common.MSG_ReadShort (net_chan.net_message)
		state.pmove.velocity[1] = common.MSG_ReadShort (net_chan.net_message)
		state.pmove.velocity[2] = common.MSG_ReadShort (net_chan.net_message)
	

	if flags & qcommon.PS_M_TIME:
		state.pmove.pm_time = common.MSG_ReadByte (net_chan.net_message)

	if flags & qcommon.PS_M_FLAGS:
		state.pmove.pm_flags = common.MSG_ReadByte (net_chan.net_message)

	if flags & qcommon.PS_M_GRAVITY:
		state.pmove.gravity = common.MSG_ReadShort (net_chan.net_message)

	if flags & qcommon.PS_M_DELTA_ANGLES:
	
		state.pmove.delta_angles[0] = common.MSG_ReadShort (net_chan.net_message)
		state.pmove.delta_angles[1] = common.MSG_ReadShort (net_chan.net_message)
		state.pmove.delta_angles[2] = common.MSG_ReadShort (net_chan.net_message)
	

	if cl_main.cl.attractloop:
		state.pmove.pm_type = q_shared.pmtype_t.PM_FREEZE		# demo playback

	#
	# parse the rest of the player_state_t
	#
	if flags & qcommon.PS_VIEWOFFSET:
	
		state.viewoffset[0] = common.MSG_ReadChar (net_chan.net_message) * 0.25
		state.viewoffset[1] = common.MSG_ReadChar (net_chan.net_message) * 0.25
		state.viewoffset[2] = common.MSG_ReadChar (net_chan.net_message) * 0.25
	

	if flags & qcommon.PS_VIEWANGLES:
	
		state.viewangles[0] = common.MSG_ReadAngle16 (net_chan.net_message)
		state.viewangles[1] = common.MSG_ReadAngle16 (net_chan.net_message)
		state.viewangles[2] = common.MSG_ReadAngle16 (net_chan.net_message)
	

	if flags & qcommon.PS_KICKANGLES:
	
		state.kick_angles[0] = common.MSG_ReadChar (net_chan.net_message) * 0.25
		state.kick_angles[1] = common.MSG_ReadChar (net_chan.net_message) * 0.25
		state.kick_angles[2] = common.MSG_ReadChar (net_chan.net_message) * 0.25
	

	if flags & qcommon.PS_WEAPONINDEX:
	
		state.gunindex = common.MSG_ReadByte (net_chan.net_message)
	

	if flags & qcommon.PS_WEAPONFRAME:
	
		state.gunframe = common.MSG_ReadByte (net_chan.net_message)
		state.gunoffset[0] = common.MSG_ReadChar (net_chan.net_message)*0.25
		state.gunoffset[1] = common.MSG_ReadChar (net_chan.net_message)*0.25
		state.gunoffset[2] = common.MSG_ReadChar (net_chan.net_message)*0.25
		state.gunangles[0] = common.MSG_ReadChar (net_chan.net_message)*0.25
		state.gunangles[1] = common.MSG_ReadChar (net_chan.net_message)*0.25
		state.gunangles[2] = common.MSG_ReadChar (net_chan.net_message)*0.25
	

	if flags & qcommon.PS_BLEND:
	
		state.blend[0] = common.MSG_ReadByte (net_chan.net_message)/255.0
		state.blend[1] = common.MSG_ReadByte (net_chan.net_message)/255.0
		state.blend[2] = common.MSG_ReadByte (net_chan.net_message)/255.0
		state.blend[3] = common.MSG_ReadByte (net_chan.net_message)/255.0
	

	if flags & qcommon.PS_FOV:
		state.fov = common.MSG_ReadByte (net_chan.net_message)

	if flags & qcommon.PS_RDFLAGS:
		state.rdflags = common.MSG_ReadByte (net_chan.net_message)

	# parse stats
	statbits = common.MSG_ReadLong (net_chan.net_message)
	for i in range(q_shared.MAX_STATS):
		if statbits & (1<<i):
			state.stats[i] = common.MSG_ReadShort(net_chan.net_message)



"""
==================
CL_FireEntityEvents

==================
"""
def CL_FireEntityEvents (frame): #frame_t *

	print ("CL_FireEntityEvents")
	"""
	entity_state_t		*s1;
	int					pnum, num;

	for (pnum = 0 ; pnum<frame.num_entities ; pnum++)
	{
		num = (frame.parse_entities + pnum)&(client.MAX_PARSE_ENTITIES-1);
		s1 = &cl_main.cl_parse_entities[num];
		if (s1.event)
			CL_EntityEvent (s1);

		// EF_TELEPORTER acts like an event, but is not cleared each frame
		if (s1.effects & EF_TELEPORTER)
			CL_TeleporterParticles (s1);
	}
}


/*
================
CL_ParseFrame
================
"""
def CL_ParseFrame ():

	"""
	int			cmd;
	int			len;
	frame_t		*old;
	"""

	cl_main.cl.frame.clear()

#if 0
#	CL_ClearProjectiles(); // clear projectiles for new frame
#endif

	cl_main.cl.frame.serverframe = common.MSG_ReadSLong (net_chan.net_message)
	cl_main.cl.frame.deltaframe = common.MSG_ReadSLong (net_chan.net_message)
	cl_main.cl.frame.servertime = cl_main.cl.frame.serverframe*100

	# BIG HACK to let old demos continue to work
	if cl_main.cls.serverProtocol != 26:
		cl_main.cl.surpressCount = common.MSG_ReadByte (net_chan.net_message)

	if cl_main.cl_shownet.value == 3:
		common.Com_Printf ("   frame:{}  delta:{}\n".format(cl_main.cl.frame.serverframe,
			cl_main.cl.frame.deltaframe))

	# If the frame is delta compressed from data that we
	# no longer have available, we must suck up the rest of
	# the frame, but not use it, then ask for a non-compressed
	# message 
	if cl_main.cl.frame.deltaframe <= 0:
	
		cl_main.cl.frame.valid = True		# uncompressed frame
		old = None
		cl_main.cls.demowaiting = False	# we can start recording now
	
	else:
		old = cl_main.cl.frames[cl_main.cl.frame.deltaframe & qcommon.UPDATE_MASK]

		if not old.valid:
			# should never happen
			common.Com_Printf ("Delta from invalid frame (not supposed to happen!).\n");
		
		if old.serverframe != cl_main.cl.frame.deltaframe:
			# The frame that the server did the delta from
			# is too old, so we can't reconstruct it properly.
			common.Com_Printf ("Delta frame too old.\n")
		
		elif cl_main.cl.parse_entities - old.parse_entities > client.MAX_PARSE_ENTITIES-128:
		
			common.Com_Printf ("Delta parse_entities too old.\n")
		
		else:
			cl_main.cl.frame.valid = True	# valid delta parse
	
	
	# clamp time 
	if cl_main.cl.time > cl_main.cl.frame.servertime:
		cl_main.cl.time = cl_main.cl.frame.servertime
	elif cl_main.cl.time < cl_main.cl.frame.servertime - 100:
		cl_main.cl.time = cl_main.cl.frame.servertime - 100

	# read areabits
	length = common.MSG_ReadByte (net_chan.net_message)
	cl_main.cl.frame.areabits = common.MSG_ReadData (net_chan.net_message, length)

	# read playerinfo
	cmd = common.MSG_ReadByte (net_chan.net_message)
	cl_parse.SHOWNET(cl_parse.svc_strings[cmd])
	if cmd != qcommon.svc_ops_e.svc_playerinfo.value:
		common.Com_Error (q_shared.ERR_DROP, "CL_ParseFrame: not playerinfo")
	CL_ParsePlayerstate (old, cl_main.cl.frame)

	# read packet entities
	cmd = common.MSG_ReadByte (net_chan.net_message)
	cl_parse.SHOWNET(cl_parse.svc_strings[cmd])
	if cmd != qcommon.svc_ops_e.svc_packetentities.value:
		common.Com_Error (q_shared.ERR_DROP, "CL_ParseFrame: not packetentities")
	CL_ParsePacketEntities (old, cl_main.cl.frame)

#if 0
#	if (cmd == svc_packetentities2)
#		CL_ParseProjectiles()
#endif

	# save the frame off in the backup array for later delta comparisons
	cl_main.cl.frames[cl_main.cl.frame.serverframe & qcommon.UPDATE_MASK] = copy.copy(cl_main.cl.frame)

	if cl_main.cl.frame.valid:
	
		# getting a valid frame message ends the connection process
		if cl_main.cls.state != client.connstate_t.ca_active:
		
			cl_main.cls.state = client.connstate_t.ca_active
			cl_main.cl.force_refdef = True
			cl_main.cl.predicted_origin[0] = cl_main.cl.frame.playerstate.pmove.origin[0]*0.125
			cl_main.cl.predicted_origin[1] = cl_main.cl.frame.playerstate.pmove.origin[1]*0.125
			cl_main.cl.predicted_origin[2] = cl_main.cl.frame.playerstate.pmove.origin[2]*0.125
			q_shared.VectorCopy (cl_main.cl.frame.playerstate.viewangles, cl_main.cl.predicted_angles)
			if (cl_main.cls.disable_servercount != cl_main.cl.servercount
				and cl_main.cl.refresh_prepped):
				cl_scrn.SCR_EndLoadingPlaque ()	# get rid of loading plaque
		
		cl_main.cl.sound_prepped = True	# can start mixing ambient sounds
	
		# fire entity events
		CL_FireEntityEvents (cl_main.cl.frame)
		cl_pred.CL_CheckPredictionError ()
	


"""
==========================================================================

INTERPOLATE BETWEEN FRAMES TO GET RENDERING PARMS

==========================================================================
*/

struct model_s *S_RegisterSexedModel (entity_state_t *ent, char *base)
{
	int				n;
	char			*p;
	struct model_s	*mdl;
	char			model[MAX_QPATH];
	char			buffer[MAX_QPATH];

	// determine what model the client is using
	model[0] = 0;
	n = CS_PLAYERSKINS + ent.number - 1;
	if (cl_main.cl.configstrings[n][0])
	{
		p = strchr(cl_main.cl.configstrings[n], '\\');
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

	Com_sprintf (buffer, sizeof(buffer), "players/%s/%s", model, base+1);
	mdl = re.RegisterModel(buffer);
	if (!mdl) {
		// not found, try default weapon model
		Com_sprintf (buffer, sizeof(buffer), "players/%s/weapon.md2", model);
		mdl = re.RegisterModel(buffer);
		if (!mdl) {
			// no, revert to the male model
			Com_sprintf (buffer, sizeof(buffer), "players/%s/%s", "male", base+1);
			mdl = re.RegisterModel(buffer);
			if (!mdl) {
				// last try, default male weapon.md2
				Com_sprintf (buffer, sizeof(buffer), "players/male/weapon.md2");
				mdl = re.RegisterModel(buffer);
			}
		} 
	}

	return mdl;
}

// PMM - used in shell code 
extern int Developer_searchpath (int who);
// pmm
/*
===============
CL_AddPacketEntities

===============
*/
void CL_AddPacketEntities (frame_t *frame)
{
	entity_t			ent;
	entity_state_t		*s1;
	float				autorotate;
	int					i;
	int					pnum;
	centity_t			*cent;
	int					autoanim;
	clientinfo_t		*ci;
	unsigned int		effects, renderfx;

	// bonus items rotate at a fixed rate
	autorotate = anglemod(cl_main.cl.time/10);

	// brush models can auto animate their frames
	autoanim = 2*cl_main.cl.time/1000;

	memset (&ent, 0, sizeof(ent));

	for (pnum = 0 ; pnum<frame.num_entities ; pnum++)
	{
		s1 = &cl_main.cl_parse_entities[(frame.parse_entities+pnum)&(client.MAX_PARSE_ENTITIES-1)];

		cent = &cl_main.cl_entities[s1.number];

		effects = s1.effects;
		renderfx = s1.renderfx;

			// set frame
		if (effects & EF_ANIM01)
			ent.frame = autoanim & 1;
		else if (effects & EF_ANIM23)
			ent.frame = 2 + (autoanim & 1);
		else if (effects & EF_ANIM_ALL)
			ent.frame = autoanim;
		else if (effects & EF_ANIM_ALLFAST)
			ent.frame = cl_main.cl.time / 100;
		else
			ent.frame = s1.frame;

		// quad and pent can do different things on client
		if (effects & EF_PENT)
		{
			effects &= ~EF_PENT;
			effects |= EF_COLOR_SHELL;
			renderfx |= RF_SHELL_RED;
		}

		if (effects & EF_QUAD)
		{
			effects &= ~EF_QUAD;
			effects |= EF_COLOR_SHELL;
			renderfx |= RF_SHELL_BLUE;
		}
//======
// PMM
		if (effects & EF_DOUBLE)
		{
			effects &= ~EF_DOUBLE;
			effects |= EF_COLOR_SHELL;
			renderfx |= RF_SHELL_DOUBLE;
		}

		if (effects & EF_HALF_DAMAGE)
		{
			effects &= ~EF_HALF_DAMAGE;
			effects |= EF_COLOR_SHELL;
			renderfx |= RF_SHELL_HALF_DAM;
		}
// pmm
//======
		ent.oldframe = cent.prev.frame;
		ent.backlerp = 1.0 - cl_main.cl.lerpfrac;

		if (renderfx & (RF_FRAMELERP|RF_BEAM))
		{	// step origin discretely, because the frames
			// do the animation properly
			q_shared.VectorCopy (cent.current.origin, ent.origin);
			q_shared.VectorCopy (cent.current.old_origin, ent.oldorigin);
		}
		else
		{	// interpolate origin
			for (i=0 ; i<3 ; i++)
			{
				ent.origin[i] = ent.oldorigin[i] = cent.prev.origin[i] + cl_main.cl.lerpfrac * 
					(cent.current.origin[i] - cent.prev.origin[i]);
			}
		}

		// create a new entity
	
		// tweak the color of beams
		if ( renderfx & RF_BEAM )
		{	// the four beam colors are encoded in 32 bits of skinnum (hack)
			ent.alpha = 0.30;
			ent.skinnum = (s1.skinnum >> ((rand() % 4)*8)) & 0xff;
			ent.model = NULL;
		}
		else
		{
			// set skin
			if (s1.modelindex == 255)
			{	// use custom player skin
				ent.skinnum = 0;
				ci = &cl_main.cl.clientinfo[s1.skinnum & 0xff];
				ent.skin = ci.skin;
				ent.model = ci.model;
				if (!ent.skin or !ent.model)
				{
					ent.skin = cl_main.cl.baseclientinfo.skin;
					ent.model = cl_main.cl.baseclientinfo.model;
				}

//============
//PGM
				if (renderfx & RF_USE_DISGUISE)
				{
					if(!strncmp((char *)ent.skin, "players/male", 12))
					{
						ent.skin = re.RegisterSkin ("players/male/disguise.pcx");
						ent.model = re.RegisterModel ("players/male/tris.md2");
					}
					else if(!strncmp((char *)ent.skin, "players/female", 14))
					{
						ent.skin = re.RegisterSkin ("players/female/disguise.pcx");
						ent.model = re.RegisterModel ("players/female/tris.md2");
					}
					else if(!strncmp((char *)ent.skin, "players/cyborg", 14))
					{
						ent.skin = re.RegisterSkin ("players/cyborg/disguise.pcx");
						ent.model = re.RegisterModel ("players/cyborg/tris.md2");
					}
				}
//PGM
//============
			}
			else
			{
				ent.skinnum = s1.skinnum;
				ent.skin = NULL;
				ent.model = cl_main.cl.model_draw[s1.modelindex];
			}
		}

		// only used for black hole model right now, FIXME: do better
		if (renderfx == RF_TRANSLUCENT)
			ent.alpha = 0.70;

		// render effects (fullbright, translucent, etc)
		if ((effects & EF_COLOR_SHELL))
			ent.flags = 0;	// renderfx go on color shell entity
		else
			ent.flags = renderfx;

		// calculate angles
		if (effects & EF_ROTATE)
		{	// some bonus items auto-rotate
			ent.angles[0] = 0;
			ent.angles[1] = autorotate;
			ent.angles[2] = 0;
		}
		// RAFAEL
		else if (effects & EF_SPINNINGLIGHTS)
		{
			ent.angles[0] = 0;
			ent.angles[1] = anglemod(cl_main.cl.time/2) + s1.angles[1];
			ent.angles[2] = 180;
			{
				vec3_t forward;
				vec3_t start;

				AngleVectors (ent.angles, forward, NULL, NULL);
				VectorMA (ent.origin, 64, forward, start);
				V_AddLight (start, 100, 1, 0, 0);
			}
		}
		else
		{	// interpolate angles
			float	a1, a2;

			for (i=0 ; i<3 ; i++)
			{
				a1 = cent.current.angles[i];
				a2 = cent.prev.angles[i];
				ent.angles[i] = LerpAngle (a2, a1, cl_main.cl.lerpfrac);
			}
		}

		if (s1.number == cl_main.cl.playernum+1)
		{
			ent.flags |= RF_VIEWERMODEL;	// only draw from mirrors
			// FIXME: still pass to refresh

			if (effects & EF_FLAG1)
				V_AddLight (ent.origin, 225, 1.0, 0.1, 0.1);
			else if (effects & EF_FLAG2)
				V_AddLight (ent.origin, 225, 0.1, 0.1, 1.0);
			else if (effects & EF_TAGTRAIL)						//PGM
				V_AddLight (ent.origin, 225, 1.0, 1.0, 0.0);	//PGM
			else if (effects & EF_TRACKERTRAIL)					//PGM
				V_AddLight (ent.origin, 225, -1.0, -1.0, -1.0);	//PGM

			continue;
		}

		// if set to invisible, skip
		if (!s1.modelindex)
			continue;

		if (effects & EF_BFG)
		{
			ent.flags |= RF_TRANSLUCENT;
			ent.alpha = 0.30;
		}

		// RAFAEL
		if (effects & EF_PLASMA)
		{
			ent.flags |= RF_TRANSLUCENT;
			ent.alpha = 0.6;
		}

		if (effects & EF_SPHERETRANS)
		{
			ent.flags |= RF_TRANSLUCENT;
			// PMM - *sigh*  yet more EF overloading
			if (effects & EF_TRACKERTRAIL)
				ent.alpha = 0.6;
			else
				ent.alpha = 0.3;
		}
//pmm

		// add to refresh list
		V_AddEntity (&ent);


		// color shells generate a seperate entity for the main model
		if (effects & EF_COLOR_SHELL)
		{
			// PMM - at this point, all of the shells have been handled
			// if we're in the rogue pack, set up the custom mixing, otherwise just
			// keep going
//			if(Developer_searchpath(2) == 2)
//			{
				// all of the solo colors are fine.  we need to catch any of the combinations that look bad
				// (double & half) and turn them into the appropriate color, and make double/quad something special
				if (renderfx & RF_SHELL_HALF_DAM)
				{
					if(Developer_searchpath(2) == 2)
					{
						// ditch the half damage shell if any of red, blue, or double are on
						if (renderfx & (RF_SHELL_RED|RF_SHELL_BLUE|RF_SHELL_DOUBLE))
							renderfx &= ~RF_SHELL_HALF_DAM;
					}
				}

				if (renderfx & RF_SHELL_DOUBLE)
				{
					if(Developer_searchpath(2) == 2)
					{
						// lose the yellow shell if we have a red, blue, or green shell
						if (renderfx & (RF_SHELL_RED|RF_SHELL_BLUE|RF_SHELL_GREEN))
							renderfx &= ~RF_SHELL_DOUBLE;
						// if we have a red shell, turn it to purple by adding blue
						if (renderfx & RF_SHELL_RED)
							renderfx |= RF_SHELL_BLUE;
						// if we have a blue shell (and not a red shell), turn it to cyan by adding green
						else if (renderfx & RF_SHELL_BLUE)
							// go to green if it's on already, otherwise do cyan (flash green)
							if (renderfx & RF_SHELL_GREEN)
								renderfx &= ~RF_SHELL_BLUE;
							else
								renderfx |= RF_SHELL_GREEN;
					}
				}
//			}
			// pmm
			ent.flags = renderfx | RF_TRANSLUCENT;
			ent.alpha = 0.30;
			V_AddEntity (&ent);
		}

		ent.skin = NULL;		// never use a custom skin on others
		ent.skinnum = 0;
		ent.flags = 0;
		ent.alpha = 0;

		// duplicate for linked models
		if (s1.modelindex2)
		{
			if (s1.modelindex2 == 255)
			{	// custom weapon
				ci = &cl_main.cl.clientinfo[s1.skinnum & 0xff];
				i = (s1.skinnum >> 8); // 0 is default weapon model
				if (!cl_vwep.value or i > MAX_CLIENTWEAPONMODELS - 1)
					i = 0;
				ent.model = ci.weaponmodel[i];
				if (!ent.model) {
					if (i != 0)
						ent.model = ci.weaponmodel[0];
					if (!ent.model)
						ent.model = cl_main.cl.baseclientinfo.weaponmodel[0];
				}
			}
			else
				ent.model = cl_main.cl.model_draw[s1.modelindex2];

			// PMM - check for the defender sphere shell .. make it translucent
			// replaces the previous version which used the high bit on modelindex2 to determine transparency
			if (!Q_strcasecmp (cl_main.cl.configstrings[CS_MODELS+(s1.modelindex2)], "models/items/shell/tris.md2"))
			{
				ent.alpha = 0.32;
				ent.flags = RF_TRANSLUCENT;
			}
			// pmm

			V_AddEntity (&ent);

			//PGM - make sure these get reset.
			ent.flags = 0;
			ent.alpha = 0;
			//PGM
		}
		if (s1.modelindex3)
		{
			ent.model = cl_main.cl.model_draw[s1.modelindex3];
			V_AddEntity (&ent);
		}
		if (s1.modelindex4)
		{
			ent.model = cl_main.cl.model_draw[s1.modelindex4];
			V_AddEntity (&ent);
		}

		if ( effects & EF_POWERSCREEN )
		{
			ent.model = cl_mod_powerscreen;
			ent.oldframe = 0;
			ent.frame = 0;
			ent.flags |= (RF_TRANSLUCENT | RF_SHELL_GREEN);
			ent.alpha = 0.30;
			V_AddEntity (&ent);
		}

		// add automatic particle trails
		if ( (effects&~EF_ROTATE) )
		{
			if (effects & EF_ROCKET)
			{
				CL_RocketTrail (cent.lerp_origin, ent.origin, cent);
				V_AddLight (ent.origin, 200, 1, 1, 0);
			}
			// PGM - Do not reorder EF_BLASTER and EF_HYPERBLASTER. 
			// EF_BLASTER | EF_TRACKER is a special case for EF_BLASTER2... Cheese!
			else if (effects & EF_BLASTER)
			{
//				CL_BlasterTrail (cent.lerp_origin, ent.origin);
//PGM
				if (effects & EF_TRACKER)	// lame... problematic?
				{
					CL_BlasterTrail2 (cent.lerp_origin, ent.origin);
					V_AddLight (ent.origin, 200, 0, 1, 0);		
				}
				else
				{
					CL_BlasterTrail (cent.lerp_origin, ent.origin);
					V_AddLight (ent.origin, 200, 1, 1, 0);
				}
//PGM
			}
			else if (effects & EF_HYPERBLASTER)
			{
				if (effects & EF_TRACKER)						// PGM	overloaded for blaster2.
					V_AddLight (ent.origin, 200, 0, 1, 0);		// PGM
				else											// PGM
					V_AddLight (ent.origin, 200, 1, 1, 0);
			}
			else if (effects & EF_GIB)
			{
				CL_DiminishingTrail (cent.lerp_origin, ent.origin, cent, effects);
			}
			else if (effects & EF_GRENADE)
			{
				CL_DiminishingTrail (cent.lerp_origin, ent.origin, cent, effects);
			}
			else if (effects & EF_FLIES)
			{
				CL_FlyEffect (cent, ent.origin);
			}
			else if (effects & EF_BFG)
			{
				static int bfg_lightramp[6] = {300, 400, 600, 300, 150, 75};

				if (effects & EF_ANIM_ALLFAST)
				{
					CL_BfgParticles (&ent);
					i = 200;
				}
				else
				{
					i = bfg_lightramp[s1.frame];
				}
				V_AddLight (ent.origin, i, 0, 1, 0);
			}
			// RAFAEL
			else if (effects & EF_TRAP)
			{
				ent.origin[2] += 32;
				CL_TrapParticles (&ent);
				i = (rand()%100) + 100;
				V_AddLight (ent.origin, i, 1, 0.8, 0.1);
			}
			else if (effects & EF_FLAG1)
			{
				CL_FlagTrail (cent.lerp_origin, ent.origin, 242);
				V_AddLight (ent.origin, 225, 1, 0.1, 0.1);
			}
			else if (effects & EF_FLAG2)
			{
				CL_FlagTrail (cent.lerp_origin, ent.origin, 115);
				V_AddLight (ent.origin, 225, 0.1, 0.1, 1);
			}
//======
//ROGUE
			else if (effects & EF_TAGTRAIL)
			{
				CL_TagTrail (cent.lerp_origin, ent.origin, 220);
				V_AddLight (ent.origin, 225, 1.0, 1.0, 0.0);
			}
			else if (effects & EF_TRACKERTRAIL)
			{
				if (effects & EF_TRACKER)
				{
					float intensity;

					intensity = 50 + (500 * (sin(cl_main.cl.time/500.0) + 1.0));
					// FIXME - check out this effect in rendition
					if(vidref_val == VIDREF_GL)
						V_AddLight (ent.origin, intensity, -1.0, -1.0, -1.0);
					else
						V_AddLight (ent.origin, -1.0 * intensity, 1.0, 1.0, 1.0);
					}
				else
				{
					CL_Tracker_Shell (cent.lerp_origin);
					V_AddLight (ent.origin, 155, -1.0, -1.0, -1.0);
				}
			}
			else if (effects & EF_TRACKER)
			{
				CL_TrackerTrail (cent.lerp_origin, ent.origin, 0);
				// FIXME - check out this effect in rendition
				if(vidref_val == VIDREF_GL)
					V_AddLight (ent.origin, 200, -1, -1, -1);
				else
					V_AddLight (ent.origin, -200, 1, 1, 1);
			}
//ROGUE
//======
			// RAFAEL
			else if (effects & EF_GREENGIB)
			{
				CL_DiminishingTrail (cent.lerp_origin, ent.origin, cent, effects);				
			}
			// RAFAEL
			else if (effects & EF_IONRIPPER)
			{
				CL_IonripperTrail (cent.lerp_origin, ent.origin);
				V_AddLight (ent.origin, 100, 1, 0.5, 0.5);
			}
			// RAFAEL
			else if (effects & EF_BLUEHYPERBLASTER)
			{
				V_AddLight (ent.origin, 200, 0, 0, 1);
			}
			// RAFAEL
			else if (effects & EF_PLASMA)
			{
				if (effects & EF_ANIM_ALLFAST)
				{
					CL_BlasterTrail (cent.lerp_origin, ent.origin);
				}
				V_AddLight (ent.origin, 130, 1, 0.5, 0.5);
			}
		}

		q_shared.VectorCopy (ent.origin, cent.lerp_origin);
	}
}



/*
==============
CL_AddViewWeapon
==============
*/
void CL_AddViewWeapon (player_state_t *ps, player_state_t *ops)
{
	entity_t	gun;		// view model
	int			i;

	// allow the gun to be completely removed
	if (!cl_gun.value)
		return;

	// don't draw gun if in wide angle view
	if (ps.fov > 90)
		return;

	memset (&gun, 0, sizeof(gun));

	if (gun_model)
		gun.model = gun_model;	// development tool
	else
		gun.model = cl_main.cl.model_draw[ps.gunindex];
	if (!gun.model)
		return;

	// set up gun position
	for (i=0 ; i<3 ; i++)
	{
		gun.origin[i] = cl_main.cl.refdef.vieworg[i] + ops.gunoffset[i]
			+ cl_main.cl.lerpfrac * (ps.gunoffset[i] - ops.gunoffset[i]);
		gun.angles[i] = cl_main.cl.refdef.viewangles[i] + LerpAngle (ops.gunangles[i],
			ps.gunangles[i], cl_main.cl.lerpfrac);
	}

	if (gun_frame)
	{
		gun.frame = gun_frame;	// development tool
		gun.oldframe = gun_frame;	// development tool
	}
	else
	{
		gun.frame = ps.gunframe;
		if (gun.frame == 0)
			gun.oldframe = 0;	// just changed weapons, don't lerp from old
		else
			gun.oldframe = ops.gunframe;
	}

	gun.flags = RF_MINLIGHT | RF_DEPTHHACK | RF_WEAPONMODEL;
	gun.backlerp = 1.0 - cl_main.cl.lerpfrac;
	q_shared.VectorCopy (gun.origin, gun.oldorigin);	// don't lerp at all
	V_AddEntity (&gun);
}


/*
===============
CL_CalcViewValues

Sets cl_main.cl.refdef view values
===============
*/
void CL_CalcViewValues (void)
{
	int			i;
	float		lerp, backlerp;
	centity_t	*ent;
	frame_t		*oldframe;
	player_state_t	*ps, *ops;

	// find the previous frame to interpolate from
	ps = &cl_main.cl.frame.playerstate;
	i = (cl_main.cl.frame.serverframe - 1) & qcommon.UPDATE_MASK;
	oldframe = &cl_main.cl.frames[i];
	if (oldframe.serverframe != cl_main.cl.frame.serverframe-1 or !oldframe.valid)
		oldframe = &cl_main.cl.frame;		// previous frame was dropped or involid
	ops = &oldframe.playerstate;

	// see if the player entity was teleported this frame
	if ( fabs(ops.pmove.origin[0] - ps.pmove.origin[0]) > 256*8
		or abs(ops.pmove.origin[1] - ps.pmove.origin[1]) > 256*8
		or abs(ops.pmove.origin[2] - ps.pmove.origin[2]) > 256*8)
		ops = ps;		// don't interpolate

	ent = &cl_main.cl_entities[cl_main.cl.playernum+1];
	lerp = cl_main.cl.lerpfrac;

	// calculate the origin
	if ((cl_predict.value) && !(cl_main.cl.frame.playerstate.pmove.pm_flags & PMF_NO_PREDICTION))
	{	// use predicted values
		unsigned	delta;

		backlerp = 1.0 - lerp;
		for (i=0 ; i<3 ; i++)
		{
			cl_main.cl.refdef.vieworg[i] = cl_main.cl.predicted_origin[i] + ops.viewoffset[i] 
				+ cl_main.cl.lerpfrac * (ps.viewoffset[i] - ops.viewoffset[i])
				- backlerp * cl_main.cl.prediction_error[i];
		}

		// smooth out stair climbing
		delta = cls.realtime - cl_main.cl.predicted_step_time;
		if (delta < 100)
			cl_main.cl.refdef.vieworg[2] -= cl_main.cl.predicted_step * (100 - delta) * 0.01;
	}
	else
	{	// just use interpolated values
		for (i=0 ; i<3 ; i++)
			cl_main.cl.refdef.vieworg[i] = ops.pmove.origin[i]*0.125 + ops.viewoffset[i] 
				+ lerp * (ps.pmove.origin[i]*0.125 + ps.viewoffset[i] 
				- (ops.pmove.origin[i]*0.125 + ops.viewoffset[i]) );
	}

	// if not running a demo or on a locked frame, add the local angle movement
	if ( cl_main.cl.frame.playerstate.pmove.pm_type < PM_DEAD )
	{	// use predicted values
		for (i=0 ; i<3 ; i++)
			cl_main.cl.refdef.viewangles[i] = cl_main.cl.predicted_angles[i];
	}
	else
	{	// just use interpolated values
		for (i=0 ; i<3 ; i++)
			cl_main.cl.refdef.viewangles[i] = LerpAngle (ops.viewangles[i], ps.viewangles[i], lerp);
	}

	for (i=0 ; i<3 ; i++)
		cl_main.cl.refdef.viewangles[i] += LerpAngle (ops.kick_angles[i], ps.kick_angles[i], lerp);

	AngleVectors (cl_main.cl.refdef.viewangles, cl_main.cl.v_forward, cl_main.cl.v_right, cl_main.cl.v_up);

	// interpolate field of view
	cl_main.cl.refdef.fov_x = ops.fov + lerp * (ps.fov - ops.fov);

	// don't interpolate blend color
	for (i=0 ; i<4 ; i++)
		cl_main.cl.refdef.blend[i] = ps.blend[i];

	// add the weapon
	CL_AddViewWeapon (ps, ops);
}

/*
===============
CL_AddEntities

Emits all entities, particles, and lights to the refresh
===============
*/
void CL_AddEntities (void)
{
	if (cls.state != ca_active)
		return;

	if (cl_main.cl.time > cl_main.cl.frame.servertime)
	{
		if (cl_showclamp.value)
			Com_Printf ("high clamp %i\n", cl_main.cl.time - cl_main.cl.frame.servertime);
		cl_main.cl.time = cl_main.cl.frame.servertime;
		cl_main.cl.lerpfrac = 1.0;
	}
	else if (cl_main.cl.time < cl_main.cl.frame.servertime - 100)
	{
		if (cl_showclamp.value)
			Com_Printf ("low clamp %i\n", cl_main.cl.frame.servertime-100 - cl_main.cl.time);
		cl_main.cl.time = cl_main.cl.frame.servertime - 100;
		cl_main.cl.lerpfrac = 0;
	}
	else
		cl_main.cl.lerpfrac = 1.0 - (cl_main.cl.frame.servertime - cl_main.cl.time) * 0.01;

	if (cl_timedemo.value)
		cl_main.cl.lerpfrac = 1.0;

//	CL_AddPacketEntities (&cl_main.cl.frame);
//	CL_AddTEnts ();
//	CL_AddParticles ();
//	CL_AddDLights ();
//	CL_AddLightStyles ();

	CL_CalcViewValues ();
	// PMM - moved this here so the heat beam has the right values for the vieworg, and can lock the beam to the gun
	CL_AddPacketEntities (&cl_main.cl.frame);
#if 0
	CL_AddProjectiles ();
#endif
	CL_AddTEnts ();
	CL_AddParticles ();
	CL_AddDLights ();
	CL_AddLightStyles ();
}



/*
===============
CL_GetEntitySoundOrigin

Called to get the sound spatialization origin
===============
*/
void CL_GetEntitySoundOrigin (int ent, vec3_t org)
{
	centity_t	*old;

	if (ent < 0 or ent >= q_shared.MAX_EDICTS)
		Com_Error (q_shared.ERR_DROP, "CL_GetEntitySoundOrigin: bad ent");
	old = &cl_main.cl_entities[ent];
	q_shared.VectorCopy (old.lerp_origin, org);

	// FIXME: bmodel issues...
}
"""
