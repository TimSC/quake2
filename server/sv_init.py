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
import random
from enum import Enum
from server import sv_main, sv_send, sv_game
from client import cl_main, cl_scrn
from qcommon import cvar, common, cmd, qcommon, cmodel
from game import q_shared
from linux import net_udp
"""
#include "server.h"

"""
#define	MAX_MASTERS	8				// max recipients for heartbeat packets

class server_state_t(Enum):
	ss_dead = 0			# no map loaded
	ss_loading = 1			# spawning level edicts
	ss_game = 2			# actively running
	ss_cinematic = 3
	ss_demo = 4
	ss_pic = 5

# some qc commands are only valid before the server has finished
# initializing (precache commands, static sounds / objects, etc)

class server_t(object):

	def __init__(self):

		self.clear()

	def clear(self):

		self.state = server_state_t.ss_dead #server_state_t, precache commands are only valid during load

		self.attractloop = False # qboolean	;		// running cinematics and demos for the local system only
		self.loadgame = False # qboolean	;			// client begins should reuse existing entity

		self.time = 0 # unsigned	;				// always sv.framenum * 100 msec
		self.framenum = 0 # int			;

		self.name = None # char		[MAX_QPATH];			// map name, or cinematic name
		self.models = [] # struct cmodel_s		*[MAX_MODELS];

		self.configstrings = [] # char		[MAX_CONFIGSTRINGS][MAX_QPATH];
		for i in range(q_shared.MAX_CONFIGSTRINGS):
			self.configstrings.append("")
		self.baselines = [] # entity_state_t	[MAX_EDICTS];

		# the multicast buffer is used to send a message to a set of clients
		# it is only used to marshall data until SV_Multicast is called
		self.multicast = None # sizebuf_t	;
		self.multicast_buf = None # byte		[MAX_MSGLEN];

		# demo server information
		self.demofile = None # FILE		*;
		self.timedemo = False # qboolean	;		// don't time sync

"""
#define EDICT_NUM(n) ((edict_t *)((byte *)ge->edicts + ge->edict_size*(n)))
#define NUM_FOR_EDICT(e) ( ((byte *)(e)-(byte *)ge->edicts ) / ge->edict_size)


typedef enum
{
	cs_free,		// can be reused for a new connection
	cs_zombie,		// client has been disconnected, but don't reuse
					// connection for a couple seconds
	cs_connected,	// has been assigned to a client_t, but not in game yet
	cs_spawned		// client is fully in game
} client_state_t;

typedef struct
{
	int					areabytes;
	byte				areabits[MAX_MAP_AREAS/8];		// portalarea visibility bits
	player_state_t		ps;
	int					num_entities;
	int					first_entity;		// into the circular sv_packet_entities[]
	int					senttime;			// for ping calculations
} client_frame_t;

#define	LATENCY_COUNTS	16
#define	RATE_MESSAGES	10

typedef struct client_s
{
	client_state_t	state;

	char			userinfo[MAX_INFO_STRING];		// name, etc

	int				lastframe;			// for delta compression
	usercmd_t		lastcmd;			// for filling in big drops

	int				commandMsec;		// every seconds this is reset, if user
										// commands exhaust it, assume time cheating

	int				frame_latency[LATENCY_COUNTS];
	int				ping;

	int				message_size[RATE_MESSAGES];	// used to rate drop packets
	int				rate;
	int				surpressCount;		// number of messages rate supressed

	edict_t			*edict;				// EDICT_NUM(clientnum+1)
	char			name[32];			// extracted from userinfo, high bits masked
	int				messagelevel;		// for filtering printed messages

	// The datagram is written to by sound calls, prints, temp ents, etc.
	// It can be harmlessly overflowed.
	sizebuf_t		datagram;
	byte			datagram_buf[MAX_MSGLEN];

	client_frame_t	frames[UPDATE_BACKUP];	// updates can be delta'd from here

	byte			*download;			// file being downloaded
	int				downloadsize;		// total bytes (can't use EOF because of paks)
	int				downloadcount;		// bytes sent

	int				lastmessage;		// sv.framenum when packet was last received
	int				lastconnect;

	int				challenge;			// challenge of this user, randomly generated

	netchan_t		netchan;
} client_t;

// a client can leave the server in one of four ways:
// dropping properly by quiting or disconnecting
// timing out if no valid messages are received for timeout.value seconds
// getting kicked off by the server operator
// a program error, like an overflowed reliable buffer

//=============================================================================

// MAX_CHALLENGES is made large to prevent a denial
// of service attack that could cycle all of them
// out before legitimate users connected
#define	MAX_CHALLENGES	1024

typedef struct
{
	netadr_t	adr;
	int			challenge;
	int			time;
} challenge_t;

"""
class server_static_t(object):

	def __init__(self):

		self.initialized = False # qboolean, sv_init has completed
		self.realtime = 0 # int, always increasing, no clamping, etc

		self.mapcmd = None # char [MAX_TOKEN_CHARS], ie: *intro.cin+base 

		self.spawncount = 0 # int, incremented each server start
												# used to check late spawns

		self.clients = [] 					# client_t	*, [maxclients->value];
		self.num_client_entities = 0 		# int, maxclients->value*UPDATE_BACKUP*MAX_PACKET_ENTITIES
		self.next_client_entities = 0 		# int, next client_entity to use
		self.client_entities = [] 			# entity_state_t	*, [num_client_entities]

		self.last_heartbeat = 0 # int

		self.challenges = [] # challenge_t	[MAX_CHALLENGES], to prevent invalid IPs from connecting

		# serverrecord values
		self.demofile = None # FILE		*
		self.demo_multicast = None # sizebuf_t
		self.demo_multicast_buf = None # byte		[MAX_MSGLEN]



svs = server_static_t()				# persistant server info
sv = server_t()					# local server
"""
/*
================
SV_FindIndex

================
*/
int SV_FindIndex (char *name, int start, int max, qboolean create)
{
	int		i;
	
	if (!name || !name[0])
		return 0;

	for (i=1 ; i<max && sv.configstrings[start+i][0] ; i++)
		if (!strcmp(sv.configstrings[start+i], name))
			return i;

	if (!create)
		return 0;

	if (i == max)
		Com_Error (ERR_DROP, "*Index: overflow");

	strncpy (sv.configstrings[start+i], name, sizeof(sv.configstrings[i]));

	if (sv.state != ss_loading)
	{	// send the update to everyone
		SZ_Clear (&sv.multicast);
		MSG_WriteChar (&sv.multicast, svc_configstring);
		MSG_WriteShort (&sv.multicast, start+i);
		MSG_WriteString (&sv.multicast, name);
		SV_Multicast (vec3_origin, MULTICAST_ALL_R);
	}

	return i;
}


int SV_ModelIndex (char *name)
{
	return SV_FindIndex (name, CS_MODELS, MAX_MODELS, true);
}

int SV_SoundIndex (char *name)
{
	return SV_FindIndex (name, CS_SOUNDS, MAX_SOUNDS, true);
}

int SV_ImageIndex (char *name)
{
	return SV_FindIndex (name, CS_IMAGES, MAX_IMAGES, true);
}


/*
================
SV_CreateBaseline

Entity baselines are used to compress the update messages
to the clients -- only the fields that differ from the
baseline will be transmitted
================
*/
void SV_CreateBaseline (void)
{
	edict_t			*svent;
	int				entnum;	

	for (entnum = 1; entnum < ge->num_edicts ; entnum++)
	{
		svent = EDICT_NUM(entnum);
		if (!svent->inuse)
			continue;
		if (!svent->s.modelindex && !svent->s.sound && !svent->s.effects)
			continue;
		svent->s.number = entnum;

		//
		// take current state as baseline
		//
		VectorCopy (svent->s.origin, svent->s.old_origin);
		sv.baselines[entnum] = svent->s;
	}
}


/*
=================
SV_CheckForSavegame
=================
*/
void SV_CheckForSavegame (void)
{
	char		name[MAX_OSPATH];
	FILE		*f;
	int			i;

	if (sv_noreload->value)
		return;

	if (Cvar_VariableValue ("deathmatch"))
		return;

	Com_sprintf (name, sizeof(name), "%s/save/current/%s.sav", FS_Gamedir(), sv.name);
	f = fopen (name, "rb");
	if (!f)
		return;		// no savegame

	fclose (f);

	SV_ClearWorld ();

	// get configstrings and areaportals
	SV_ReadLevelFile ();

	if (!sv.loadgame)
	{	// coming back to a level after being in a different
		// level, so run it for ten seconds

		// rlava2 was sending too many lightstyles, and overflowing the
		// reliable data. temporarily changing the server state to loading
		// prevents these from being passed down.
		server_state_t		previousState;		// PGM

		previousState = sv.state;				// PGM
		sv.state = ss_loading;					// PGM
		for (i=0 ; i<100 ; i++)
			ge->RunFrame ();

		sv.state = previousState;				// PGM
	}
}


/*
================
SV_SpawnServer

Change the server to a new map, taking all connected
clients along with it.

================
"""
def SV_SpawnServer (server, spawnpoint, serverstate, attractloop, loadgame): #char *, char *, server_state_t, qboolean, qboolean

	#int			i;
	#unsigned	checksum;

	if attractloop:
		cvar.Cvar_Set ("paused", "0")

	common.Com_Printf ("------- Server Initialization -------\n")

	common.Com_DPrintf ("SpawnServer: {}\n".format(server))

	if sv.demofile is not None:
		sv.demofile = None

	svs.spawncount+=1		# any partially connected client will be
							# restarted
	sv.state = server_state_t.ss_dead
	common.Com_SetServerState (sv.state)

	# wipe the entire per-level structure
	#memset (&sv, 0, sizeof(sv));
	sv.clear()
	svs.realtime = 0
	sv.loadgame = loadgame
	sv.attractloop = attractloop

	"""
	// save name for levels that don't set message
	strcpy (sv.configstrings[q_shared.CS_NAME], server);
	if (Cvar_VariableValue ("deathmatch"))
	{
		sprintf(sv.configstrings[CS_AIRACCEL], "%g", sv_airaccelerate->value);
		pm_airaccelerate = sv_airaccelerate->value;
	}
	else
	{
		strcpy(sv.configstrings[CS_AIRACCEL], "0");
		pm_airaccelerate = 0;
	}
	"""
	sv.multicast = common.SZ_Init (sv.multicast_buf);

	sv.name = server

	"""
	# leave slots at start for clients only
	for (i=0 ; i<maxclients->value ; i++)
	{
		// needs to reconnect
		if (svs.clients[i].state > cs_connected)
			svs.clients[i].state = cs_connected;
		svs.clients[i].lastframe = -1;
	}
	"""
	sv.time = 1000;
	
	sv.name = server
	sv.configstrings[q_shared.CS_NAME] = server
	
	if serverstate != server_state_t.ss_game:
	
		while len(sv.models) < 2: sv.models.append(None)
		sv.models[1], checksum = cmodel.CM_LoadMap ("", False)	# no real map
	
	else:
	
		sv.configstrings[q_shared.CS_MODELS+1] = "maps/%s.bsp".format(server)
		while len(sv.models) < 2: sv.models.append(None)
		sv.models[1], checksum = cmodel.CM_LoadMap (sv.configstrings[q_shared.CS_MODELS+1], False)
	
	sv.configstrings[q_shared.CS_MAPCHECKSUM] = "{:d}".format(checksum)
	"""
	//
	// clear physics interaction links
	//
	SV_ClearWorld ();
	
	for (i=1 ; i< CM_NumInlineModels() ; i++)
	{
		Com_sprintf (sv.configstrings[CS_MODELS+1+i], sizeof(sv.configstrings[CS_MODELS+1+i]),
			"*%i", i);
		sv.models[i+1] = CM_InlineModel (sv.configstrings[CS_MODELS+1+i]);
	}
	"""
	#
	# spawn the rest of the entities on the map
	#	

	# precache and static commands can be issued during
	# map initialization
	sv.state = server_state_t.ss_loading
	common.Com_SetServerState (sv.state)
	"""
	# load and spawn all other entities
	ge->SpawnEntities ( sv.name, CM_EntityString(), spawnpoint )

	# run two frames to allow everything to settle
	ge->RunFrame ()
	ge->RunFrame ()
	"""
	# all precaches are complete
	sv.state = serverstate
	common.Com_SetServerState (sv.state)
	"""
	# create a baseline for more efficient communications
	SV_CreateBaseline ()

	# check for a savegame
	SV_CheckForSavegame ()
	"""
	# set serverinfo variable
	cvar.Cvar_FullSet ("mapname", sv.name, q_shared.CVAR_SERVERINFO | q_shared.CVAR_NOSET)

	common.Com_Printf ("-------------------------------------\n")


"""
==============
SV_InitGame

A brand new game has been started
==============
"""
def SV_InitGame ():

	#int		i;
	#edict_t	*ent;
	#char	idmaster[32];

	if svs.initialized:
	
		# cause any connected clients to reconnect
		sv_main.SV_Shutdown ("Server restarted\n", true);
	
	else:
	
		# make sure the client is down
		cl_main.CL_Drop ()
		cl_scrn.SCR_BeginLoadingPlaque ()
	

	# get any latched variable changes (maxclients, etc)
	cvar.Cvar_GetLatchedVars ()

	svs.initialized = True

	if cvar.Cvar_VariableValue ("coop") and cvar.Cvar_VariableValue ("deathmatch"):
	
		common.Com_Printf("Deathmatch and Coop both set, disabling Coop\n");
		cvar.Cvar_FullSet ("coop", "0",  CVAR_SERVERINFO | CVAR_LATCH);
	

	# dedicated servers are can't be single player and are usually DM
	# so unless they explicity set coop, force it to deathmatch
	if common.dedicated.value:
	
		if cvar.Cvar_VariableValue ("coop") != 0:
			cvar.Cvar_FullSet ("deathmatch", "1",  q_shared.CVAR_SERVERINFO | q_shared.CVAR_LATCH);
	
	# init clients
	if cvar.Cvar_VariableValue ("deathmatch"):
	
		if sv_main.maxclients.value <= 1:
			cvar.Cvar_FullSet ("maxclients", "8", q_shared.CVAR_SERVERINFO | q_shared.CVAR_LATCH)
		elif sv_main.maxclients.value > MAX_CLIENTS:
			cvar.Cvar_FullSet ("maxclients", va("%i", MAX_CLIENTS), q_shared.CVAR_SERVERINFO | q_shared.CVAR_LATCH)
	
	elif cvar.Cvar_VariableValue ("coop"):
	
		if sv_main.maxclients.value <= 1 or sv_main.maxclients.value > 4:
			cvar.Cvar_FullSet ("maxclients", "4", q_shared.CVAR_SERVERINFO | q_shared.CVAR_LATCH)
		#ifdef COPYPROTECT
		#if (!sv.attractloop && !common.dedicated->value)
		#	Sys_CopyProtect ();
		#endif
	
	else:	# non-deathmatch, non-coop is one player
	
		cvar.Cvar_FullSet ("maxclients", "1", q_shared.CVAR_SERVERINFO | q_shared.CVAR_LATCH)
		#ifdef COPYPROTECT
		#if (!sv.attractloop)
		#	Sys_CopyProtect ();
		#endif
	
	svs.spawncount = random.randint(0, 1 << 32)
	#svs.clients = Z_Malloc (sizeof(client_t)*maxclients->value)
	svs.num_client_entities = int(sv_main.maxclients.value*qcommon.UPDATE_BACKUP*64)
	#svs.client_entities = Z_Malloc (sizeof(entity_state_t)*svs.num_client_entities)

	# init network stuff
	net_udp.NET_Config (sv_main.maxclients.value > 1)
	"""
	# heartbeats will always be sent to the id master
	svs.last_heartbeat = -99999;		// send immediately
	Com_sprintf(idmaster, sizeof(idmaster), "192.246.40.37:%i", PORT_MASTER);
	NET_StringToAdr (idmaster, &master_adr[0]);
	"""
	# init game
	sv_game.SV_InitGameProgs ()
	"""
	for (i=0 ; i<sv_main.maxclients.value ; i++)
	{
		ent = EDICT_NUM(i+1);
		ent->s.number = i+1;
		svs.clients[i].edict = ent;
		memset (&svs.clients[i].lastcmd, 0, sizeof(svs.clients[i].lastcmd));
	}



/*
======================
SV_Map

  the full syntax is:

  map [*]<map>$<startspot>+<nextserver>

command from the console or progs.
Map can also be a.cin, .pcx, or .dm2 file
Nextserver is used to allow a cinematic to play, then proceed to
another level:

	map tram.cin+jail_e3
======================
"""
def SV_Map ( attractloop, levelstring, loadgame): #qboolean, char *, qboolean

	#char	level[MAX_QPATH];
	#char	*ch;
	#int		l;
	#char	spawnpoint[MAX_QPATH];
	spawnpoint = ""
	
	sv.loadgame = loadgame
	sv.attractloop = attractloop

	if sv.state == server_state_t.ss_dead and not sv.loadgame:
		SV_InitGame ()	# the game is just starting

	level = levelstring

	# if there is a + in the map, set nextserver to the remainder
	ch = level.find("+")
	if ch != -1:
	
		level = level[:ch]
		cvar.Cvar_Set ("nextserver", "gamemap \"%s\"".format(level[ch+1:]))
	
	else:
		cvar.Cvar_Set ("nextserver", "");

	#ZOID special hack for end game screen in coop mode
	if cvar.Cvar_VariableValue ("coop") and not q_shared.Q_stricmp(level, "victory.pcx"):
		cvar.Cvar_Set ("nextserver", "gamemap \"*base1\"")

	# if there is a $, use the remainder as a spawnpoint
	ch = level.find("$")
	if ch != -1:

		spawnpoint = level[ch+1:]
		level = level[:ch]
	
	else:
		spawnpoint = ""

	# skip the end-of-unit flag if necessary
	if level[0] == '*':
		level = level[1:]

	l = len(level)
	if l > 4 and level[-4:] == ".cin":

		cl_scrn.SCR_BeginLoadingPlaque ()			# for local system
		sv_send.SV_BroadcastCommand ("changing\n")
		SV_SpawnServer (level, spawnpoint, server_state_t.ss_cinematic, attractloop, loadgame)
	
	elif l > 4 and level[-4:] == ".dm2":

		cl_scrn.SCR_BeginLoadingPlaque ()			# for local system
		sv_send.SV_BroadcastCommand ("changing\n")
		SV_SpawnServer (level, spawnpoint, server_state_t.ss_demo, attractloop, loadgame)
	
	elif l > 4 and level[-4:] == ".pcx":

		cl_scrn.SCR_BeginLoadingPlaque ()			# for local system
		sv_send.SV_BroadcastCommand ("changing\n")
		SV_SpawnServer (level, spawnpoint, server_state_t.ss_pic, attractloop, loadgame)
	
	else:

		cl_scrn.SCR_BeginLoadingPlaque ()			# for local system
		sv_send.SV_BroadcastCommand ("changing\n")
		sv_send.SV_SendClientMessages ()
		SV_SpawnServer (level, spawnpoint, server_state_t.ss_game, attractloop, loadgame)
		cmd.Cbuf_CopyToDefer ()
	
	sv_send.SV_BroadcastCommand ("reconnect\n")


