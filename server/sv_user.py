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
from server import sv_main, sv_init
from qcommon import cvar, qcommon, common, net_chan, cmd
from game import q_shared
"""
// sv_user.c -- server code for moving users

#include "server.h"

"""
sv_player = None #edict_t *
"""

/*
============================================================

USER STRINGCMD EXECUTION

sv_client and sv_player will be valid.
============================================================
*/

/*
==================
SV_BeginDemoServer
==================
"""

def SV_BeginDemoserver ():

	#char		name[MAX_OSPATH];

	q_shared.Com_sprintf (name, MAX_OSPATH, "demos/{}".format(sv.name))
	FS_FOpenFile (name, sv.demofile)
	if not sv.demofile:
		common.Com_Error (ERR_DROP, "Couldn't open %s\n", name)


"""
================
SV_New_f

Sends the first message from the server to a connected client.
This will be sent on the initial connection and upon each server load.
================
"""
def SV_New_f (): #void

	"""
	char		*gamedir;
	int			playernum;
	edict_t		*ent;
	"""

	
	common.Com_DPrintf ("New() from {}\n".format(sv_main.sv_client.name))
	
	if sv_main.sv_client.state != sv_init.client_state_t.cs_connected:
	
		common.Com_Printf ("New not valid -- already spawned\n")
		return
	

	# demo servers just dump the file message
	if sv_init.sv.state == sv_init.server_state_t.ss_demo:
	
		SV_BeginDemoserver ()
		return
	

	#
	# serverdata needs to go over for all types of servers
	# to make sure the protocol is right, and to set the gamedir
	#
	gamedir = cvar.Cvar_VariableString ("gamedir")

	# send the serverdata
	common.MSG_WriteByte (sv_main.sv_client.netchan.message, qcommon.svc_ops_e.svc_serverdata.value.to_bytes(1, 'big'))
	common.MSG_WriteLong (sv_main.sv_client.netchan.message, qcommon.PROTOCOL_VERSION)
	common.MSG_WriteLong (sv_main.sv_client.netchan.message, sv_init.svs.spawncount)
	common.MSG_WriteByte (sv_main.sv_client.netchan.message, sv_init.sv.attractloop.to_bytes(1, 'big'))
	common.MSG_WriteString (sv_main.sv_client.netchan.message, gamedir.encode('ascii'))

	if sv_init.sv.state == sv_init.server_state_t.ss_cinematic or sv_init.sv.state == sv_init.server_state_t.ss_pic:
		playernum = -1
	else:
		playernum = sv_main.sv_client - sv_init.svs.clients
	common.MSG_WriteSShort (sv_main.sv_client.netchan.message, playernum)

	# send full levelname
	common.MSG_WriteString (sv_main.sv_client.netchan.message, sv_init.sv.configstrings[q_shared.CS_NAME].encode('ascii'))

	#
	# game server
	# 
	if sv_init.sv.state == sv_init.server_state_t.ss_game:
	
		pass
		"""
		# set up the entity for the client
		ent = EDICT_NUM(playernum+1);
		ent->s.number = playernum+1;
		sv_main.sv_client->edict = ent;
		memset (&sv_main.sv_client->lastcmd, 0, sizeof(sv_main.sv_client->lastcmd));

		# begin fetching configstrings
		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_stufftext);
		MSG_WriteString (&sv_main.sv_client->netchan.message, va("cmd configstrings %i 0\n",svs.spawncount) );
	
		"""


"""
==================
SV_Configstrings_f
==================
"""
def SV_Configstrings_f ():

	print ("SV_Configstrings_f")
	pass
	"""
	int			start;

	common.Com_DPrintf ("Configstrings() from %s\n", sv_main.sv_client->name);

	if (sv_main.sv_client->state != sv_init.client_state_t.cs_connected)
	{
		common.Com_Printf ("configstrings not valid -- already spawned\n");
		return;
	}

	// handle the case of a level changing while a client was connecting
	if ( atoi(Cmd_Argv(1)) != svs.spawncount )
	{
		common.Com_Printf ("SV_Configstrings_f from different level\n");
		SV_New_f ();
		return;
	}
	
	start = atoi(Cmd_Argv(2));

	// write a packet full of data

	while ( sv_main.sv_client->netchan.message.cursize < MAX_MSGLEN/2 
		&& start < MAX_CONFIGSTRINGS)
	{
		if (sv.configstrings[start][0])
		{
			MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_configstring);
			MSG_WriteShort (&sv_main.sv_client->netchan.message, start);
			MSG_WriteString (&sv_main.sv_client->netchan.message, sv.configstrings[start]);
		}
		start++;
	}

	// send next command

	if (start == MAX_CONFIGSTRINGS)
	{
		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_stufftext);
		MSG_WriteString (&sv_main.sv_client->netchan.message, va("cmd baselines %i 0\n",svs.spawncount) );
	}
	else
	{
		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_stufftext);
		MSG_WriteString (&sv_main.sv_client->netchan.message, va("cmd configstrings %i %i\n",svs.spawncount, start) );
	}
}

/*
==================
SV_Baselines_f
==================
"""
def SV_Baselines_f ():

	print ("SV_Baselines_f")
	pass
	"""
	int		start;
	entity_state_t	nullstate;
	entity_state_t	*base;

	common.Com_DPrintf ("Baselines() from %s\n", sv_main.sv_client->name);

	if (sv_main.sv_client->state != sv_init.client_state_t.cs_connected)
	{
		common.Com_Printf ("baselines not valid -- already spawned\n");
		return;
	}
	
	// handle the case of a level changing while a client was connecting
	if ( atoi(Cmd_Argv(1)) != svs.spawncount )
	{
		common.Com_Printf ("SV_Baselines_f from different level\n");
		SV_New_f ();
		return;
	}
	
	start = atoi(Cmd_Argv(2));

	memset (&nullstate, 0, sizeof(nullstate));

	// write a packet full of data

	while ( sv_main.sv_client->netchan.message.cursize <  MAX_MSGLEN/2
		&& start < MAX_EDICTS)
	{
		base = &sv.baselines[start];
		if (base->modelindex || base->sound || base->effects)
		{
			MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_spawnbaseline);
			MSG_WriteDeltaEntity (&nullstate, base, &sv_main.sv_client->netchan.message, true, true);
		}
		start++;
	}

	// send next command

	if (start == MAX_EDICTS)
	{
		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_stufftext);
		MSG_WriteString (&sv_main.sv_client->netchan.message, va("precache %i\n", svs.spawncount) );
	}
	else
	{
		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_stufftext);
		MSG_WriteString (&sv_main.sv_client->netchan.message, va("cmd baselines %i %i\n",svs.spawncount, start) );
	}
}

/*
==================
SV_Begin_f
==================
"""
def SV_Begin_f ():

	print ("SV_Begin_f")
	"""
	common.Com_DPrintf ("Begin() from %s\n", sv_main.sv_client->name);

	// handle the case of a level changing while a client was connecting
	if ( atoi(Cmd_Argv(1)) != svs.spawncount )
	{
		common.Com_Printf ("SV_Begin_f from different level\n");
		SV_New_f ();
		return;
	}

	sv_main.sv_client->state = cs_spawned;
	
	// call the game begin function
	ge->ClientBegin (sv_player);

	Cbuf_InsertFromDefer ();
}

//=============================================================================

/*
==================
SV_NextDownload_f
==================
"""
def SV_NextDownload_f ():
	print ("SV_NextDownload_f")
	"""
	int		r;
	int		percent;
	int		size;

	if (!sv_main.sv_client->download)
		return;

	r = sv_main.sv_client->downloadsize - sv_main.sv_client->downloadcount;
	if (r > 1024)
		r = 1024;

	MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_download);
	MSG_WriteShort (&sv_main.sv_client->netchan.message, r);

	sv_main.sv_client->downloadcount += r;
	size = sv_main.sv_client->downloadsize;
	if (!size)
		size = 1;
	percent = sv_main.sv_client->downloadcount*100/size;
	MSG_WriteByte (&sv_main.sv_client->netchan.message, percent);
	SZ_Write (&sv_main.sv_client->netchan.message,
		sv_main.sv_client->download + sv_main.sv_client->downloadcount - r, r);

	if (sv_main.sv_client->downloadcount != sv_main.sv_client->downloadsize)
		return;

	FS_FreeFile (sv_main.sv_client->download);
	sv_main.sv_client->download = NULL;
}


==================
SV_BeginDownload_f
==================
"""
def SV_BeginDownload_f():
	print ("SV_BeginDownload_f")
	"""
{
	char	*name;
	extern	cvar_t *allow_download;
	extern	cvar_t *allow_download_players;
	extern	cvar_t *allow_download_models;
	extern	cvar_t *allow_download_sounds;
	extern	cvar_t *allow_download_maps;
	extern	int		file_from_pak; // ZOID did file come from pak?
	int offset = 0;

	name = Cmd_Argv(1);

	if (Cmd_Argc() > 2)
		offset = atoi(Cmd_Argv(2)); // downloaded offset

	// hacked by zoid to allow more conrol over download
	// first off, no .. or global allow check
	if (strstr (name, "..") || !allow_download->value
		// leading dot is no good
		|| *name == '.' 
		// leading slash bad as well, must be in subdir
		|| *name == '/'
		// next up, skin check
		|| (strncmp(name, "players/", 6) == 0 && !allow_download_players->value)
		// now models
		|| (strncmp(name, "models/", 6) == 0 && !allow_download_models->value)
		// now sounds
		|| (strncmp(name, "sound/", 6) == 0 && !allow_download_sounds->value)
		// now maps (note special case for maps, must not be in pak)
		|| (strncmp(name, "maps/", 6) == 0 && !allow_download_maps->value)
		// MUST be in a subdirectory	
		|| !strstr (name, "/") )	
	{	// don't allow anything with .. path
		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_download);
		MSG_WriteShort (&sv_main.sv_client->netchan.message, -1);
		MSG_WriteByte (&sv_main.sv_client->netchan.message, 0);
		return;
	}


	if (sv_main.sv_client->download)
		FS_FreeFile (sv_main.sv_client->download);

	sv_main.sv_client->downloadsize = FS_LoadFile (name, (void **)&sv_main.sv_client->download);
	sv_main.sv_client->downloadcount = offset;

	if (offset > sv_main.sv_client->downloadsize)
		sv_main.sv_client->downloadcount = sv_main.sv_client->downloadsize;

	if (!sv_main.sv_client->download
		// special check for maps, if it came from a pak file, don't allow
		// download  ZOID
		|| (strncmp(name, "maps/", 5) == 0 && file_from_pak))
	{
		common.Com_DPrintf ("Couldn't download %s to %s\n", name, sv_main.sv_client->name);
		if (sv_main.sv_client->download) {
			FS_FreeFile (sv_main.sv_client->download);
			sv_main.sv_client->download = NULL;
		}

		MSG_WriteByte (&sv_main.sv_client->netchan.message, svc_download);
		MSG_WriteShort (&sv_main.sv_client->netchan.message, -1);
		MSG_WriteByte (&sv_main.sv_client->netchan.message, 0);
		return;
	}

	SV_NextDownload_f ();
	common.Com_DPrintf ("Downloading %s to %s\n", name, sv_main.sv_client->name);
}



//============================================================================


/*
=================
SV_Disconnect_f

The client is going to disconnect, so remove the connection immediately
=================
"""
def SV_Disconnect_f ():

#	SV_EndRedirect ();
	sv_main.SV_DropClient (sv_main.sv_client)



"""
==================
SV_ShowServerinfo_f

Dumps the serverinfo info string
==================
"""
def SV_ShowServerinfo_f ():

	Info_Print (Cvar_Serverinfo())


"""
void SV_Nextserver (void)
{
	char	*v;

	//ZOID, ss_pic can be nextserver'd in coop mode
	if (sv.state == ss_game || (sv.state == ss_pic && !Cvar_VariableValue("coop")))
		return;		// can't nextserver while playing a normal game

	svs.spawncount++;	// make sure another doesn't sneak in
	v = Cvar_VariableString ("nextserver");
	if (!v[0])
		Cbuf_AddText ("killserver\n");
	else
	{
		Cbuf_AddText (v);
		Cbuf_AddText ("\n");
	}
	Cvar_Set ("nextserver","");
}

/*
==================
SV_Nextserver_f

A cinematic has completed or been aborted by a client, so move
to the next server,
==================
"""
def SV_Nextserver_f ():
	
	print ("SV_Nextserver_f")
	"""
	if ( atoi(Cmd_Argv(1)) != svs.spawncount ) {
		common.Com_DPrintf ("Nextserver() from wrong level, from %s\n", sv_main.sv_client->name);
		return;		// leftover from last server
	}

	common.Com_DPrintf ("Nextserver() from %s\n", sv_main.sv_client->name);

	SV_Nextserver ();


typedef struct
{
	char	*name;
	void	(*func) (void);
} ucmd_t;
"""
ucmds = {
	# auto issued
	"new": SV_New_f,
	"configstrings": SV_Configstrings_f,
	"baselines": SV_Baselines_f,
	"begin": SV_Begin_f,

	"nextserver": SV_Nextserver_f,

	"disconnect": SV_Disconnect_f,

	# issued by hand at client consoles	
	"info": SV_ShowServerinfo_f,

	"download": SV_BeginDownload_f,
	"nextdl": SV_NextDownload_f,
}

"""
==================
SV_ExecuteUserCommand
==================
"""
def SV_ExecuteUserCommand (s): #char *

	# ucmd_t	*u;
	
	cmd.Cmd_TokenizeString (s, True)
	sv_player = sv_main.sv_client.edict

#	SV_BeginRedirect (RD_CLIENT)

	if cmd.Cmd_Argv(0) in ucmds:
		ucmds[cmd.Cmd_Argv(0)]()
	elif sv_init.sv.state == ss_game:
		ge.ClientCommand (sv_player)

#	SV_EndRedirect ()


"""
===========================================================================

USER CMD EXECUTION

===========================================================================
*/



void SV_ClientThink (client_t *cl, usercmd_t *cmd)

{
	cl->commandMsec -= cmd->msec;

	if (cl->commandMsec < 0 && sv_enforcetime->value )
	{
		common.Com_DPrintf ("commandMsec underflow from %s\n", cl->name);
		return;
	}

	ge->ClientThink (cl->edict, cmd);
}


"""
MAX_STRINGCMDS = 8
"""
===================
SV_ExecuteClientMessage

The current net_message is parsed for the given client
===================
"""
def SV_ExecuteClientMessage (cl): #client_t *

	global sv_player
	"""
	int		c;
	char	*s;

	usercmd_t	nullcmd;
	usercmd_t	oldest, oldcmd, newcmd;
	int		net_drop;
	int		stringCmdCount;
	int		checksum, calculatedChecksum;
	int		checksumIndex;
	qboolean	move_issued;
	int		lastframe;
"""
	sv_main.sv_client = cl
	sv_player = sv_main.sv_client.edict

	# only allow one move command
	move_issued = False
	stringCmdCount = 0

	while True:
	
		if net_chan.net_message.readcount > net_chan.net_message.cursize:
		
			common.Com_Printf ("SV_ReadClientMessage: badread\n")
			sv_main.SV_DropClient (cl)
			return

		c = common.MSG_ReadByte (net_chan.net_message)
		if c == -1:
			break # nothing to read

		try:
			c = qcommon.clc_ops_e(c)
		except ValueError:
			pass

		if c == qcommon.clc_ops_e.clc_nop:
			pass

		elif c == qcommon.clc_ops_e.clc_userinfo:
			pass
			"""
			strncpy (cl->userinfo, MSG_ReadString (&net_message), sizeof(cl->userinfo)-1);
			SV_UserinfoChanged (cl);
			break;
			"""

		elif c == qcommon.clc_ops_e.clc_move:


			if move_issued:
				return		# someone is trying to cheat...

			move_issued = True
			checksumIndex = net_chan.net_message.readcount
			checksum = common.MSG_ReadByte (net_chan.net_message)
			lastframe = common.MSG_ReadLong (net_chan.net_message)
			"""
			if (lastframe != cl->lastframe) {
				cl->lastframe = lastframe;
				if (cl->lastframe > 0) {
					cl->frame_latency[cl->lastframe&(LATENCY_COUNTS-1)] = 
						svs.realtime - cl->frames[cl->lastframe & UPDATE_MASK].senttime;
				}
			}

			memset (&nullcmd, 0, sizeof(nullcmd));
			MSG_ReadDeltaUsercmd (&net_message, &nullcmd, &oldest);
			MSG_ReadDeltaUsercmd (&net_message, &oldest, &oldcmd);
			MSG_ReadDeltaUsercmd (&net_message, &oldcmd, &newcmd);

			if ( cl->state != cs_spawned )
			{
				cl->lastframe = -1;
				break;
			}

			// if the checksum fails, ignore the rest of the packet
			calculatedChecksum = COM_BlockSequenceCRCByte (
				net_message.data + checksumIndex + 1,
				net_message.readcount - checksumIndex - 1,
				cl->netchan.incoming_sequence);

			if (calculatedChecksum != checksum)
			{
				common.Com_DPrintf ("Failed command checksum for %s (%d != %d)/%d\n", 
					cl->name, calculatedChecksum, checksum, 
					cl->netchan.incoming_sequence);
				return;
			}"""

			"""
			if (!sv_paused->value)
			{
				net_drop = cl->netchan.dropped;
				if (net_drop < 20)
				{

//if (net_drop > 2)

//	common.Com_Printf ("drop %i\n", net_drop);
					while (net_drop > 2)
					{
						SV_ClientThink (cl, &cl->lastcmd);

						net_drop--;
					}
					if (net_drop > 1)
						SV_ClientThink (cl, &oldest);

					if (net_drop > 0)
						SV_ClientThink (cl, &oldcmd);

				}
				SV_ClientThink (cl, &newcmd);
			}

			cl->lastcmd = newcmd;
			break;
			"""

		elif c == qcommon.clc_ops_e.clc_stringcmd:	

			s = common.MSG_ReadString (net_chan.net_message)

			# malicious users may try using too many string commands
			stringCmdCount += 1
			if stringCmdCount < MAX_STRINGCMDS:
				SV_ExecuteUserCommand (s)

			if cl.state == sv_init.client_state_t.cs_zombie:
				return	# disconnect command
			
		else:

			common.Com_Printf ("SV_ReadClientMessage: unknown command char\n")
			sv_main.SV_DropClient (cl)
			return

