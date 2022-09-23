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
from qcommon import cmd, common
from game import q_shared
from client import console, client

#
# these are the key numbers that should be passed to Key_Event
#
K_TAB			= 9
K_ENTER			= 13
K_ESCAPE		= 27
K_SPACE			= 32

# normal keys should be passed as lowercased ascii

K_BACKSPACE		= 127
K_UPARROW		= 128
K_DOWNARROW		= 129
K_LEFTARROW		= 130
K_RIGHTARROW	= 131

K_ALT			= 132
K_CTRL			= 133
K_SHIFT			= 134
K_F1			= 135
K_F2			= 136
K_F3			= 137
K_F4			= 138
K_F5			= 139
K_F6			= 140
K_F7			= 141
K_F8			= 142
K_F9			= 143
K_F10			= 144
K_F11			= 145
K_F12			= 146
K_INS			= 147
K_DEL			= 148
K_PGDN			= 149
K_PGUP			= 150
K_HOME			= 151
K_END			= 152

K_KP_HOME		= 160
K_KP_UPARROW	= 161
K_KP_PGUP		= 162
K_KP_LEFTARROW	= 163
K_KP_5			= 164
K_KP_RIGHTARROW	= 165
K_KP_END		= 166
K_KP_DOWNARROW	= 167
K_KP_PGDN		= 168
K_KP_ENTER		= 169
K_KP_INS   		= 170
K_KP_DEL		= 171
K_KP_SLASH		= 172
K_KP_MINUS		= 173
K_KP_PLUS		= 174

K_PAUSE			= 255

#
# mouse buttons generate virtual keys
#
K_MOUSE1		= 200
K_MOUSE2		= 201
K_MOUSE3		= 202

#
# joystick buttons
#
K_JOY1			= 203
K_JOY2			= 204
K_JOY3			= 205
K_JOY4			= 206

#
# aux keys are for multi-buttoned joysticks to generate so they can use
# the normal binding process
#
K_AUX1			= 207
K_AUX2			= 208
K_AUX3			= 209
K_AUX4			= 210
K_AUX5			= 211
K_AUX6			= 212
K_AUX7			= 213
K_AUX8			= 214
K_AUX9			= 215
K_AUX10			= 216
K_AUX11			= 217
K_AUX12			= 218
K_AUX13			= 219
K_AUX14			= 220
K_AUX15			= 221
K_AUX16			= 222
K_AUX17			= 223
K_AUX18			= 224
K_AUX19			= 225
K_AUX20			= 226
K_AUX21			= 227
K_AUX22			= 228
K_AUX23			= 229
K_AUX24			= 230
K_AUX25			= 231
K_AUX26			= 232
K_AUX27			= 233
K_AUX28			= 234
K_AUX29			= 235
K_AUX30			= 236
K_AUX31			= 237
K_AUX32			= 238

K_MWHEELDOWN	= 239
K_MWHEELUP		= 240

"""
extern char		*keybindings[256];
extern	int		key_repeats[256];

extern	int	anykeydown;
extern char chat_buffer[];
extern	int chat_bufferlen;
extern	qboolean	chat_team;

void Key_Event (int key, qboolean down, unsigned time);
void Key_Init (void);
void Key_WriteBindings (FILE *f);
void Key_SetBinding (int keynum, char *binding);
void Key_ClearStates (void);
int Key_GetKey (void);

#include "client.h"

/*

key up events are sent even if in console mode

*/


#define		MAXCMDLINE	256
char	key_lines[32][MAXCMDLINE];
int		key_linepos;
int		shift_down=false;
int	anykeydown;

int		edit_line=0;
int		history_line=0;
"""
key_waiting = None # int

keybindings = [] #char	*[256]
for i in range(256):
	keybindings.append(None)

"""
qboolean	consolekeys[256];	// if true, can't be rebound while in console
qboolean	menubound[256];	// if true, can't be rebound while in menu
int		keyshift[256];		// key to map to if shift held down in console
"""
key_repeats = [] #int[256], if > 1, it is autorepeating
for i in range(256):
	key_repeats.append(0)

keydown = [] #qboolean	[256];
for i in range(256):
	keydown.append(False)

"""
typedef struct
{
	char	*name;
	int		keynum;
} keyname_t;
"""
keynames = [ #keyname_t[]

	["TAB", K_TAB],
	["ENTER", K_ENTER],
	["ESCAPE", K_ESCAPE],
	["SPACE", K_SPACE],
	["BACKSPACE", K_BACKSPACE],
	["UPARROW", K_UPARROW],
	["DOWNARROW", K_DOWNARROW],
	["LEFTARROW", K_LEFTARROW],
	["RIGHTARROW", K_RIGHTARROW],

	["ALT", K_ALT],
	["CTRL", K_CTRL],
	["SHIFT", K_SHIFT],
	
	["F1", K_F1],
	["F2", K_F2],
	["F3", K_F3],
	["F4", K_F4],
	["F5", K_F5],
	["F6", K_F6],
	["F7", K_F7],
	["F8", K_F8],
	["F9", K_F9],
	["F10", K_F10],
	["F11", K_F11],
	["F12", K_F12],

	["INS", K_INS],
	["DEL", K_DEL],
	["PGDN", K_PGDN],
	["PGUP", K_PGUP],
	["HOME", K_HOME],
	["END", K_END],

	["MOUSE1", K_MOUSE1],
	["MOUSE2", K_MOUSE2],
	["MOUSE3", K_MOUSE3],

	["JOY1", K_JOY1],
	["JOY2", K_JOY2],
	["JOY3", K_JOY3],
	["JOY4", K_JOY4],

	["AUX1", K_AUX1],
	["AUX2", K_AUX2],
	["AUX3", K_AUX3],
	["AUX4", K_AUX4],
	["AUX5", K_AUX5],
	["AUX6", K_AUX6],
	["AUX7", K_AUX7],
	["AUX8", K_AUX8],
	["AUX9", K_AUX9],
	["AUX10", K_AUX10],
	["AUX11", K_AUX11],
	["AUX12", K_AUX12],
	["AUX13", K_AUX13],
	["AUX14", K_AUX14],
	["AUX15", K_AUX15],
	["AUX16", K_AUX16],
	["AUX17", K_AUX17],
	["AUX18", K_AUX18],
	["AUX19", K_AUX19],
	["AUX20", K_AUX20],
	["AUX21", K_AUX21],
	["AUX22", K_AUX22],
	["AUX23", K_AUX23],
	["AUX24", K_AUX24],
	["AUX25", K_AUX25],
	["AUX26", K_AUX26],
	["AUX27", K_AUX27],
	["AUX28", K_AUX28],
	["AUX29", K_AUX29],
	["AUX30", K_AUX30],
	["AUX31", K_AUX31],
	["AUX32", K_AUX32],

	["KP_HOME",			K_KP_HOME ],
	["KP_UPARROW",		K_KP_UPARROW ],
	["KP_PGUP",			K_KP_PGUP ],
	["KP_LEFTARROW",	K_KP_LEFTARROW ],
	["KP_5",			K_KP_5 ],
	["KP_RIGHTARROW",	K_KP_RIGHTARROW ],
	["KP_END",			K_KP_END ],
	["KP_DOWNARROW",	K_KP_DOWNARROW ],
	["KP_PGDN",			K_KP_PGDN ],
	["KP_ENTER",		K_KP_ENTER ],
	["KP_INS",			K_KP_INS ],
	["KP_DEL",			K_KP_DEL ],
	["KP_SLASH",		K_KP_SLASH ],
	["KP_MINUS",		K_KP_MINUS ],
	["KP_PLUS",			K_KP_PLUS ],

	["MWHEELUP", K_MWHEELUP ],
	["MWHEELDOWN", K_MWHEELDOWN ],

	["PAUSE", K_PAUSE],

	["SEMICOLON", ord(';')],	# because a raw semicolon seperates commands

	#[NULL,0]
]

"""
==============================================================================

			LINE TYPING INTO THE CONSOLE

==============================================================================
*/

void CompleteCommand (void)
{
	char	*cmd, *s;

	s = key_lines[edit_line]+1;
	if (*s == '\\' || *s == '/')
		s++;

	cmd = Cmd_CompleteCommand (s);
	if (!cmd)
		cmd = Cvar_CompleteVariable (s);
	if (cmd)
	{
		key_lines[edit_line][1] = '/';
		strcpy (key_lines[edit_line]+2, cmd);
		key_linepos = strlen(cmd)+2;
		key_lines[edit_line][key_linepos] = ' ';
		key_linepos++;
		key_lines[edit_line][key_linepos] = 0;
		return;
	}
}

/*
====================
Key_Console

Interactive line editing and console scrollback
====================
*/
void Key_Console (int key)
{

	switch ( key )
	{
	case K_KP_SLASH:
		key = '/';
		break;
	case K_KP_MINUS:
		key = '-';
		break;
	case K_KP_PLUS:
		key = '+';
		break;
	case K_KP_HOME:
		key = '7';
		break;
	case K_KP_UPARROW:
		key = '8';
		break;
	case K_KP_PGUP:
		key = '9';
		break;
	case K_KP_LEFTARROW:
		key = '4';
		break;
	case K_KP_5:
		key = '5';
		break;
	case K_KP_RIGHTARROW:
		key = '6';
		break;
	case K_KP_END:
		key = '1';
		break;
	case K_KP_DOWNARROW:
		key = '2';
		break;
	case K_KP_PGDN:
		key = '3';
		break;
	case K_KP_INS:
		key = '0';
		break;
	case K_KP_DEL:
		key = '.';
		break;
	}

	if ( ( toupper( key ) == 'V' && keydown[K_CTRL] ) ||
		 ( ( ( key == K_INS ) || ( key == K_KP_INS ) ) && keydown[K_SHIFT] ) )
	{
		char *cbd;
		
		if ( ( cbd = Sys_GetClipboardData() ) != 0 )
		{
			int i;

			strtok( cbd, "\n\r\b" );

			i = strlen( cbd );
			if ( i + key_linepos >= MAXCMDLINE)
				i= MAXCMDLINE - key_linepos;

			if ( i > 0 )
			{
				cbd[i]=0;
				strcat( key_lines[edit_line], cbd );
				key_linepos += i;
			}
			free( cbd );
		}

		return;
	}

	if ( key == 'l' ) 
	{
		if ( keydown[K_CTRL] )
		{
			Cbuf_AddText ("clear\n");
			return;
		}
	}

	if ( key == K_ENTER || key == K_KP_ENTER )
	{	// backslash text are commands, else chat
		if (key_lines[edit_line][1] == '\\' || key_lines[edit_line][1] == '/')
			Cbuf_AddText (key_lines[edit_line]+2);	// skip the >
		else
			Cbuf_AddText (key_lines[edit_line]+1);	// valid command

		Cbuf_AddText ("\n");
		Com_Printf ("%s\n",key_lines[edit_line]);
		edit_line = (edit_line + 1) & 31;
		history_line = edit_line;
		key_lines[edit_line][0] = ']';
		key_linepos = 1;
		if (cls.state == ca_disconnected)
			SCR_UpdateScreen ();	// force an update, because the command
									// may take some time
		return;
	}

	if (key == K_TAB)
	{	// command completion
		CompleteCommand ();
		return;
	}
	
	if ( ( key == K_BACKSPACE ) || ( key == K_LEFTARROW ) || ( key == K_KP_LEFTARROW ) || ( ( key == 'h' ) && ( keydown[K_CTRL] ) ) )
	{
		if (key_linepos > 1)
			key_linepos--;
		return;
	}

	if ( ( key == K_UPARROW ) || ( key == K_KP_UPARROW ) ||
		 ( ( key == 'p' ) && keydown[K_CTRL] ) )
	{
		do
		{
			history_line = (history_line - 1) & 31;
		} while (history_line != edit_line
				&& !key_lines[history_line][1]);
		if (history_line == edit_line)
			history_line = (edit_line+1)&31;
		strcpy(key_lines[edit_line], key_lines[history_line]);
		key_linepos = strlen(key_lines[edit_line]);
		return;
	}

	if ( ( key == K_DOWNARROW ) || ( key == K_KP_DOWNARROW ) ||
		 ( ( key == 'n' ) && keydown[K_CTRL] ) )
	{
		if (history_line == edit_line) return;
		do
		{
			history_line = (history_line + 1) & 31;
		}
		while (history_line != edit_line
			&& !key_lines[history_line][1]);
		if (history_line == edit_line)
		{
			key_lines[edit_line][0] = ']';
			key_linepos = 1;
		}
		else
		{
			strcpy(key_lines[edit_line], key_lines[history_line]);
			key_linepos = strlen(key_lines[edit_line]);
		}
		return;
	}

	if (key == K_PGUP || key == K_KP_PGUP )
	{
		con.display -= 2;
		return;
	}

	if (key == K_PGDN || key == K_KP_PGDN ) 
	{
		con.display += 2;
		if (con.display > con.current)
			con.display = con.current;
		return;
	}

	if (key == K_HOME || key == K_KP_HOME )
	{
		con.display = con.current - con.totallines + 10;
		return;
	}

	if (key == K_END || key == K_KP_END )
	{
		con.display = con.current;
		return;
	}
	
	if (key < 32 || key > 127)
		return;	// non printable
		
	if (key_linepos < MAXCMDLINE-1)
	{
		key_lines[edit_line][key_linepos] = key;
		key_linepos++;
		key_lines[edit_line][key_linepos] = 0;
	}

}

#============================================================================

qboolean	chat_team;
char		chat_buffer[MAXCMDLINE];
int			chat_bufferlen = 0;

void Key_Message (int key)
{

	if ( key == K_ENTER || key == K_KP_ENTER )
	{
		if (chat_team)
			Cbuf_AddText ("say_team \"");
		else
			Cbuf_AddText ("say \"");
		Cbuf_AddText(chat_buffer);
		Cbuf_AddText("\"\n");

		cls.key_dest = key_game;
		chat_bufferlen = 0;
		chat_buffer[0] = 0;
		return;
	}

	if (key == K_ESCAPE)
	{
		cls.key_dest = key_game;
		chat_bufferlen = 0;
		chat_buffer[0] = 0;
		return;
	}

	if (key < 32 || key > 127)
		return;	// non printable

	if (key == K_BACKSPACE)
	{
		if (chat_bufferlen)
		{
			chat_bufferlen--;
			chat_buffer[chat_bufferlen] = 0;
		}
		return;
	}

	if (chat_bufferlen == sizeof(chat_buffer)-1)
		return; // all full

	chat_buffer[chat_bufferlen++] = key;
	chat_buffer[chat_bufferlen] = 0;
}
"""
"""
#============================================================================



===================
Key_StringToKeynum

Returns a key number to be used to index keybindings[] by looking at
the given string.  Single ascii characters return themselves, while
the K_* names are matched up.
===================
"""
def Key_StringToKeynum (strIn): #char * (returns int)

	#keyname_t	*kn;
	
	if strIn is None or len(strIn) == 0:
		return -1
	if len(strIn) == 1:
		return ord(strIn)

	for kn in keynames:
		if not q_shared.Q_strcasecmp(strIn, kn[0]):
			return kn[1]
	
	return -1
	
	
"""
===================
Key_KeynumToString

Returns a string (either a single ascii char, or a K_* name) for the
given keynum.
FIXME: handle quote special (general escape sequence?)
===================
"""
def Key_KeynumToString (keynum): # int (returns char *)

	#keyname_t	*kn;	
	
	if keynum == -1:
		return "<KEY NOT FOUND>"
	if keynum > 32 and keynum < 127:
		# printable ascii
		return chr(keynum)
		
	for kn in keynames:
		if keynum == kn[1]:
			return kn[0]

	return "<UNKNOWN KEYNUM>"

"""
===================
Key_SetBinding
===================
"""
def Key_SetBinding (keynum, binding): #int, char *
		
	if keynum == -1:
		return;
	
	# allocate memory for new binding
	if len(binding) == 0:
		keybindings[keynum] = None
	else:
		keybindings[keynum] = binding

"""
===================
Key_Unbind_f
===================
"""
def Key_Unbind_f ():

	#int		b;

	if cmd.Cmd_Argc() != 2:
	
		common.Com_Printf ("unbind <key> : remove commands from a key\n")
		return
	
	
	b = Key_StringToKeynum (cmd.Cmd_Argv(1))
	if b==-1:
	
		Com_Printf ("\"{}\" isn't a valid key\n".format( cmd.Cmd_Argv(1)))
		return;
	

	Key_SetBinding (b, "")

def Key_Unbindall_f ():
	
	for i in range(256):
		if keybindings[i]:
			Key_SetBinding (i, "")



"""
===================
Key_Bind_f
===================
"""
def Key_Bind_f ():
	
	c = cmd.Cmd_Argc()

	if c < 2:
	
		common.Com_Printf ("bind <key> [command] : attach a command to a key\n")
		return
	
	b = Key_StringToKeynum (cmd.Cmd_Argv(1))

	if b==-1:
	
		common.Com_Printf ("\"{}\" isn't a valid key\n".format(Cmd_Argv(1)))
		return
	
	if c == 2:
	
		if keybindings[b] is not None:
			common.Com_Printf ("\"{}\" = \"{}\"\n".format(cmd.Cmd_Argv(1), keybindings[b]))
		else:
			common.Com_Printf ("\"{}\" is not bound\n".format( cmd.Cmd_Argv(1)) )
		return
	
	
	# copy the rest of the command line
	cmdArr = []		# start out with a null string
	for i in range(2, c):
	
		cmdArr.append(cmd.Cmd_Argv(i))
		if i != (c-1):
			cmdArr.append(" ")
	
	Key_SetBinding (b, "".join(cmdArr))


"""
============
Key_WriteBindings

Writes lines containing "bind key value"
============
*/
void Key_WriteBindings (FILE *f)
{
	int		i;

	for (i=0 ; i<256 ; i++)
		if (keybindings[i] && keybindings[i][0])
			fprintf (f, "bind %s \"%s\"\n", Key_KeynumToString(i), keybindings[i]);
}


/*
============
Key_Bindlist_f

============
"""
def Key_Bindlist_f ():

	for i in range(256):
		if keybindings[i] is not None:
			common.Com_Printf ("{} \"{}\"\n".format(Key_KeynumToString(i), keybindings[i]))

"""
===================
Key_Init
===================
"""
def Key_Init ():

	"""
	int		i;

	for (i=0 ; i<32 ; i++)
	{
		key_lines[i][0] = ']';
		key_lines[i][1] = 0;
	}
	key_linepos = 1;
	
	#
	# init ascii characters in console mode
	#
	for (i=32 ; i<128 ; i++)
		consolekeys[i] = true;
	consolekeys[K_ENTER] = true;
	consolekeys[K_KP_ENTER] = true;
	consolekeys[K_TAB] = true;
	consolekeys[K_LEFTARROW] = true;
	consolekeys[K_KP_LEFTARROW] = true;
	consolekeys[K_RIGHTARROW] = true;
	consolekeys[K_KP_RIGHTARROW] = true;
	consolekeys[K_UPARROW] = true;
	consolekeys[K_KP_UPARROW] = true;
	consolekeys[K_DOWNARROW] = true;
	consolekeys[K_KP_DOWNARROW] = true;
	consolekeys[K_BACKSPACE] = true;
	consolekeys[K_HOME] = true;
	consolekeys[K_KP_HOME] = true;
	consolekeys[K_END] = true;
	consolekeys[K_KP_END] = true;
	consolekeys[K_PGUP] = true;
	consolekeys[K_KP_PGUP] = true;
	consolekeys[K_PGDN] = true;
	consolekeys[K_KP_PGDN] = true;
	consolekeys[K_SHIFT] = true;
	consolekeys[K_INS] = true;
	consolekeys[K_KP_INS] = true;
	consolekeys[K_KP_DEL] = true;
	consolekeys[K_KP_SLASH] = true;
	consolekeys[K_KP_PLUS] = true;
	consolekeys[K_KP_MINUS] = true;
	consolekeys[K_KP_5] = true;

	consolekeys['`'] = false;
	consolekeys['~'] = false;

	for (i=0 ; i<256 ; i++)
		keyshift[i] = i;
	for (i='a' ; i<='z' ; i++)
		keyshift[i] = i - 'a' + 'A';
	keyshift['1'] = '!';
	keyshift['2'] = '@';
	keyshift['3'] = '#';
	keyshift['4'] = '$';
	keyshift['5'] = '%';
	keyshift['6'] = '^';
	keyshift['7'] = '&';
	keyshift['8'] = '*';
	keyshift['9'] = '(';
	keyshift['0'] = ')';
	keyshift['-'] = '_';
	keyshift['='] = '+';
	keyshift[','] = '<';
	keyshift['.'] = '>';
	keyshift['/'] = '?';
	keyshift[';'] = ':';
	keyshift['\''] = '"';
	keyshift['['] = '{';
	keyshift[']'] = '}';
	keyshift['`'] = '~';
	keyshift['\\'] = '|';

	menubound[K_ESCAPE] = true;
	for (i=0 ; i<12 ; i++)
		menubound[K_F1+i] = true;
"""
	#
	# register our functions
	#

	cmd.Cmd_AddCommand ("bind",Key_Bind_f);
	cmd.Cmd_AddCommand ("unbind",Key_Unbind_f);
	cmd.Cmd_AddCommand ("unbindall",Key_Unbindall_f);
	cmd.Cmd_AddCommand ("bindlist",Key_Bindlist_f);

"""
===================
Key_Event

Called by the system between frames for both key up and key down events
Should NOT be called during an interrupt!
===================
"""

def Key_Event (key, down, time): #int, qboolean, unsigned

	#char	*kb;
	#char	cmd[1024];

	global key_waiting, key_repeats, keydown, menubound, consolekeys
	# hack for modal presses
	if key_waiting == -1:
	
		if down:
			key_waiting = key
		return
	
	# update auto-repeat status
	if down:
	
		key_repeats[key] += 1
		if key != K_BACKSPACE \
			and key != K_PAUSE \
			and key != K_PGUP \
			and key != K_KP_PGUP \
			and key != K_PGDN \
			and key != K_KP_PGDN \
			and key_repeats[key] > 1:
			return	# ignore most autorepeats
			
		if key >= 200 and not keybindings[key]:
			common.Com_Printf ("{} is unbound, hit F4 to set.\n".format(Key_KeynumToString (key) ))
	
	else:
	
		key_repeats[key] = 0
	
	
	if key == K_SHIFT:
		shift_down = down

	# console key is hardcoded, so the user can never unbind it
	if key == '`' or key == '~':
	
		if not down:
			return
		console.Con_ToggleConsole_f ()
		return
	
	
	# any key during the attract mode will bring up the menu
	if client.cl.attractloop and client.cls.key_dest != key_menu and \
		not(key >= K_F1 and key <= K_F12):
		key = K_ESCAPE

	# menu key is hardcoded, so the user can never unbind it
	if key == K_ESCAPE:
	
		if not down:
			return

		if client.cl.frame.playerstate.stats[STAT_LAYOUTS] and client.cls.key_dest == key_game:
			# put away help computer / inventory
			cmd.Cbuf_AddText ("cmd putaway\n")
			return
		
		if client.cls.key_dest == keydest_t.key_message:
			Key_Message (key)
		elif client.cls.key_dest == keydest_t.key_menu:
			M_Keydown (key)
		elif client.cls.key_dest in [keydest_t.key_game, keydest_t.key_console]:
			M_Menu_Main_f ()
		else:
			Com_Error (q_shared.ERR_FATAL, "Bad cls.key_dest")

		return
	
	
	# track if any key is down for BUTTON_ANY
	keydown[key] = down
	if down:
	
		if key_repeats[key] == 1:
			anykeydown+=1
	
	else:
	
		anykeydown-=1
		if anykeydown < 0:
			anykeydown = 0
	

	#
	# key up events only generate commands if the game key binding is
	# a button command (leading + sign).  These will occur even in console mode,
	# to keep the character from continuing an action started before a console
	# switch.  Button commands include the kenum as a parameter, so multiple
	# downs can be matched with ups
	#
	if not down:
	
		kb = keybindings[key]
		if kb and kb[0] == '+':
		
			cmdStr = "-%s %i %i\n".format(kb+1, key, time)
			cmd.Cbuf_AddText (cmd)
		
		if keyshift[key] != key:
		
			kb = keybindings[keyshift[key]]
			if kb and kb[0] == '+':
			
				cmdStr = "-{} %i %i\n".format(kb+1, key, time)
				cmd.Cbuf_AddText (cmdStr)
		
		return
	

	#
	# if not a consolekey, send to the interpreter no matter what mode is
	#
	if ( (client.cls.key_dest == key_menu and menubound[key])
		or (client.cls.key_dest == key_console and not consolekeys[key])
		or (client.cls.key_dest == key_game and ( client.cls.state == ca_active or not consolekeys[key] ) ) ):
	
		kb = keybindings[key]
		if kb:
		
			if kb[0] == '+':
				# button commands add keynum and time as a parm
				cmdStr = "%s %i %i\n".format(kb, key, time)
				cmd.Cbuf_AddText (cmdStr)
			
			else:			
				cmd.Cbuf_AddText (kb)
				cmd.Cbuf_AddText ("\n")

		return
	
	if not down:
		return		# other systems only care about key down events

	if shift_down:
		key = keyshift[key]

	if client.cls.key_dest == keydest_t.key_message:
		Key_Message (key)
	elif client.cls.key_dest == keydest_t.key_menu:
		M_Keydown (key)
	elif client.cls.key_dest in [keydest_t.key_game, keydest_t.key_console]:
		Key_Console (key)
	else:
		common.Com_Error (q_shared.ERR_FATAL, "Bad cls.key_dest")

"""
===================
Key_ClearStates
===================
*/
void Key_ClearStates (void)
{
	int		i;

	anykeydown = false;

	for (i=0 ; i<256 ; i++)
	{
		if ( keydown[i] || key_repeats[i] )
			Key_Event( i, false, 0 );
		keydown[i] = 0;
		key_repeats[i] = 0;
	}
}


/*
===================
Key_GetKey
===================
*/
int Key_GetKey (void)
{
	key_waiting = -1;

	while (key_waiting == -1)
		Sys_SendKeyEvents ();

	return key_waiting;
}
"""
