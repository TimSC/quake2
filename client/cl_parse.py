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
from client import cl_main, cl_scrn
from qcommon import net_chan, qcommon, common
"""
// cl_parse.c  -- parse a message received from the server

#include "client.h"

char *svc_strings[256] =
{
	"svc_bad",

	"svc_muzzleflash",
	"svc_muzzlflash2",
	"svc_temp_entity",
	"svc_layout",
	"svc_inventory",

	"svc_nop",
	"svc_disconnect",
	"svc_reconnect",
	"svc_sound",
	"svc_print",
	"svc_stufftext",
	"svc_serverdata",
	"svc_configstring",
	"svc_spawnbaseline",	
	"svc_centerprint",
	"svc_download",
	"svc_playerinfo",
	"svc_packetentities",
	"svc_deltapacketentities",
	"svc_frame"
};

//=============================================================================

void CL_DownloadFileName(char *dest, int destlen, char *fn)
{
	if (strncmp(fn, "players", 7) == 0)
		Com_sprintf (dest, destlen, "%s/%s", BASEDIRNAME, fn);
	else
		Com_sprintf (dest, destlen, "%s/%s", FS_Gamedir(), fn);
}

/*
===============
CL_CheckOrDownloadFile

Returns true if the file exists, otherwise it attempts
to start a download from the server.
===============
*/
qboolean	CL_CheckOrDownloadFile (char *filename)
{
	FILE *fp;
	char	name[MAX_OSPATH];

	if (strstr (filename, ".."))
	{
		Com_Printf ("Refusing to download a path with ..\n");
		return true;
	}

	if (FS_LoadFile (filename, NULL) != -1)
	{	// it exists, no need to download
		return true;
	}

	strcpy (cl_main.cls.downloadname, filename);

	// download to a temp name, and only rename
	// to the real name when done, so if interrupted
	// a runt file wont be left
	COM_StripExtension (cl_main.cls.downloadname, cl_main.cls.downloadtempname);
	strcat (cl_main.cls.downloadtempname, ".tmp");

//ZOID
	// check to see if we already have a tmp for this file, if so, try to resume
	// open the file if not opened yet
	CL_DownloadFileName(name, sizeof(name), cl_main.cls.downloadtempname);

//	FS_CreatePath (name);

	fp = fopen (name, "r+b");
	if (fp) { // it exists
		int len;
		fseek(fp, 0, SEEK_END);
		len = ftell(fp);

		cl_main.cls.download = fp;

		// give the server an offset to start the download
		Com_Printf ("Resuming %s\n", cl_main.cls.downloadname);
		MSG_WriteByte (&cl_main.cls.netchan.message, clc_stringcmd);
		MSG_WriteString (&cl_main.cls.netchan.message,
			va("download %s %i", cl_main.cls.downloadname, len));
	} else {
		Com_Printf ("Downloading %s\n", cl_main.cls.downloadname);
		MSG_WriteByte (&cl_main.cls.netchan.message, clc_stringcmd);
		MSG_WriteString (&cl_main.cls.netchan.message,
			va("download %s", cl_main.cls.downloadname));
	}

	cl_main.cls.downloadnumber++;

	return false;
}

/*
===============
CL_Download_f

Request a download from the server
===============
*/
void	CL_Download_f (void)
{
	char filename[MAX_OSPATH];

	if (Cmd_Argc() != 2) {
		Com_Printf("Usage: download <filename>\n");
		return;
	}

	Com_sprintf(filename, sizeof(filename), "%s", Cmd_Argv(1));

	if (strstr (filename, ".."))
	{
		Com_Printf ("Refusing to download a path with ..\n");
		return;
	}

	if (FS_LoadFile (filename, NULL) != -1)
	{	// it exists, no need to download
		Com_Printf("File already exists.\n");
		return;
	}

	strcpy (cl_main.cls.downloadname, filename);
	Com_Printf ("Downloading %s\n", cl_main.cls.downloadname);

	// download to a temp name, and only rename
	// to the real name when done, so if interrupted
	// a runt file wont be left
	COM_StripExtension (cl_main.cls.downloadname, cl_main.cls.downloadtempname);
	strcat (cl_main.cls.downloadtempname, ".tmp");

	MSG_WriteByte (&cl_main.cls.netchan.message, clc_stringcmd);
	MSG_WriteString (&cl_main.cls.netchan.message,
		va("download %s", cl_main.cls.downloadname));

	cl_main.cls.downloadnumber++;
}

/*
======================
CL_RegisterSounds
======================
*/
void CL_RegisterSounds (void)
{
	int		i;

	S_BeginRegistration ();
	CL_RegisterTEntSounds ();
	for (i=1 ; i<MAX_SOUNDS ; i++)
	{
		if (!cl_main.cl.configstrings[CS_SOUNDS+i][0])
			break;
		cl_main.cl.sound_precache[i] = S_RegisterSound (cl_main.cl.configstrings[CS_SOUNDS+i]);
		Sys_SendKeyEvents ();	// pump message loop
	}
	S_EndRegistration ();
}


/*
=====================
CL_ParseDownload

A download message has been received from the server
=====================
*/
void CL_ParseDownload (void)
{
	int		size, percent;
	char	name[MAX_OSPATH];
	int		r;

	// read the data
	size = MSG_ReadShort (&net_chan.net_message);
	percent = MSG_ReadByte (&net_chan.net_message);
	if (size == -1)
	{
		Com_Printf ("Server does not have this file.\n");
		if (cl_main.cls.download)
		{
			// if here, we tried to resume a file but the server said no
			fclose (cl_main.cls.download);
			cl_main.cls.download = NULL;
		}
		CL_RequestNextDownload ();
		return;
	}

	// open the file if not opened yet
	if (!cl_main.cls.download)
	{
		CL_DownloadFileName(name, sizeof(name), cl_main.cls.downloadtempname);

		FS_CreatePath (name);

		cl_main.cls.download = fopen (name, "wb");
		if (!cl_main.cls.download)
		{
			net_chan.net_message.readcount += size;
			Com_Printf ("Failed to open %s\n", cl_main.cls.downloadtempname);
			CL_RequestNextDownload ();
			return;
		}
	}

	fwrite (net_chan.net_message.data + net_chan.net_message.readcount, 1, size, cl_main.cls.download);
	net_chan.net_message.readcount += size;

	if (percent != 100)
	{
		// request next block
// change display routines by zoid
#if 0
		Com_Printf (".");
		if (10*(percent/10) != cl_main.cls.downloadpercent)
		{
			cl_main.cls.downloadpercent = 10*(percent/10);
			Com_Printf ("%i%%", cl_main.cls.downloadpercent);
		}
#endif
		cl_main.cls.downloadpercent = percent;

		MSG_WriteByte (&cl_main.cls.netchan.message, clc_stringcmd);
		SZ_Print (&cl_main.cls.netchan.message, "nextdl");
	}
	else
	{
		char	oldn[MAX_OSPATH];
		char	newn[MAX_OSPATH];

//		Com_Printf ("100%%\n");

		fclose (cl_main.cls.download);

		// rename the temp file to it's final name
		CL_DownloadFileName(oldn, sizeof(oldn), cl_main.cls.downloadtempname);
		CL_DownloadFileName(newn, sizeof(newn), cl_main.cls.downloadname);
		r = rename (oldn, newn);
		if (r)
			Com_Printf ("failed to rename.\n");

		cl_main.cls.download = NULL;
		cl_main.cls.downloadpercent = 0;

		// get another file if needed

		CL_RequestNextDownload ();
	}
}


/*
=====================================================================

  SERVER CONNECTING MESSAGES

=====================================================================
*/

/*
==================
CL_ParseServerData
==================
"""
def CL_ParseServerData ():

	#extern cvar_t	*fs_gamedirvar;
	#char	*str;
	#int		i;
	
	common.Com_DPrintf ("Serverdata packet received.\n")
	#
	# wipe the client_state_t struct
	#
	"""
	CL_ClearState ()
	cl_main.cls.state = ca_connected;

// parse protocol version number
	i = MSG_ReadLong (&net_chan.net_message);
	cl_main.cls.serverProtocol = i;

	// BIG HACK to let demos from release work with the 3.0x patch!!!
	if (Com_ServerState() && PROTOCOL_VERSION == 34)
	{
	}
	else if (i != PROTOCOL_VERSION)
		Com_Error (qcommon.ERR_DROP,"Server returned version %i, not %i", i, PROTOCOL_VERSION);

	cl_main.cl.servercount = MSG_ReadLong (&net_chan.net_message);
	cl_main.cl.attractloop = MSG_ReadByte (&net_chan.net_message);

	// game directory
	str = MSG_ReadString (&net_chan.net_message);
	strncpy (cl_main.cl.gamedir, str, sizeof(cl_main.cl.gamedir)-1);

	// set gamedir
	if ((*str && (!fs_gamedirvar->string || !*fs_gamedirvar->string || strcmp(fs_gamedirvar->string, str))) || (!*str && (fs_gamedirvar->string || *fs_gamedirvar->string)))
		Cvar_Set("game", str);

	// parse player entity number
	cl_main.cl.playernum = MSG_ReadShort (&net_chan.net_message);

	// get the full level name
	str = MSG_ReadString (&net_chan.net_message);

	if (cl_main.cl.playernum == -1)
	{	// playing a cinematic or showing a pic, not a level
		SCR_PlayCinematic (str);
	}
	else
	{
		// seperate the printfs so the server message can have a color
		Com_Printf("\n\n\35\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\37\n\n");
		Com_Printf ("%c%s\n", 2, str);

		// need to prep refresh at next oportunity
		cl_main.cl.refresh_prepped = false;
	}


/*
==================
CL_ParseBaseline
==================
*/
void CL_ParseBaseline (void)
{
	entity_state_t	*es;
	int				bits;
	int				newnum;
	entity_state_t	nullstate;

	memset (&nullstate, 0, sizeof(nullstate));

	newnum = CL_ParseEntityBits (&bits);
	es = &cl_entities[newnum].baseline;
	CL_ParseDelta (&nullstate, es, newnum, bits);
}


/*
================
CL_LoadClientinfo

================
*/
void CL_LoadClientinfo (clientinfo_t *ci, char *s)
{
	int i;
	char		*t;
	char		model_name[MAX_QPATH];
	char		skin_name[MAX_QPATH];
	char		model_filename[MAX_QPATH];
	char		skin_filename[MAX_QPATH];
	char		weapon_filename[MAX_QPATH];

	strncpy(ci->cinfo, s, sizeof(ci->cinfo));
	ci->cinfo[sizeof(ci->cinfo)-1] = 0;

	// isolate the player's name
	strncpy(ci->name, s, sizeof(ci->name));
	ci->name[sizeof(ci->name)-1] = 0;
	t = strstr (s, "\\");
	if (t)
	{
		ci->name[t-s] = 0;
		s = t+1;
	}

	if (cl_noskins->value || *s == 0)
	{
		Com_sprintf (model_filename, sizeof(model_filename), "players/male/tris.md2");
		Com_sprintf (weapon_filename, sizeof(weapon_filename), "players/male/weapon.md2");
		Com_sprintf (skin_filename, sizeof(skin_filename), "players/male/grunt.pcx");
		Com_sprintf (ci->iconname, sizeof(ci->iconname), "/players/male/grunt_i.pcx");
		ci->model = re.RegisterModel (model_filename);
		memset(ci->weaponmodel, 0, sizeof(ci->weaponmodel));
		ci->weaponmodel[0] = re.RegisterModel (weapon_filename);
		ci->skin = re.RegisterSkin (skin_filename);
		ci->icon = re.RegisterPic (ci->iconname);
	}
	else
	{
		// isolate the model name
		strcpy (model_name, s);
		t = strstr(model_name, "/");
		if (!t)
			t = strstr(model_name, "\\");
		if (!t)
			t = model_name;
		*t = 0;

		// isolate the skin name
		strcpy (skin_name, s + strlen(model_name) + 1);

		// model file
		Com_sprintf (model_filename, sizeof(model_filename), "players/%s/tris.md2", model_name);
		ci->model = re.RegisterModel (model_filename);
		if (!ci->model)
		{
			strcpy(model_name, "male");
			Com_sprintf (model_filename, sizeof(model_filename), "players/male/tris.md2");
			ci->model = re.RegisterModel (model_filename);
		}

		// skin file
		Com_sprintf (skin_filename, sizeof(skin_filename), "players/%s/%s.pcx", model_name, skin_name);
		ci->skin = re.RegisterSkin (skin_filename);

		// if we don't have the skin and the model wasn't male,
		// see if the male has it (this is for CTF's skins)
 		if (!ci->skin && Q_stricmp(model_name, "male"))
		{
			// change model to male
			strcpy(model_name, "male");
			Com_sprintf (model_filename, sizeof(model_filename), "players/male/tris.md2");
			ci->model = re.RegisterModel (model_filename);

			// see if the skin exists for the male model
			Com_sprintf (skin_filename, sizeof(skin_filename), "players/%s/%s.pcx", model_name, skin_name);
			ci->skin = re.RegisterSkin (skin_filename);
		}

		// if we still don't have a skin, it means that the male model didn't have
		// it, so default to grunt
		if (!ci->skin) {
			// see if the skin exists for the male model
			Com_sprintf (skin_filename, sizeof(skin_filename), "players/%s/grunt.pcx", model_name, skin_name);
			ci->skin = re.RegisterSkin (skin_filename);
		}

		// weapon file
		for (i = 0; i < num_cl_weaponmodels; i++) {
			Com_sprintf (weapon_filename, sizeof(weapon_filename), "players/%s/%s", model_name, cl_weaponmodels[i]);
			ci->weaponmodel[i] = re.RegisterModel(weapon_filename);
			if (!ci->weaponmodel[i] && strcmp(model_name, "cyborg") == 0) {
				// try male
				Com_sprintf (weapon_filename, sizeof(weapon_filename), "players/male/%s", cl_weaponmodels[i]);
				ci->weaponmodel[i] = re.RegisterModel(weapon_filename);
			}
			if (!cl_vwep->value)
				break; // only one when vwep is off
		}

		// icon file
		Com_sprintf (ci->iconname, sizeof(ci->iconname), "/players/%s/%s_i.pcx", model_name, skin_name);
		ci->icon = re.RegisterPic (ci->iconname);
	}

	// must have loaded all data types to be valud
	if (!ci->skin || !ci->icon || !ci->model || !ci->weaponmodel[0])
	{
		ci->skin = NULL;
		ci->icon = NULL;
		ci->model = NULL;
		ci->weaponmodel[0] = NULL;
		return;
	}
}

/*
================
CL_ParseClientinfo

Load the skin, icon, and model for a client
================
*/
void CL_ParseClientinfo (int player)
{
	char			*s;
	clientinfo_t	*ci;

	s = cl_main.cl.configstrings[player+CS_PLAYERSKINS];

	ci = &cl_main.cl.clientinfo[player];

	CL_LoadClientinfo (ci, s);
}


/*
================
CL_ParseConfigString
================
*/
void CL_ParseConfigString (void)
{
	int		i;
	char	*s;
	char	olds[MAX_QPATH];

	i = MSG_ReadShort (&net_chan.net_message);
	if (i < 0 || i >= MAX_CONFIGSTRINGS)
		Com_Error (qcommon.ERR_DROP, "configstring > MAX_CONFIGSTRINGS");
	s = MSG_ReadString(&net_chan.net_message);

	strncpy (olds, cl_main.cl.configstrings[i], sizeof(olds));
	olds[sizeof(olds) - 1] = 0;

	strcpy (cl_main.cl.configstrings[i], s);

	// do something apropriate 

	if (i >= CS_LIGHTS && i < CS_LIGHTS+MAX_LIGHTSTYLES)
		CL_SetLightstyle (i - CS_LIGHTS);
	else if (i == CS_CDTRACK)
	{
		if (cl_main.cl.refresh_prepped)
			CDAudio_Play (atoi(cl_main.cl.configstrings[CS_CDTRACK]), true);
	}
	else if (i >= CS_MODELS && i < CS_MODELS+MAX_MODELS)
	{
		if (cl_main.cl.refresh_prepped)
		{
			cl_main.cl.model_draw[i-CS_MODELS] = re.RegisterModel (cl_main.cl.configstrings[i]);
			if (cl_main.cl.configstrings[i][0] == '*')
				cl_main.cl.model_clip[i-CS_MODELS] = CM_InlineModel (cl_main.cl.configstrings[i]);
			else
				cl_main.cl.model_clip[i-CS_MODELS] = NULL;
		}
	}
	else if (i >= CS_SOUNDS && i < CS_SOUNDS+MAX_MODELS)
	{
		if (cl_main.cl.refresh_prepped)
			cl_main.cl.sound_precache[i-CS_SOUNDS] = S_RegisterSound (cl_main.cl.configstrings[i]);
	}
	else if (i >= CS_IMAGES && i < CS_IMAGES+MAX_MODELS)
	{
		if (cl_main.cl.refresh_prepped)
			cl_main.cl.image_precache[i-CS_IMAGES] = re.RegisterPic (cl_main.cl.configstrings[i]);
	}
	else if (i >= CS_PLAYERSKINS && i < CS_PLAYERSKINS+MAX_CLIENTS)
	{
		if (cl_main.cl.refresh_prepped && strcmp(olds, s))
			CL_ParseClientinfo (i-CS_PLAYERSKINS);
	}
}


/*
=====================================================================

ACTION MESSAGES

=====================================================================
*/

/*
==================
CL_ParseStartSoundPacket
==================
*/
void CL_ParseStartSoundPacket(void)
{
    vec3_t  pos_v;
	float	*pos;
    int 	channel, ent;
    int 	sound_num;
    float 	volume;
    float 	attenuation;  
	int		flags;
	float	ofs;

	flags = MSG_ReadByte (&net_chan.net_message);
	sound_num = MSG_ReadByte (&net_chan.net_message);

    if (flags & SND_VOLUME)
		volume = MSG_ReadByte (&net_chan.net_message) / 255.0;
	else
		volume = DEFAULT_SOUND_PACKET_VOLUME;
	
    if (flags & SND_ATTENUATION)
		attenuation = MSG_ReadByte (&net_chan.net_message) / 64.0;
	else
		attenuation = DEFAULT_SOUND_PACKET_ATTENUATION;	

    if (flags & SND_OFFSET)
		ofs = MSG_ReadByte (&net_chan.net_message) / 1000.0;
	else
		ofs = 0;

	if (flags & SND_ENT)
	{	// entity reletive
		channel = MSG_ReadShort(&net_chan.net_message); 
		ent = channel>>3;
		if (ent > MAX_EDICTS)
			Com_Error (qcommon.ERR_DROP,"CL_ParseStartSoundPacket: ent = %i", ent);

		channel &= 7;
	}
	else
	{
		ent = 0;
		channel = 0;
	}

	if (flags & SND_POS)
	{	// positioned in space
		MSG_ReadPos (&net_chan.net_message, pos_v);
 
		pos = pos_v;
	}
	else	// use entity number
		pos = NULL;

	if (!cl_main.cl.sound_precache[sound_num])
		return;

	S_StartSound (pos, ent, channel, cl_main.cl.sound_precache[sound_num], volume, attenuation, ofs);
}       
"""

def SHOWNET(s): #char *

	if cl_main.cl_shownet.value>=2:
		common.Com_Printf ("{:3d}:{}\n".format(net_chan.net_message.readcount-1, s))

"""
=====================
CL_ParseServerMessage
=====================
"""
def CL_ParseServerMessage ():

	#int			cmd;
	#char		*s;
	#int			i;

	#
	# if recording demos, copy the message out
	#
	if cl_main.cl_shownet.value == 1:
		common.Com_Printf ("{:d} ".format(net_chan.net_message.cursize))
	elif cl_main.cl_shownet.value >= 2:
		common.Com_Printf ("------------------\n")

	#
	# parse the message
	#
	while 1:
	
		if net_chan.net_message.readcount > net_chan.net_message.cursize:
		
			common.Com_Error (qcommon.ERR_DROP,"CL_ParseServerMessage: Bad server message")
			break

		cmd = common.MSG_ReadByte (net_chan.net_message)

		if cmd == -1:
		
			SHOWNET("END OF MESSAGE")
			break
		
		if cl_main.cl_shownet.value>=2:
		
			if not svc_strings[cmd]:
				common.Com_Printf ("{:3d}:BAD CMD {:d}\n".format(net_chan.net_message.readcount-1,cmd))
			else:
				SHOWNET(svc_strings[cmd])
		
		# other commands
		if cmd == qcommon.svc_ops_e.svc_nop:
			##Com_Printf ("svc_nop\n");
			pass
			
		elif cmd == qcommon.svc_ops_e.svc_disconnect:
			common.Com_Error (ERR_DISCONNECT,"Server disconnected\n");


		elif cmd == qcommon.svc_ops_e.svc_reconnect:
			common.Com_Printf ("Server disconnected, reconnecting\n");
			if cl_main.cls.download:
				#ZOID, close download
				cl_main.cls.download.close()
				cl_main.cls.download = None
			
			cl_main.cls.state = ca_connecting
			cl_main.cls.connect_time = -99999	# CL_CheckForResend() will fire immediately


		elif cmd == qcommon.svc_ops_e.svc_print:
			i = common.MSG_ReadByte (net_chan.net_message)
			if i == PRINT_CHAT:
			
				S_StartLocalSound ("misc/talk.wav")
				con.ormask = 128
			
			common.Com_Printf (common.MSG_ReadString(net_chan.net_message.data))
			con.ormask = 0

			
		elif cmd == qcommon.svc_ops_e.svc_centerprint:
			SCR_CenterPrint (common.MSG_ReadString(net_chan.net_message.data))

			
		elif cmd == qcommon.svc_ops_e.svc_stufftext:
			s = common.MSG_ReadString(net_chan.net_message.data)
			common.Com_DPrintf ("stufftext: {}\n".format(s))
			cmd.Cbuf_AddText (s)

			
		elif cmd == qcommon.svc_ops_e.svc_serverdata:
			cmd.Cbuf_Execute ()		# make sure any stuffed commands are done
			CL_ParseServerData ()

			
		elif cmd == qcommon.svc_ops_e.svc_configstring:
			CL_ParseConfigString ()

			
		elif cmd == qcommon.svc_ops_e.svc_sound:
			CL_ParseStartSoundPacket()

			
		elif cmd == qcommon.svc_ops_e.svc_spawnbaseline:
			CL_ParseBaseline ()


		elif cmd == qcommon.svc_ops_e.svc_temp_entity:
			CL_ParseTEnt ()


		elif cmd == qcommon.svc_ops_e.svc_muzzleflash:
			CL_ParseMuzzleFlash ()


		elif cmd == qcommon.svc_ops_e.svc_muzzleflash2:
			CL_ParseMuzzleFlash2 ()


		elif cmd == qcommon.svc_ops_e.svc_download:
			CL_ParseDownload ()


		elif cmd == qcommon.svc_ops_e.svc_frame:
			CL_ParseFrame ()


		elif cmd == qcommon.svc_ops_e.svc_inventory:
			CL_ParseInventory ()


		elif cmd == qcommon.svc_ops_e.svc_layout:
			s = MSG_ReadString(net_chan.net_message.data)
			cl_main.cl.layout = s


		elif cmd in [qcommon.svc_ops_e.svc_playerinfo, qcommon.svc_ops_e.svc_packetentities, qcommon.svc_ops_e.svc_deltapacketentities]:
			common.Com_Error (qcommon.ERR_DROP, "Out of place frame data");


		else:
			assert 0
			common.Com_Error (qcommon.ERR_DROP,"CL_ParseServerMessage: Illegible server message\n")


		
	
	
	cl_scrn.CL_AddNetgraph ()

	#
	# we don't know if it is ok to save a demo message until
	# after we have parsed the frame
	#
	if cl_main.cls.demorecording and not cl_main.cls.demowaiting:
		CL_WriteDemoMessage ()




