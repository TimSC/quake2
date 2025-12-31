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
from qcommon import cvar, cmd, common, files
from client import cl_main, client, cl_scrn, snd_dma, keys, qmenu, cl_view, ref
from linux import vid_so, in_linux, q_shlinux, net_udp
from game import q_shared

"""
#include <ctype.h>
#ifdef _WIN32
#include <io.h>
#endif
#include "client.h"
#include "../client/qmenu.h"
"""

MAXMENUITEMS	= 64

MTYPE_SLIDER		= 0
MTYPE_LIST			= 1
MTYPE_ACTION		= 2
MTYPE_SPINCONTROL	= 3
MTYPE_SEPARATOR  	= 4
MTYPE_FIELD			= 5

QMF_LEFT_JUSTIFY	= 0x00000001
QMF_GRAYED			= 0x00000002
QMF_NUMBERSONLY		= 0x00000004

class menuframework_s(object):

	def __init__(self):
		self.x, self.y = 0, 0 #int
		self.cursor = 0 #int

		self.nitems = 0 #int
		self.nslots = 0 #int
		self.items = [] #void *[64]

		self.statusbar = None #const char *

		self.cursordraw = None #void (*cursordraw)( struct _tag_menuframework *m )
	
class menucommon_s(object):

	def __init__(self):
		self.type = -1 #int
		self.name = None #const char *
		self.x, self.y = 0, 0 #int
		self.parent = None #menuframework_s *
		self.cursor_offset = 0 #int
		self.localdata = [0, 0, 0, 0] #int[4]
		self.flags = 0 #unsigned

		self.statusbar = None # const char *

		self.callback = None # void (*)( void *self );
		self.statusbarfunc = None # void (*)( void *self );
		self.ownerdraw = None # void (*)( void *self );
		self.cursordraw = None # void (*)( void *self );


class menufield_s(menucommon_s):

	def __init__(self):
		super().__init__()
		self.type = MTYPE_FIELD

		self.buffer = None # char[80]
		self.cursor = 0 # int
		self.length = 0 # int
		self.visible_length = 0 # int
		self.visible_offse = 0 # int


class menuslider_s(menucommon_s):

	def __init__(self):
		super().__init__()
		self.type = MTYPE_SLIDER

		self.minvalue = 0.0 #float
		self.maxvalue = 0.0 #float
		self.curvalue = 0.0 #float

		self.range = 0.0 #float


class menulist_s(menucommon_s):

	def __init__(self):
		super().__init__()
		self.type = MTYPE_LIST

		self.curvalue = 0 #int

		self.itemnames = [] #const char **

class menuaction_s(menucommon_s):

	def __init__(self):
		super().__init__()
		self.type = MTYPE_ACTION


class menuseparator_s(menucommon_s):

	def __init__(self):
		super().__init__()
		self.type = MTYPE_SEPARATOR

class menuspincontrol_s(menucommon_s):

	def __init__(self):
		super().__init__()
		self.type = MTYPE_SPINCONTROL

		self.curvalue = 0 #int

		self.itemnames = [] #const char **

m_main_cursor = 0 #static int

NUM_CURSOR_FRAMES = 15

menu_in_sound		= "misc/menu1.wav" #static char *
menu_move_sound		= "misc/menu2.wav" #static char *
menu_out_sound		= "misc/menu3.wav" #static char *
"""
void M_Menu_Main_f (void);
	void M_Menu_Game_f (void);
		void M_Menu_LoadGame_f (void);
		void M_Menu_SaveGame_f (void);
		void M_Menu_PlayerConfig_f (void);
			void M_Menu_DownloadOptions_f (void);
		void M_Menu_Credits_f( void );
	void M_Menu_Multiplayer_f( void );
		void M_Menu_JoinServer_f (void);
			void M_Menu_AddressBook_f( void );
		void M_Menu_StartServer_f (void);
			void M_Menu_DMOptions_f (void);
	void M_Menu_Video_f (void);
	void M_Menu_Options_f (void);
		void M_Menu_Keys_f (void);
	void M_Menu_Quit_f (void);

	void M_Menu_Credits( void );
"""
m_entersound = True #qboolean	 play after drawing a frame, so caching
								# won't disrupt the sound

m_drawfunc = None #void	(*) (void);
m_keyfunc = None # const char *(*) (int key);
"""
//=============================================================================
/* Support Routines */
"""
MAX_MENU_DEPTH	= 8

class menulayer_t(object):
	def __init__(self, drawIn=None, keyIn=None):
		self.draw = drawIn #void	(*draw) (void);
		self.key = keyIn #const char *(*key) (int k);

m_layers = [] #menulayer_t	[MAX_MENU_DEPTH];
m_menudepth = 0

def M_Banner( name ): #char *

	#int w, h;

	w, h = vid_so.re.DrawGetPicSize ( name )
	vid_so.re.DrawPic( vid_so.viddef.width // 2 - w // 2, vid_so.viddef.height // 2 - 110, name )

def M_PushMenu ( draw, key ): #void (*) (void), const char *(*) (int k)

	global m_layers, m_drawfunc, m_keyfunc
	"""
	int		i;
	"""

	if cvar.Cvar_VariableValue ("maxclients") == 1 \
		and common.Com_ServerState ():
		cvar.Cvar_Set ("paused", "1");

	# if this menu is already present, drop back to that level
	# to avoid stacking menus by hotkeys
	found = None
	for i, layer in enumerate(m_layers):
		if layer.draw == draw and \
			layer.key == key:
		
			#m_menudepth = i
			found = i

	if found is not None:
		m_layers = m_layers[:found]

	else:
	
		if m_menudepth >= MAX_MENU_DEPTH:
			qcommon.Com_Error (q_shared.ERR_FATAL, "M_PushMenu: MAX_MENU_DEPTH")
		
		m_layers.append(menulayer_t(m_drawfunc, m_keyfunc))
		#m_menudepth++;
	
	m_drawfunc = draw
	m_keyfunc = key

	m_entersound = True

	cl_main.cls.key_dest = client.keydest_t.key_menu


def M_ForceMenuOff ():

	global m_layers, m_drawfunc, m_keyfunc

	m_drawfunc = 0
	m_keyfunc = 0
	cl_main.cls.key_dest = client.keydest_t.key_game
	#m_menudepth = 0
	m_layers = []
	#Key_ClearStates ()
	cvar.Cvar_Set ("paused", "0")


def M_PopMenu ():

	global m_layers, m_drawfunc, m_keyfunc

	snd_dma.S_StartLocalSound( menu_out_sound )
	if len(m_layers) == 0:
		common.Com_Error (q_shared.ERR_FATAL, "M_PopMenu: depth < 1")
	#m_menudepth--;

	layer = m_layers.pop()
	m_drawfunc = layer.draw
	m_keyfunc = layer.key

	if len(m_layers) == 0:
		M_ForceMenuOff ()



def Default_MenuKey( m, key ): # menuframework_s *, int (returns const char *)

	sound = None #const char *
	#menucommon_s *item;

	if m is not None:
	
		item = qmenu.Menu_ItemAtCursor( m )
		if item is not None:
		
			if item.type == MTYPE_FIELD:
			
				if qmenu.Field_Key( item, key ):
					return None
	
	if key == keys.K_ESCAPE:
		M_PopMenu()
		return menu_out_sound

	elif key == keys.K_KP_UPARROW or key == keys.K_UPARROW:
		if m is not None:
		
			m.cursor-=1
			qmenu.Menu_AdjustCursor( m, -1 )
			sound = menu_move_sound
		
	elif key == keys.K_TAB:
		if m is not None:
		
			m.cursor+=1
			qmenu.Menu_AdjustCursor( m, 1 )
			sound = menu_move_sound
		

	elif key == keys.K_KP_DOWNARROW or key == keys.K_DOWNARROW:
		if m is not None:
		
			m.cursor+=1
			qmenu.Menu_AdjustCursor( m, 1 )
			sound = menu_move_sound

	elif key == keys.K_KP_LEFTARROW or key == keys.K_LEFTARROW:
		if m is not None:
		
			qmenu.Menu_SlideItem( m, -1 )
			sound = menu_move_sound

	elif key == keys.K_KP_RIGHTARROW or key == keys.K_RIGHTARROW:
		if m is not None:
		
			qmenu.Menu_SlideItem( m, 1 )
			sound = menu_move_sound


	elif key in [keys.K_MOUSE1, keys.K_MOUSE2, keys.K_MOUSE3,
		keys.K_JOY1, keys.K_JOY2, keys.K_JOY3, keys.K_JOY4,
		keys.K_AUX1, keys.K_AUX2, keys.K_AUX3, keys.K_AUX4,
		keys.K_AUX5, keys.K_AUX6, keys.K_AUX7, keys.K_AUX8,
		keys.K_AUX9, keys.K_AUX10, keys.K_AUX11, keys.K_AUX12,
		keys.K_AUX13, keys.K_AUX14, keys.K_AUX15, keys.K_AUX16,
		keys.K_AUX17, keys.K_AUX18, keys.K_AUX19, keys.K_AUX20,
		keys.K_AUX21, keys.K_AUX22, keys.K_AUX23, keys.K_AUX24,
		keys.K_AUX25, keys.K_AUX26, keys.K_AUX27, keys.K_AUX28,
		keys.K_AUX29, keys.K_AUX30, keys.K_AUX31, keys.K_AUX32,
		keys.K_KP_ENTER, keys.K_ENTER]:
		
		if m is not None:
			qmenu.Menu_SelectItem( m )
		sound = menu_move_sound

	return sound

"""
//=============================================================================

/*
================
M_DrawCharacter

Draws one solid graphics character
cx and cy are in 320*240 coordinates, and will be centered on
higher res screens.
================
*/
void M_DrawCharacter (int cx, int cy, int num)
{
	vid_so.re.DrawChar ( cx + ((vid_so.viddef.width - 320)>>1), cy + ((vid_so.viddef.height - 240)>>1), num);
}
"""
def M_DrawCharacter(cx, cy, num): #int, int, int

	vid_so.re.DrawChar(
		cx + ((vid_so.viddef.width - 320) >> 1),
		cy + ((vid_so.viddef.height - 240) >> 1),
		num,
	)


def M_Print(cx, cy, strIn): #int, int, char *

	for ch in strIn:
		M_DrawCharacter(cx, cy, ord(ch) + 128)
		cx += 8


def M_PrintWhite(cx, cy, strIn): #int, int, char *

	for ch in strIn:
		M_DrawCharacter(cx, cy, ord(ch))
		cx += 8


def M_DrawPic(x, y, pic): #int, int, char *

	vid_so.re.DrawPic(
		x + ((vid_so.viddef.width - 320) >> 1),
		y + ((vid_so.viddef.height - 240) >> 1),
		pic,
	)


"""
/*
=============
M_DrawCursor

Draws an animating cursor with the point at
x,y.  The pic will extend to the left of x,
and both above and below y.
=============
"""
cached = False

def M_DrawCursor( x, y, f ): #int, int, int

	global cached
	#char	cursorname[80];
	#static qboolean cached;

	if not cached:
	
		for i in range(NUM_CURSOR_FRAMES):
		
			cursorname = "m_cursor{:d}".format(i)
			vid_so.re.RegisterPic( cursorname )
		
		cached = True
	
	cursorname = "m_cursor{:d}".format(f)
	vid_so.re.DrawPic( x, y, cursorname )



def M_DrawTextBox(x, y, width, lines): #int, int, int, int

	# draw left side
	cx = x
	cy = y
	M_DrawCharacter(cx, cy, 1)
	for _ in range(lines):
		cy += 8
		M_DrawCharacter(cx, cy, 4)
	M_DrawCharacter(cx, cy + 8, 7)

	# draw middle
	cx += 8
	while width > 0:
		cy = y
		M_DrawCharacter(cx, cy, 2)
		for _ in range(lines):
			cy += 8
			M_DrawCharacter(cx, cy, 5)
		M_DrawCharacter(cx, cy + 8, 8)
		width -= 1
		cx += 8

	# draw right side
	cy = y
	M_DrawCharacter(cx, cy, 3)
	for _ in range(lines):
		cy += 8
		M_DrawCharacter(cx, cy, 6)
	M_DrawCharacter(cx, cy + 8, 9)


"""
/*
=======================================================================

MAIN MENU

=======================================================================
"""
MAIN_ITEMS	= 5


def M_Main_Draw ():

	global m_main_cursor

	"""
	int i;
	int w, h;
	int ystart;
	int	xoffset;
	int totalheight = 0;
	char litname[80];
	"""
	names = [
		"m_main_game",
		"m_main_multiplayer",
		"m_main_options",
		"m_main_video",
		"m_main_quit"] #char *[]

	widest = -1
	totalheight = 0

	for name in names:
	
		w, h = vid_so.re.DrawGetPicSize( name )

		if w > widest:
			widest = w
		totalheight += ( h + 12 )
	

	ystart = vid_so.viddef.height // 2 - 110
	xoffset = ( vid_so.viddef.width - widest + 70 ) // 2

	
	for i, name in enumerate(names):
	
		if i != m_main_cursor:
			vid_so.re.DrawPic( xoffset, ystart + i * 40 + 13, name )
	
	litname = names[m_main_cursor] + "_sel"
	vid_so.re.DrawPic( xoffset, ystart + m_main_cursor * 40 + 13, litname )

	M_DrawCursor( xoffset - 25, ystart + m_main_cursor * 40 + 11, (int(cl_main.cls.realtime) // 100)%NUM_CURSOR_FRAMES )

	w, h = vid_so.re.DrawGetPicSize( "m_main_plaque" )
	vid_so.re.DrawPic( xoffset - 30 - w, ystart, "m_main_plaque" )

	vid_so.re.DrawPic( xoffset - 30 - w, ystart + h + 5, "m_main_logo" )


def M_Main_Key (key): #int (returns const char *)

	global m_entersound, m_main_cursor

	sound = menu_move_sound #const char *

	if key == keys.K_ESCAPE:
		M_PopMenu ()

	elif key == keys.K_KP_DOWNARROW or key == keys.K_DOWNARROW:
		m_main_cursor += 1
		if m_main_cursor >= MAIN_ITEMS:
			m_main_cursor = 0
		return sound

	elif key == keys.K_KP_UPARROW or key == keys.K_UPARROW:

		m_main_cursor -= 1
		if m_main_cursor < 0:
			m_main_cursor = MAIN_ITEMS - 1
		return sound;

	elif key == keys.K_KP_ENTER or key == keys.K_ENTER:

		m_entersound = True

		if m_main_cursor == 0:
			M_Menu_Game_f ()
		elif m_main_cursor == 1:
			M_Menu_Multiplayer_f()
		elif m_main_cursor == 2:
			M_Menu_Options_f ()
		elif m_main_cursor == 3:
			M_Menu_Video_f ()
		elif m_main_cursor == 4:
			M_Menu_Quit_f ()

	return None



def M_Menu_Main_f ():

	M_PushMenu (M_Main_Draw, M_Main_Key)


"""
=======================================================================

MULTIPLAYER MENU

=======================================================================
*/
static menuframework_s	s_multiplayer_menu;
static menuaction_s		s_join_network_server_action;
static menuaction_s		s_start_network_server_action;
static menuaction_s		s_player_setup_action;

static void Multiplayer_MenuDraw (void)
{
	M_Banner( "m_banner_multiplayer" );

	qmenu.Menu_AdjustCursor( &s_multiplayer_menu, 1 );
	qmenu.Menu_Draw( &s_multiplayer_menu );
}

static void PlayerSetupFunc( void *unused )
{
	M_Menu_PlayerConfig_f();
}

static void JoinNetworkServerFunc( void *unused )
{
	M_Menu_JoinServer_f();
}

static void StartNetworkServerFunc( void *unused )
{
	M_Menu_StartServer_f ();
}

void Multiplayer_MenuInit( void )
{
	s_multiplayer_menu.x = vid_so.viddef.width * 0.50 - 64;
	s_multiplayer_menu.nitems = 0;

	s_join_network_server_action.type	= MTYPE_ACTION;
	s_join_network_server_action.flags  = QMF_LEFT_JUSTIFY;
	s_join_network_server_action.x		= 0;
	s_join_network_server_action.y		= 0;
	s_join_network_server_action.name	= " join network server";
	s_join_network_server_action.callback = JoinNetworkServerFunc;

	s_start_network_server_action.type	= MTYPE_ACTION;
	s_start_network_server_action.flags  = QMF_LEFT_JUSTIFY;
	s_start_network_server_action.x		= 0;
	s_start_network_server_action.y		= 10;
	s_start_network_server_action.name	= " start network server";
	s_start_network_server_action.callback = StartNetworkServerFunc;

	s_player_setup_action.type	= MTYPE_ACTION;
	s_player_setup_action.flags  = QMF_LEFT_JUSTIFY;
	s_player_setup_action.x		= 0;
	s_player_setup_action.y		= 20;
	s_player_setup_action.name	= " player setup";
	s_player_setup_action.callback = PlayerSetupFunc;

	qmenu.Menu_AddItem( &s_multiplayer_menu, s_join_network_server_action );
	qmenu.Menu_AddItem( &s_multiplayer_menu, s_start_network_server_action );
	qmenu.Menu_AddItem( &s_multiplayer_menu, s_player_setup_action );

	Menu_SetStatusBar( &s_multiplayer_menu, NULL );

	qmenu.Menu_Center( &s_multiplayer_menu );
}

const char *Multiplayer_MenuKey( int key )
{
	return Default_MenuKey( &s_multiplayer_menu, key );
}
"""
## Multiplayer menu
s_multiplayer_menu = menuframework_s()
s_join_network_server_action = menuaction_s()
s_start_network_server_action = menuaction_s()
s_player_setup_action = menuaction_s()


def Multiplayer_MenuDraw():

	M_Banner("m_banner_multiplayer")
	qmenu.Menu_AdjustCursor(s_multiplayer_menu, 1)
	qmenu.Menu_Draw(s_multiplayer_menu)


def PlayerSetupFunc(unused):

	M_Menu_PlayerConfig_f()


def JoinNetworkServerFunc(unused):

	M_Menu_JoinServer_f()


def StartNetworkServerFunc(unused):

	M_Menu_StartServer_f()


def Multiplayer_MenuInit():

	s_multiplayer_menu.x = vid_so.viddef.width * 0.50 - 64
	s_multiplayer_menu.nitems = 0

	s_join_network_server_action.type = MTYPE_ACTION
	s_join_network_server_action.flags = QMF_LEFT_JUSTIFY
	s_join_network_server_action.x = 0
	s_join_network_server_action.y = 0
	s_join_network_server_action.name = " join network server"
	s_join_network_server_action.callback = JoinNetworkServerFunc

	s_start_network_server_action.type = MTYPE_ACTION
	s_start_network_server_action.flags = QMF_LEFT_JUSTIFY
	s_start_network_server_action.x = 0
	s_start_network_server_action.y = 10
	s_start_network_server_action.name = " start network server"
	s_start_network_server_action.callback = StartNetworkServerFunc

	s_player_setup_action.type = MTYPE_ACTION
	s_player_setup_action.flags = QMF_LEFT_JUSTIFY
	s_player_setup_action.x = 0
	s_player_setup_action.y = 20
	s_player_setup_action.name = " player setup"
	s_player_setup_action.callback = PlayerSetupFunc

	qmenu.Menu_AddItem(s_multiplayer_menu, s_join_network_server_action)
	qmenu.Menu_AddItem(s_multiplayer_menu, s_start_network_server_action)
	qmenu.Menu_AddItem(s_multiplayer_menu, s_player_setup_action)

	qmenu.Menu_SetStatusBar(s_multiplayer_menu, None)
	qmenu.Menu_Center(s_multiplayer_menu)


def Multiplayer_MenuKey(key): #int (returns const char *)

	return Default_MenuKey(s_multiplayer_menu, key)


def M_Menu_Multiplayer_f():

	Multiplayer_MenuInit()
	M_PushMenu(Multiplayer_MenuDraw, Multiplayer_MenuKey)

"""
=======================================================================

KEYS MENU

=======================================================================
*/
char *bindnames[][2] =
{
{"+attack", 		"attack"},
{"weapnext", 		"next weapon"},
{"+forward", 		"walk forward"},
{"+back", 			"backpedal"},
{"+left", 			"turn left"},
{"+right", 			"turn right"},
{"+speed", 			"run"},
{"+moveleft", 		"step left"},
{"+moveright", 		"step right"},
{"+strafe", 		"sidestep"},
{"+lookup", 		"look up"},
{"+lookdown", 		"look down"},
{"centerview", 		"center view"},
{"+mlook", 			"mouse look"},
{"+klook", 			"keyboard look"},
{"+moveup",			"up / jump"},
{"+movedown",		"down / crouch"},

{"inven",			"inventory"},
{"invuse",			"use item"},
{"invdrop",			"drop item"},
{"invprev",			"prev item"},
{"invnext",			"next item"},

{"cmd help", 		"help computer" }, 
{ 0, 0 }
};

int				keys_cursor;
static int		bind_grab;

static menuframework_s	s_keys_menu;
static menuaction_s		s_keys_attack_action;
static menuaction_s		s_keys_change_weapon_action;
static menuaction_s		s_keys_walk_forward_action;
static menuaction_s		s_keys_backpedal_action;
static menuaction_s		s_keys_turn_left_action;
static menuaction_s		s_keys_turn_right_action;
static menuaction_s		s_keys_run_action;
static menuaction_s		s_keys_step_left_action;
static menuaction_s		s_keys_step_right_action;
static menuaction_s		s_keys_sidestep_action;
static menuaction_s		s_keys_look_up_action;
static menuaction_s		s_keys_look_down_action;
static menuaction_s		s_keys_center_view_action;
static menuaction_s		s_keys_mouse_look_action;
static menuaction_s		s_keys_keyboard_look_action;
static menuaction_s		s_keys_move_up_action;
static menuaction_s		s_keys_move_down_action;
static menuaction_s		s_keys_inventory_action;
static menuaction_s		s_keys_inv_use_action;
static menuaction_s		s_keys_inv_drop_action;
static menuaction_s		s_keys_inv_prev_action;
static menuaction_s		s_keys_inv_next_action;

static menuaction_s		s_keys_help_computer_action;

static void M_UnbindCommand (char *command)
{
	int		j;
	int		l;
	char	*b;

	l = strlen(command);

	for (j=0 ; j<256 ; j++)
	{
		b = keybindings[j];
		if (!b)
			continue;
		if (!strncmp (b, command, l) )
			Key_SetBinding (j, "");
	}
}

static void M_FindKeysForCommand (char *command, int *twokeys)
{
	int		count;
	int		j;
	int		l;
	char	*b;

	twokeys[0] = twokeys[1] = -1;
	l = strlen(command);
	count = 0;

	for (j=0 ; j<256 ; j++)
	{
		b = keybindings[j];
		if (!b)
			continue;
		if (!strncmp (b, command, l) )
		{
			twokeys[count] = j;
			count++;
			if (count == 2)
				break;
		}
	}
}

static void KeyCursorDrawFunc( menuframework_s *menu )
{
	if ( bind_grab )
		vid_so.re.DrawChar( menu->x, menu->y + menu->cursor * 9, '=' );
	else
		vid_so.re.DrawChar( menu->x, menu->y + menu->cursor * 9, 12 + ( ( int ) ( Sys_Milliseconds() / 250 ) & 1 ) );
}

static void DrawKeyBindingFunc( void *self )
{
	int keys[2];
	menuaction_s *a = ( menuaction_s * ) self;

	M_FindKeysForCommand( bindnames[a->localdata[0]][0], keys);
		
	if (keys[0] == -1)
	{
		qmenu.Menu_DrawString( a->x + a->parent->x + 16, a->y + a->parent->y, "???" );
	}
	else
	{
		int x;
		const char *name;

		name = Key_KeynumToString (keys[0]);

		qmenu.Menu_DrawString( a->x + a->parent->x + 16, a->y + a->parent->y, name );

		x = strlen(name) * 8;

		if (keys[1] != -1)
		{
			qmenu.Menu_DrawString( a->x + a->parent->x + 24 + x, a->y + a->parent->y, "or" );
			qmenu.Menu_DrawString( a->x + a->parent->x + 48 + x, a->y + a->parent->y, Key_KeynumToString (keys[1]) );
		}
	}
}

static void KeyBindingFunc( void *self )
{
	menuaction_s *a = ( menuaction_s * ) self;
	int keys[2];

	M_FindKeysForCommand( bindnames[a->localdata[0]][0], keys );

	if (keys[1] != -1)
		M_UnbindCommand( bindnames[a->localdata[0]][0]);

	bind_grab = true;

	Menu_SetStatusBar( s_keys_menu, "press a key or button for this action" );
}

static void Keys_MenuInit( void )
{
	int y = 0;
	int i = 0;

	s_keys_menu.x = vid_so.viddef.width * 0.50;
	s_keys_menu.nitems = 0;
	s_keys_menu.cursordraw = KeyCursorDrawFunc;

	s_keys_attack_action.type	= MTYPE_ACTION;
	s_keys_attack_action.flags  = QMF_GRAYED;
	s_keys_attack_action.x		= 0;
	s_keys_attack_action.y		= y;
	s_keys_attack_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_attack_action.localdata[0] = i;
	s_keys_attack_action.name	= bindnames[s_keys_attack_action.localdata[0]][1];

	s_keys_change_weapon_action.type	= MTYPE_ACTION;
	s_keys_change_weapon_action.flags  = QMF_GRAYED;
	s_keys_change_weapon_action.x		= 0;
	s_keys_change_weapon_action.y		= y += 9;
	s_keys_change_weapon_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_change_weapon_action.localdata[0] = ++i;
	s_keys_change_weapon_action.name	= bindnames[s_keys_change_weapon_action.localdata[0]][1];

	s_keys_walk_forward_action.type	= MTYPE_ACTION;
	s_keys_walk_forward_action.flags  = QMF_GRAYED;
	s_keys_walk_forward_action.x		= 0;
	s_keys_walk_forward_action.y		= y += 9;
	s_keys_walk_forward_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_walk_forward_action.localdata[0] = ++i;
	s_keys_walk_forward_action.name	= bindnames[s_keys_walk_forward_action.localdata[0]][1];

	s_keys_backpedal_action.type	= MTYPE_ACTION;
	s_keys_backpedal_action.flags  = QMF_GRAYED;
	s_keys_backpedal_action.x		= 0;
	s_keys_backpedal_action.y		= y += 9;
	s_keys_backpedal_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_backpedal_action.localdata[0] = ++i;
	s_keys_backpedal_action.name	= bindnames[s_keys_backpedal_action.localdata[0]][1];

	s_keys_turn_left_action.type	= MTYPE_ACTION;
	s_keys_turn_left_action.flags  = QMF_GRAYED;
	s_keys_turn_left_action.x		= 0;
	s_keys_turn_left_action.y		= y += 9;
	s_keys_turn_left_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_turn_left_action.localdata[0] = ++i;
	s_keys_turn_left_action.name	= bindnames[s_keys_turn_left_action.localdata[0]][1];

	s_keys_turn_right_action.type	= MTYPE_ACTION;
	s_keys_turn_right_action.flags  = QMF_GRAYED;
	s_keys_turn_right_action.x		= 0;
	s_keys_turn_right_action.y		= y += 9;
	s_keys_turn_right_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_turn_right_action.localdata[0] = ++i;
	s_keys_turn_right_action.name	= bindnames[s_keys_turn_right_action.localdata[0]][1];

	s_keys_run_action.type	= MTYPE_ACTION;
	s_keys_run_action.flags  = QMF_GRAYED;
	s_keys_run_action.x		= 0;
	s_keys_run_action.y		= y += 9;
	s_keys_run_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_run_action.localdata[0] = ++i;
	s_keys_run_action.name	= bindnames[s_keys_run_action.localdata[0]][1];

	s_keys_step_left_action.type	= MTYPE_ACTION;
	s_keys_step_left_action.flags  = QMF_GRAYED;
	s_keys_step_left_action.x		= 0;
	s_keys_step_left_action.y		= y += 9;
	s_keys_step_left_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_step_left_action.localdata[0] = ++i;
	s_keys_step_left_action.name	= bindnames[s_keys_step_left_action.localdata[0]][1];

	s_keys_step_right_action.type	= MTYPE_ACTION;
	s_keys_step_right_action.flags  = QMF_GRAYED;
	s_keys_step_right_action.x		= 0;
	s_keys_step_right_action.y		= y += 9;
	s_keys_step_right_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_step_right_action.localdata[0] = ++i;
	s_keys_step_right_action.name	= bindnames[s_keys_step_right_action.localdata[0]][1];

	s_keys_sidestep_action.type	= MTYPE_ACTION;
	s_keys_sidestep_action.flags  = QMF_GRAYED;
	s_keys_sidestep_action.x		= 0;
	s_keys_sidestep_action.y		= y += 9;
	s_keys_sidestep_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_sidestep_action.localdata[0] = ++i;
	s_keys_sidestep_action.name	= bindnames[s_keys_sidestep_action.localdata[0]][1];

	s_keys_look_up_action.type	= MTYPE_ACTION;
	s_keys_look_up_action.flags  = QMF_GRAYED;
	s_keys_look_up_action.x		= 0;
	s_keys_look_up_action.y		= y += 9;
	s_keys_look_up_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_look_up_action.localdata[0] = ++i;
	s_keys_look_up_action.name	= bindnames[s_keys_look_up_action.localdata[0]][1];

	s_keys_look_down_action.type	= MTYPE_ACTION;
	s_keys_look_down_action.flags  = QMF_GRAYED;
	s_keys_look_down_action.x		= 0;
	s_keys_look_down_action.y		= y += 9;
	s_keys_look_down_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_look_down_action.localdata[0] = ++i;
	s_keys_look_down_action.name	= bindnames[s_keys_look_down_action.localdata[0]][1];

	s_keys_center_view_action.type	= MTYPE_ACTION;
	s_keys_center_view_action.flags  = QMF_GRAYED;
	s_keys_center_view_action.x		= 0;
	s_keys_center_view_action.y		= y += 9;
	s_keys_center_view_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_center_view_action.localdata[0] = ++i;
	s_keys_center_view_action.name	= bindnames[s_keys_center_view_action.localdata[0]][1];

	s_keys_mouse_look_action.type	= MTYPE_ACTION;
	s_keys_mouse_look_action.flags  = QMF_GRAYED;
	s_keys_mouse_look_action.x		= 0;
	s_keys_mouse_look_action.y		= y += 9;
	s_keys_mouse_look_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_mouse_look_action.localdata[0] = ++i;
	s_keys_mouse_look_action.name	= bindnames[s_keys_mouse_look_action.localdata[0]][1];

	s_keys_keyboard_look_action.type	= MTYPE_ACTION;
	s_keys_keyboard_look_action.flags  = QMF_GRAYED;
	s_keys_keyboard_look_action.x		= 0;
	s_keys_keyboard_look_action.y		= y += 9;
	s_keys_keyboard_look_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_keyboard_look_action.localdata[0] = ++i;
	s_keys_keyboard_look_action.name	= bindnames[s_keys_keyboard_look_action.localdata[0]][1];

	s_keys_move_up_action.type	= MTYPE_ACTION;
	s_keys_move_up_action.flags  = QMF_GRAYED;
	s_keys_move_up_action.x		= 0;
	s_keys_move_up_action.y		= y += 9;
	s_keys_move_up_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_move_up_action.localdata[0] = ++i;
	s_keys_move_up_action.name	= bindnames[s_keys_move_up_action.localdata[0]][1];

	s_keys_move_down_action.type	= MTYPE_ACTION;
	s_keys_move_down_action.flags  = QMF_GRAYED;
	s_keys_move_down_action.x		= 0;
	s_keys_move_down_action.y		= y += 9;
	s_keys_move_down_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_move_down_action.localdata[0] = ++i;
	s_keys_move_down_action.name	= bindnames[s_keys_move_down_action.localdata[0]][1];

	s_keys_inventory_action.type	= MTYPE_ACTION;
	s_keys_inventory_action.flags  = QMF_GRAYED;
	s_keys_inventory_action.x		= 0;
	s_keys_inventory_action.y		= y += 9;
	s_keys_inventory_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_inventory_action.localdata[0] = ++i;
	s_keys_inventory_action.name	= bindnames[s_keys_inventory_action.localdata[0]][1];

	s_keys_inv_use_action.type	= MTYPE_ACTION;
	s_keys_inv_use_action.flags  = QMF_GRAYED;
	s_keys_inv_use_action.x		= 0;
	s_keys_inv_use_action.y		= y += 9;
	s_keys_inv_use_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_inv_use_action.localdata[0] = ++i;
	s_keys_inv_use_action.name	= bindnames[s_keys_inv_use_action.localdata[0]][1];

	s_keys_inv_drop_action.type	= MTYPE_ACTION;
	s_keys_inv_drop_action.flags  = QMF_GRAYED;
	s_keys_inv_drop_action.x		= 0;
	s_keys_inv_drop_action.y		= y += 9;
	s_keys_inv_drop_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_inv_drop_action.localdata[0] = ++i;
	s_keys_inv_drop_action.name	= bindnames[s_keys_inv_drop_action.localdata[0]][1];

	s_keys_inv_prev_action.type	= MTYPE_ACTION;
	s_keys_inv_prev_action.flags  = QMF_GRAYED;
	s_keys_inv_prev_action.x		= 0;
	s_keys_inv_prev_action.y		= y += 9;
	s_keys_inv_prev_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_inv_prev_action.localdata[0] = ++i;
	s_keys_inv_prev_action.name	= bindnames[s_keys_inv_prev_action.localdata[0]][1];

	s_keys_inv_next_action.type	= MTYPE_ACTION;
	s_keys_inv_next_action.flags  = QMF_GRAYED;
	s_keys_inv_next_action.x		= 0;
	s_keys_inv_next_action.y		= y += 9;
	s_keys_inv_next_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_inv_next_action.localdata[0] = ++i;
	s_keys_inv_next_action.name	= bindnames[s_keys_inv_next_action.localdata[0]][1];

	s_keys_help_computer_action.type	= MTYPE_ACTION;
	s_keys_help_computer_action.flags  = QMF_GRAYED;
	s_keys_help_computer_action.x		= 0;
	s_keys_help_computer_action.y		= y += 9;
	s_keys_help_computer_action.ownerdraw = DrawKeyBindingFunc;
	s_keys_help_computer_action.localdata[0] = ++i;
	s_keys_help_computer_action.name	= bindnames[s_keys_help_computer_action.localdata[0]][1];

	qmenu.Menu_AddItem( s_keys_menu, s_keys_attack_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_change_weapon_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_walk_forward_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_backpedal_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_turn_left_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_turn_right_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_run_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_step_left_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_step_right_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_sidestep_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_look_up_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_look_down_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_center_view_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_mouse_look_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_keyboard_look_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_move_up_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_move_down_action );

	qmenu.Menu_AddItem( s_keys_menu, s_keys_inventory_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_inv_use_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_inv_drop_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_inv_prev_action );
	qmenu.Menu_AddItem( s_keys_menu, s_keys_inv_next_action );

	qmenu.Menu_AddItem( s_keys_menu, s_keys_help_computer_action );
	
	Menu_SetStatusBar( s_keys_menu, "enter to change, backspace to clear" );
	qmenu.Menu_Center( s_keys_menu );
}

static void Keys_MenuDraw (void)
{
	qmenu.Menu_AdjustCursor( s_keys_menu, 1 );
	qmenu.Menu_Draw( s_keys_menu );
}

static const char *Keys_MenuKey( int key )
{
	menuaction_s *item = ( menuaction_s * ) qmenu.Menu_ItemAtCursor( s_keys_menu );

	if ( bind_grab )
	{	
		if ( key != K_ESCAPE && key != '`' )
		{
			char cmd[1024];

			Com_sprintf (cmd, sizeof(cmd), "bind \"%s\" \"%s\"\n", Key_KeynumToString(key), bindnames[item->localdata[0]][0]);
			Cbuf_InsertText (cmd);
		}
		
		Menu_SetStatusBar( s_keys_menu, "enter to change, backspace to clear" );
		bind_grab = false;
		return menu_out_sound;
	}

	switch ( key )
	{
	case K_KP_ENTER:
	case K_ENTER:
		KeyBindingFunc( item );
		return menu_in_sound;
	case K_BACKSPACE:		// delete bindings
	case K_DEL:				// delete bindings
	case K_KP_DEL:
		M_UnbindCommand( bindnames[item->localdata[0]][0] );
		return menu_out_sound;
	default:
		return Default_MenuKey( s_keys_menu, key );
	}
}
"""
bindnames = [
	["+attack", "attack"],
	["weapnext", "next weapon"],
	["+forward", "walk forward"],
	["+back", "backpedal"],
	["+left", "turn left"],
	["+right", "turn right"],
	["+speed", "run"],
	["+moveleft", "step left"],
	["+moveright", "step right"],
	["+strafe", "sidestep"],
	["+lookup", "look up"],
	["+lookdown", "look down"],
	["centerview", "center view"],
	["+mlook", "mouse look"],
	["+klook", "keyboard look"],
	["+moveup", "up / jump"],
	["+movedown", "down / crouch"],
	["inven", "inventory"],
	["invuse", "use item"],
	["invdrop", "drop item"],
	["invprev", "prev item"],
	["invnext", "next item"],
	["cmd help", "help computer"],
]

keys_cursor = 0
bind_grab = False

s_keys_menu = menuframework_s()
s_keys_attack_action = menuaction_s()
s_keys_change_weapon_action = menuaction_s()
s_keys_walk_forward_action = menuaction_s()
s_keys_backpedal_action = menuaction_s()
s_keys_turn_left_action = menuaction_s()
s_keys_turn_right_action = menuaction_s()
s_keys_run_action = menuaction_s()
s_keys_step_left_action = menuaction_s()
s_keys_step_right_action = menuaction_s()
s_keys_sidestep_action = menuaction_s()
s_keys_look_up_action = menuaction_s()
s_keys_look_down_action = menuaction_s()
s_keys_center_view_action = menuaction_s()
s_keys_mouse_look_action = menuaction_s()
s_keys_keyboard_look_action = menuaction_s()
s_keys_move_up_action = menuaction_s()
s_keys_move_down_action = menuaction_s()
s_keys_inventory_action = menuaction_s()
s_keys_inv_use_action = menuaction_s()
s_keys_inv_drop_action = menuaction_s()
s_keys_inv_prev_action = menuaction_s()
s_keys_inv_next_action = menuaction_s()
s_keys_help_computer_action = menuaction_s()


def M_UnbindCommand(command):

	command_len = len(command)
	for j in range(256):
		binding = keys.keybindings[j]
		if binding is None:
			continue
		if binding[:command_len] == command:
			keys.Key_SetBinding(j, "")


def M_FindKeysForCommand(command, twokeys):

	count = 0
	command_len = len(command)
	twokeys[0] = -1
	twokeys[1] = -1

	for j in range(256):
		binding = keys.keybindings[j]
		if binding is None:
			continue
		if binding[:command_len] == command:
			twokeys[count] = j
			count += 1
			if count == 2:
				break


def KeyCursorDrawFunc(menu):

	if bind_grab:
		vid_so.re.DrawChar(menu.x, menu.y + menu.cursor * 9, ord("="))
	else:
		blink = int(q_shlinux.Sys_Milliseconds() / 250) & 1
		vid_so.re.DrawChar(menu.x, menu.y + menu.cursor * 9, 12 + blink)


def DrawKeyBindingFunc(self):

	keys_found = [-1, -1]
	M_FindKeysForCommand(bindnames[self.localdata[0]][0], keys_found)

	if keys_found[0] == -1:
		qmenu.Menu_DrawString(self.x + self.parent.x + 16, self.y + self.parent.y, "???")
		return

	name = keys.Key_KeynumToString(keys_found[0])
	qmenu.Menu_DrawString(self.x + self.parent.x + 16, self.y + self.parent.y, name)

	x = len(name) * 8
	if keys_found[1] != -1:
		qmenu.Menu_DrawString(self.x + self.parent.x + 24 + x, self.y + self.parent.y, "or")
		qmenu.Menu_DrawString(
			self.x + self.parent.x + 48 + x,
			self.y + self.parent.y,
			keys.Key_KeynumToString(keys_found[1]),
		)


def KeyBindingFunc(self):

	keys_found = [-1, -1]
	M_FindKeysForCommand(bindnames[self.localdata[0]][0], keys_found)

	if keys_found[1] != -1:
		M_UnbindCommand(bindnames[self.localdata[0]][0])

	global bind_grab
	bind_grab = True

	qmenu.Menu_SetStatusBar(s_keys_menu, "press a key or button for this action")


def Keys_MenuInit():

	y = 0
	i = 0

	s_keys_menu.x = vid_so.viddef.width * 0.50
	s_keys_menu.nitems = 0
	s_keys_menu.cursordraw = KeyCursorDrawFunc

	s_keys_attack_action.type = MTYPE_ACTION
	s_keys_attack_action.flags = QMF_GRAYED
	s_keys_attack_action.x = 0
	s_keys_attack_action.y = y
	s_keys_attack_action.ownerdraw = DrawKeyBindingFunc
	s_keys_attack_action.localdata[0] = i
	s_keys_attack_action.name = bindnames[s_keys_attack_action.localdata[0]][1]

	s_keys_change_weapon_action.type = MTYPE_ACTION
	s_keys_change_weapon_action.flags = QMF_GRAYED
	s_keys_change_weapon_action.x = 0
	s_keys_change_weapon_action.y = y + 9
	s_keys_change_weapon_action.ownerdraw = DrawKeyBindingFunc
	s_keys_change_weapon_action.localdata[0] = i + 1
	s_keys_change_weapon_action.name = bindnames[s_keys_change_weapon_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_walk_forward_action.type = MTYPE_ACTION
	s_keys_walk_forward_action.flags = QMF_GRAYED
	s_keys_walk_forward_action.x = 0
	s_keys_walk_forward_action.y = y + 9
	s_keys_walk_forward_action.ownerdraw = DrawKeyBindingFunc
	s_keys_walk_forward_action.localdata[0] = i + 1
	s_keys_walk_forward_action.name = bindnames[s_keys_walk_forward_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_backpedal_action.type = MTYPE_ACTION
	s_keys_backpedal_action.flags = QMF_GRAYED
	s_keys_backpedal_action.x = 0
	s_keys_backpedal_action.y = y + 9
	s_keys_backpedal_action.ownerdraw = DrawKeyBindingFunc
	s_keys_backpedal_action.localdata[0] = i + 1
	s_keys_backpedal_action.name = bindnames[s_keys_backpedal_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_turn_left_action.type = MTYPE_ACTION
	s_keys_turn_left_action.flags = QMF_GRAYED
	s_keys_turn_left_action.x = 0
	s_keys_turn_left_action.y = y + 9
	s_keys_turn_left_action.ownerdraw = DrawKeyBindingFunc
	s_keys_turn_left_action.localdata[0] = i + 1
	s_keys_turn_left_action.name = bindnames[s_keys_turn_left_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_turn_right_action.type = MTYPE_ACTION
	s_keys_turn_right_action.flags = QMF_GRAYED
	s_keys_turn_right_action.x = 0
	s_keys_turn_right_action.y = y + 9
	s_keys_turn_right_action.ownerdraw = DrawKeyBindingFunc
	s_keys_turn_right_action.localdata[0] = i + 1
	s_keys_turn_right_action.name = bindnames[s_keys_turn_right_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_run_action.type = MTYPE_ACTION
	s_keys_run_action.flags = QMF_GRAYED
	s_keys_run_action.x = 0
	s_keys_run_action.y = y + 9
	s_keys_run_action.ownerdraw = DrawKeyBindingFunc
	s_keys_run_action.localdata[0] = i + 1
	s_keys_run_action.name = bindnames[s_keys_run_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_step_left_action.type = MTYPE_ACTION
	s_keys_step_left_action.flags = QMF_GRAYED
	s_keys_step_left_action.x = 0
	s_keys_step_left_action.y = y + 9
	s_keys_step_left_action.ownerdraw = DrawKeyBindingFunc
	s_keys_step_left_action.localdata[0] = i + 1
	s_keys_step_left_action.name = bindnames[s_keys_step_left_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_step_right_action.type = MTYPE_ACTION
	s_keys_step_right_action.flags = QMF_GRAYED
	s_keys_step_right_action.x = 0
	s_keys_step_right_action.y = y + 9
	s_keys_step_right_action.ownerdraw = DrawKeyBindingFunc
	s_keys_step_right_action.localdata[0] = i + 1
	s_keys_step_right_action.name = bindnames[s_keys_step_right_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_sidestep_action.type = MTYPE_ACTION
	s_keys_sidestep_action.flags = QMF_GRAYED
	s_keys_sidestep_action.x = 0
	s_keys_sidestep_action.y = y + 9
	s_keys_sidestep_action.ownerdraw = DrawKeyBindingFunc
	s_keys_sidestep_action.localdata[0] = i + 1
	s_keys_sidestep_action.name = bindnames[s_keys_sidestep_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_look_up_action.type = MTYPE_ACTION
	s_keys_look_up_action.flags = QMF_GRAYED
	s_keys_look_up_action.x = 0
	s_keys_look_up_action.y = y + 9
	s_keys_look_up_action.ownerdraw = DrawKeyBindingFunc
	s_keys_look_up_action.localdata[0] = i + 1
	s_keys_look_up_action.name = bindnames[s_keys_look_up_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_look_down_action.type = MTYPE_ACTION
	s_keys_look_down_action.flags = QMF_GRAYED
	s_keys_look_down_action.x = 0
	s_keys_look_down_action.y = y + 9
	s_keys_look_down_action.ownerdraw = DrawKeyBindingFunc
	s_keys_look_down_action.localdata[0] = i + 1
	s_keys_look_down_action.name = bindnames[s_keys_look_down_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_center_view_action.type = MTYPE_ACTION
	s_keys_center_view_action.flags = QMF_GRAYED
	s_keys_center_view_action.x = 0
	s_keys_center_view_action.y = y + 9
	s_keys_center_view_action.ownerdraw = DrawKeyBindingFunc
	s_keys_center_view_action.localdata[0] = i + 1
	s_keys_center_view_action.name = bindnames[s_keys_center_view_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_mouse_look_action.type = MTYPE_ACTION
	s_keys_mouse_look_action.flags = QMF_GRAYED
	s_keys_mouse_look_action.x = 0
	s_keys_mouse_look_action.y = y + 9
	s_keys_mouse_look_action.ownerdraw = DrawKeyBindingFunc
	s_keys_mouse_look_action.localdata[0] = i + 1
	s_keys_mouse_look_action.name = bindnames[s_keys_mouse_look_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_keyboard_look_action.type = MTYPE_ACTION
	s_keys_keyboard_look_action.flags = QMF_GRAYED
	s_keys_keyboard_look_action.x = 0
	s_keys_keyboard_look_action.y = y + 9
	s_keys_keyboard_look_action.ownerdraw = DrawKeyBindingFunc
	s_keys_keyboard_look_action.localdata[0] = i + 1
	s_keys_keyboard_look_action.name = bindnames[s_keys_keyboard_look_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_move_up_action.type = MTYPE_ACTION
	s_keys_move_up_action.flags = QMF_GRAYED
	s_keys_move_up_action.x = 0
	s_keys_move_up_action.y = y + 9
	s_keys_move_up_action.ownerdraw = DrawKeyBindingFunc
	s_keys_move_up_action.localdata[0] = i + 1
	s_keys_move_up_action.name = bindnames[s_keys_move_up_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_move_down_action.type = MTYPE_ACTION
	s_keys_move_down_action.flags = QMF_GRAYED
	s_keys_move_down_action.x = 0
	s_keys_move_down_action.y = y + 9
	s_keys_move_down_action.ownerdraw = DrawKeyBindingFunc
	s_keys_move_down_action.localdata[0] = i + 1
	s_keys_move_down_action.name = bindnames[s_keys_move_down_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_inventory_action.type = MTYPE_ACTION
	s_keys_inventory_action.flags = QMF_GRAYED
	s_keys_inventory_action.x = 0
	s_keys_inventory_action.y = y + 9
	s_keys_inventory_action.ownerdraw = DrawKeyBindingFunc
	s_keys_inventory_action.localdata[0] = i + 1
	s_keys_inventory_action.name = bindnames[s_keys_inventory_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_inv_use_action.type = MTYPE_ACTION
	s_keys_inv_use_action.flags = QMF_GRAYED
	s_keys_inv_use_action.x = 0
	s_keys_inv_use_action.y = y + 9
	s_keys_inv_use_action.ownerdraw = DrawKeyBindingFunc
	s_keys_inv_use_action.localdata[0] = i + 1
	s_keys_inv_use_action.name = bindnames[s_keys_inv_use_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_inv_drop_action.type = MTYPE_ACTION
	s_keys_inv_drop_action.flags = QMF_GRAYED
	s_keys_inv_drop_action.x = 0
	s_keys_inv_drop_action.y = y + 9
	s_keys_inv_drop_action.ownerdraw = DrawKeyBindingFunc
	s_keys_inv_drop_action.localdata[0] = i + 1
	s_keys_inv_drop_action.name = bindnames[s_keys_inv_drop_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_inv_prev_action.type = MTYPE_ACTION
	s_keys_inv_prev_action.flags = QMF_GRAYED
	s_keys_inv_prev_action.x = 0
	s_keys_inv_prev_action.y = y + 9
	s_keys_inv_prev_action.ownerdraw = DrawKeyBindingFunc
	s_keys_inv_prev_action.localdata[0] = i + 1
	s_keys_inv_prev_action.name = bindnames[s_keys_inv_prev_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_inv_next_action.type = MTYPE_ACTION
	s_keys_inv_next_action.flags = QMF_GRAYED
	s_keys_inv_next_action.x = 0
	s_keys_inv_next_action.y = y + 9
	s_keys_inv_next_action.ownerdraw = DrawKeyBindingFunc
	s_keys_inv_next_action.localdata[0] = i + 1
	s_keys_inv_next_action.name = bindnames[s_keys_inv_next_action.localdata[0]][1]

	y += 9
	i += 1

	s_keys_help_computer_action.type = MTYPE_ACTION
	s_keys_help_computer_action.flags = QMF_GRAYED
	s_keys_help_computer_action.x = 0
	s_keys_help_computer_action.y = y + 9
	s_keys_help_computer_action.ownerdraw = DrawKeyBindingFunc
	s_keys_help_computer_action.localdata[0] = i + 1
	s_keys_help_computer_action.name = bindnames[s_keys_help_computer_action.localdata[0]][1]

	qmenu.Menu_AddItem(s_keys_menu, s_keys_attack_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_change_weapon_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_walk_forward_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_backpedal_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_turn_left_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_turn_right_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_run_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_step_left_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_step_right_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_sidestep_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_look_up_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_look_down_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_center_view_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_mouse_look_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_keyboard_look_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_move_up_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_move_down_action)

	qmenu.Menu_AddItem(s_keys_menu, s_keys_inventory_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_inv_use_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_inv_drop_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_inv_prev_action)
	qmenu.Menu_AddItem(s_keys_menu, s_keys_inv_next_action)

	qmenu.Menu_AddItem(s_keys_menu, s_keys_help_computer_action)

	qmenu.Menu_SetStatusBar(s_keys_menu, "enter to change, backspace to clear")
	qmenu.Menu_Center(s_keys_menu)


def Keys_MenuDraw():

	qmenu.Menu_AdjustCursor(s_keys_menu, 1)
	qmenu.Menu_Draw(s_keys_menu)


def Keys_MenuKey(key): #int (returns const char *)

	global bind_grab

	item = qmenu.Menu_ItemAtCursor(s_keys_menu)

	if bind_grab:
		if key not in (keys.K_ESCAPE, ord("`")):
			cmd.Cbuf_InsertText(
				"bind \"{}\" \"{}\"\n".format(
					keys.Key_KeynumToString(key),
					bindnames[item.localdata[0]][0],
				)
			)

		qmenu.Menu_SetStatusBar(s_keys_menu, "enter to change, backspace to clear")
		bind_grab = False
		return menu_out_sound

	if key in (keys.K_KP_ENTER, keys.K_ENTER):
		KeyBindingFunc(item)
		return menu_in_sound
	if key in (keys.K_BACKSPACE, keys.K_DEL, keys.K_KP_DEL):
		M_UnbindCommand(bindnames[item.localdata[0]][0])
		return menu_out_sound

	return Default_MenuKey(s_keys_menu, key)


def M_Menu_Keys_f ():

	Keys_MenuInit()
	M_PushMenu(Keys_MenuDraw, Keys_MenuKey)



"""
=======================================================================

CONTROLS MENU

=======================================================================
"""
win_noalttab = None #static cvar_t *

s_options_menu = menuframework_s()
s_options_defaults_action = menuaction_s()
s_options_customize_options_action = menuaction_s()
s_options_sensitivity_slider = menuslider_s()
s_options_freelook_box = menuspincontrol_s()
s_options_noalttab_box = menuspincontrol_s()
s_options_alwaysrun_box = menuspincontrol_s()
s_options_invertmouse_box = menuspincontrol_s()
s_options_lookspring_box = menuspincontrol_s()
s_options_lookstrafe_box = menuspincontrol_s()
s_options_crosshair_box = menuspincontrol_s()
s_options_sfxvolume_slider = menuslider_s()
s_options_joystick_box = menuspincontrol_s()
s_options_cdvolume_box = menuspincontrol_s()
s_options_quality_list = menuspincontrol_s()
s_options_compatibility_list = menuspincontrol_s()
s_options_console_action = menuspincontrol_s()


def CrosshairFunc( unused ):

	cvar.Cvar_SetValue( "crosshair", s_options_crosshair_box.curvalue )


def JoystickFunc( unused ):

	cvar.Cvar_SetValue( "in_joystick", s_options_joystick_box.curvalue )


def CustomizeControlsFunc( unused ):

	M_Menu_Keys_f()


def AlwaysRunFunc( unused ):

	cvar.Cvar_SetValue( "cl_run", s_options_alwaysrun_box.curvalue )


def FreeLookFunc( unused ):

	cvar.Cvar_SetValue( "freelook", s_options_freelook_box.curvalue )


def MouseSpeedFunc( unused ):

	cvar.Cvar_SetValue( "sensitivity", s_options_sensitivity_slider.curvalue / 2.0 )


def NoAltTabFunc( unused ):

	cvar.Cvar_SetValue( "win_noalttab", s_options_noalttab_box.curvalue )


def ClampCvar( minIn, maxIn, value ): #float, float, float (returns float)

	if value < minIn: return minIn
	if value > maxIn: return maxIn
	return value


def ControlsSetMenuItemValues( ):

	s_options_sfxvolume_slider.curvalue		= int(cvar.Cvar_VariableValue( "s_volume" ) * 10)
	s_options_cdvolume_box.curvalue 		= cvar.Cvar_VariableValue("cd_nocd") != 0.0
	s_options_quality_list.curvalue			= cvar.Cvar_VariableValue( "s_loadas8bit" ) != 0.0
	s_options_sensitivity_slider.curvalue	= int (( cl_main.sensitivity.value ) * 2)

	cvar.Cvar_SetValue( "cl_run", ClampCvar( 0, 1, cl_main.cl_run.value ) )
	s_options_alwaysrun_box.curvalue		= int(cl_main.cl_run.value)

	s_options_invertmouse_box.curvalue		= int(cl_main.m_pitch.value < 0)

	cvar.Cvar_SetValue( "lookspring", ClampCvar( 0, 1, cl_main.lookspring.value ) )
	s_options_lookspring_box.curvalue		= int(cl_main.lookspring.value)

	cvar.Cvar_SetValue( "lookstrafe", ClampCvar( 0, 1, cl_main.lookstrafe.value ) )
	s_options_lookstrafe_box.curvalue		= int(cl_main.lookstrafe.value)

	cvar.Cvar_SetValue( "freelook", ClampCvar( 0, 1, cl_main.freelook.value ) )
	s_options_freelook_box.curvalue			= int(cl_main.freelook.value)

	cvar.Cvar_SetValue( "crosshair", ClampCvar( 0, 3, cl_view.crosshair.value ) )
	s_options_crosshair_box.curvalue		= int(cl_view.crosshair.value)

	cvar.Cvar_SetValue( "in_joystick", ClampCvar( 0, 1, in_linux.in_joystick.value ) )
	s_options_joystick_box.curvalue		= int(in_linux.in_joystick.value)

	if win_noalttab is not None:
		s_options_noalttab_box.curvalue			= int(win_noalttab.value)


def ControlsResetDefaultsFunc( unused ):

	cmd.Cbuf_AddText ("exec default.cfg\n")
	cmd.Cbuf_Execute()

	ControlsSetMenuItemValues()

def InvertMouseFunc( unused ):

	cvar.Cvar_SetValue( "m_pitch", -cl_main.m_pitch.value )


def LookspringFunc( unused ):

	cvar.Cvar_SetValue( "lookspring", cl_main.lookspring.value != 0.0 )


def LookstrafeFunc( unused ):

	cvar.Cvar_SetValue( "lookstrafe", cl_main.lookstrafe.value != 0.0 )


def UpdateVolumeFunc( unused ):

	cvar.Cvar_SetValue( "s_volume", s_options_sfxvolume_slider.curvalue // 10 )


def UpdateCDVolumeFunc( unused ):

	cvar.Cvar_SetValue( "cd_nocd", not s_options_cdvolume_box.curvalue )


def ConsoleFunc( unused ):

	#
	# the proper way to do this is probably to have ToggleConsole_f accept a parameter
	#
	#extern void Key_ClearTyping( void )

	if cl_main.cl.attractloop :
	
		cmd.Cbuf_AddText ("killserver\n")
		return
	
	console.Key_ClearTyping ()
	console.Con_ClearNotify ()

	M_ForceMenuOff ()
	cl_main.cls.key_dest = client.keydest_t.key_console


def UpdateSoundQualityFunc( unused ):

	if s_options_quality_list.curvalue:
	
		cvar.Cvar_SetValue( "s_khz", 22 )
		cvar.Cvar_SetValue( "s_loadas8bit", False )
	
	else:
	
		cvar.Cvar_SetValue( "s_khz", 11 )
		cvar.Cvar_SetValue( "s_loadas8bit", True )
	
	
	cvar.Cvar_SetValue( "s_primary", s_options_compatibility_list.curvalue )

	M_DrawTextBox( 8, 120 - 48, 36, 3 );
	M_Print( 16 + 16, 120 - 48 + 8,  "Restarting the sound system. This" )
	M_Print( 16 + 16, 120 - 48 + 16, "could take up to a minute, so" )
	M_Print( 16 + 16, 120 - 48 + 24, "please be patient." )

	# the text box won't show up unless we do a buffer swap
	vid_so.re.EndFrame()

	snd_dma.CL_Snd_Restart_f()


def Options_MenuInit( ):

	cd_music_items = [
		"disabled",
		"enabled",
	] #static const char *

	quality_items = [
		"low", "high",
	] #static const char *

	compatibility_items = [
		"max compatibility", "max performance",
	] #static const char *

	yesno_names = [
		"no",
		"yes",
	] #static const char *

	crosshair_names = [
		"none",
		"cross",
		"dot",
		"angle",
	] #static const char *

	win_noalttab = cvar.Cvar_Get( "win_noalttab", "0", q_shared.CVAR_ARCHIVE )

	#
	# configure controls menu and menu items
	#
	s_options_menu.x = vid_so.viddef.width // 2
	s_options_menu.y = vid_so.viddef.height // 2 - 58
	s_options_menu.nitems = 0

	s_options_sfxvolume_slider.x	= 0
	s_options_sfxvolume_slider.y	= 0
	s_options_sfxvolume_slider.name	= "effects volume"
	s_options_sfxvolume_slider.callback	= UpdateVolumeFunc
	s_options_sfxvolume_slider.minvalue		= 0
	s_options_sfxvolume_slider.maxvalue		= 10
	s_options_sfxvolume_slider.curvalue		= int(cvar.Cvar_VariableValue( "s_volume" ) * 10)

	s_options_cdvolume_box.x		= 0
	s_options_cdvolume_box.y		= 10
	s_options_cdvolume_box.name	= "CD music"
	s_options_cdvolume_box.callback	= UpdateCDVolumeFunc
	s_options_cdvolume_box.itemnames		= cd_music_items
	s_options_cdvolume_box.curvalue 		= cvar.Cvar_VariableValue("cd_nocd") != 0

	s_options_quality_list.x		= 0
	s_options_quality_list.y		= 20
	s_options_quality_list.name		= "sound quality"
	s_options_quality_list.callback = UpdateSoundQualityFunc
	s_options_quality_list.itemnames		= quality_items
	s_options_quality_list.curvalue			= cvar.Cvar_VariableValue( "s_loadas8bit" ) != 0

	s_options_compatibility_list.x		= 0
	s_options_compatibility_list.y		= 30
	s_options_compatibility_list.name	= "sound compatibility"
	s_options_compatibility_list.callback = UpdateSoundQualityFunc
	s_options_compatibility_list.itemnames		= compatibility_items
	s_options_compatibility_list.curvalue		= int(cvar.Cvar_VariableValue( "s_primary" ))

	s_options_sensitivity_slider.x		= 0
	s_options_sensitivity_slider.y		= 50
	s_options_sensitivity_slider.name	= "mouse speed"
	s_options_sensitivity_slider.callback = MouseSpeedFunc
	s_options_sensitivity_slider.minvalue		= 2
	s_options_sensitivity_slider.maxvalue		= 22

	s_options_alwaysrun_box.x	= 0
	s_options_alwaysrun_box.y	= 60
	s_options_alwaysrun_box.name	= "always run"
	s_options_alwaysrun_box.callback = AlwaysRunFunc
	s_options_alwaysrun_box.itemnames = yesno_names

	s_options_invertmouse_box.x	= 0
	s_options_invertmouse_box.y	= 70
	s_options_invertmouse_box.name	= "invert mouse"
	s_options_invertmouse_box.callback = InvertMouseFunc
	s_options_invertmouse_box.itemnames = yesno_names

	s_options_lookspring_box.x	= 0
	s_options_lookspring_box.y	= 80
	s_options_lookspring_box.name	= "lookspring"
	s_options_lookspring_box.callback = LookspringFunc
	s_options_lookspring_box.itemnames = yesno_names

	s_options_lookstrafe_box.x	= 0
	s_options_lookstrafe_box.y	= 90
	s_options_lookstrafe_box.name	= "lookstrafe"
	s_options_lookstrafe_box.callback = LookstrafeFunc
	s_options_lookstrafe_box.itemnames = yesno_names

	s_options_freelook_box.x	= 0
	s_options_freelook_box.y	= 100
	s_options_freelook_box.name	= "free look"
	s_options_freelook_box.callback = FreeLookFunc
	s_options_freelook_box.itemnames = yesno_names

	s_options_crosshair_box.x	= 0
	s_options_crosshair_box.y	= 110
	s_options_crosshair_box.name	= "crosshair"
	s_options_crosshair_box.callback = CrosshairFunc
	s_options_crosshair_box.itemnames = crosshair_names

	##s_options_noalttab_box.x	= 0;
	##s_options_noalttab_box.y	= 110;
	##s_options_noalttab_box.name	= "disable alt-tab";
	##s_options_noalttab_box.callback = NoAltTabFunc;
	##s_options_noalttab_box.itemnames = yesno_names;

	s_options_joystick_box.x	= 0
	s_options_joystick_box.y	= 120
	s_options_joystick_box.name	= "use joystick"
	s_options_joystick_box.callback = JoystickFunc
	s_options_joystick_box.itemnames = yesno_names

	s_options_customize_options_action.x		= 0
	s_options_customize_options_action.y		= 140
	s_options_customize_options_action.name	= "customize controls"
	s_options_customize_options_action.callback = CustomizeControlsFunc

	s_options_defaults_action.x		= 0
	s_options_defaults_action.y		= 150
	s_options_defaults_action.name	= "reset defaults"
	s_options_defaults_action.callback = ControlsResetDefaultsFunc

	s_options_console_action.x		= 0
	s_options_console_action.y		= 160
	s_options_console_action.name	= "go to console"
	s_options_console_action.callback = ConsoleFunc

	ControlsSetMenuItemValues()

	qmenu.Menu_AddItem( s_options_menu, s_options_sfxvolume_slider )
	qmenu.Menu_AddItem( s_options_menu, s_options_cdvolume_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_quality_list )
	qmenu.Menu_AddItem( s_options_menu, s_options_compatibility_list )
	qmenu.Menu_AddItem( s_options_menu, s_options_sensitivity_slider )
	qmenu.Menu_AddItem( s_options_menu, s_options_alwaysrun_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_invertmouse_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_lookspring_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_lookstrafe_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_freelook_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_crosshair_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_joystick_box )
	qmenu.Menu_AddItem( s_options_menu, s_options_customize_options_action )
	qmenu.Menu_AddItem( s_options_menu, s_options_defaults_action )
	qmenu.Menu_AddItem( s_options_menu, s_options_console_action )


def Options_MenuDraw ():

	M_Banner( "m_banner_options" )
	qmenu.Menu_AdjustCursor( s_options_menu, 1 )
	qmenu.Menu_Draw( s_options_menu )

def Options_MenuKey( key ):

	return Default_MenuKey( s_options_menu, key )


def M_Menu_Options_f ():

	Options_MenuInit()
	M_PushMenu ( Options_MenuDraw, Options_MenuKey )


"""
=======================================================================

VIDEO MENU

=======================================================================
"""


def M_Menu_Video_f ():

	if "VID_MenuInit" not in globals():
		common.Com_Printf("VID menu not available.\n")
		return

	VID_MenuInit()
	M_PushMenu(VID_MenuDraw, VID_MenuKey)


"""
=============================================================================

END GAME MENU

=============================================================================
*/
static int credits_start_time;
static const char **credits;
static char *creditsIndex[256];
static char *creditsBuffer;
static const char *idcredits[] =
{
	"+QUAKE II BY ID SOFTWARE",
	"",
	"+PROGRAMMING",
	"John Carmack",
	"John Cash",
	"Brian Hook",
	"",
	"+ART",
	"Adrian Carmack",
	"Kevin Cloud",
	"Paul Steed",
	"",
	"+LEVEL DESIGN",
	"Tim Willits",
	"American McGee",
	"Christian Antkow",
	"Paul Jaquays",
	"Brandon James",
	"",
	"+BIZ",
	"Todd Hollenshead",
	"Barrett (Bear) Alexander",
	"Donna Jackson",
	"",
	"",
	"+SPECIAL THANKS",
	"Ben Donges for beta testing",
	"",
	"",
	"",
	"",
	"",
	"",
	"+ADDITIONAL SUPPORT",
	"",
	"+LINUX PORT AND CTF",
	"Dave \"Zoid\" Kirsch",
	"",
	"+CINEMATIC SEQUENCES",
	"Ending Cinematic by Blur Studio - ",
	"Venice, CA",
	"",
	"Environment models for Introduction",
	"Cinematic by Karl Dolgener",
	"",
	"Assistance with environment design",
	"by Cliff Iwai",
	"",
	"+SOUND EFFECTS AND MUSIC",
	"Sound Design by Soundelux Media Labs.",
	"Music Composed and Produced by",
	"Soundelux Media Labs.  Special thanks",
	"to Bill Brown, Tom Ozanich, Brian",
	"Celano, Jeff Eisner, and The Soundelux",
	"Players.",
	"",
	"\"Level Music\" by Sonic Mayhem",
	"www.sonicmayhem.com",
	"",
	"\"Quake II Theme Song\"",
	"(C) 1997 Rob Zombie. All Rights",
	"Reserved.",
	"",
	"Track 10 (\"Climb\") by Jer Sypult",
	"",
	"Voice of computers by",
	"Carly Staehlin-Taylor",
	"",
	"+THANKS TO ACTIVISION",
	"+IN PARTICULAR:",
	"",
	"John Tam",
	"Steve Rosenthal",
	"Marty Stratton",
	"Henk Hartong",
	"",
	"Quake II(tm) (C)1997 Id Software, Inc.",
	"All Rights Reserved.  Distributed by",
	"Activision, Inc. under license.",
	"Quake II(tm), the Id Software name,",
	"the \"Q II\"(tm) logo and id(tm)",
	"logo are trademarks of Id Software,",
	"Inc. Activision(R) is a registered",
	"trademark of Activision, Inc. All",
	"other trademarks and trade names are",
	"properties of their respective owners.",
	0
};

static const char *xatcredits[] =
{
	"+QUAKE II MISSION PACK: THE RECKONING",
	"+BY",
	"+XATRIX ENTERTAINMENT, INC.",
	"",
	"+DESIGN AND DIRECTION",
	"Drew Markham",
	"",
	"+PRODUCED BY",
	"Greg Goodrich",
	"",
	"+PROGRAMMING",
	"Rafael Paiz",
	"",
	"+LEVEL DESIGN / ADDITIONAL GAME DESIGN",
	"Alex Mayberry",
	"",
	"+LEVEL DESIGN",
	"Mal Blackwell",
	"Dan Koppel",
	"",
	"+ART DIRECTION",
	"Michael \"Maxx\" Kaufman",
	"",
	"+COMPUTER GRAPHICS SUPERVISOR AND",
	"+CHARACTER ANIMATION DIRECTION",
	"Barry Dempsey",
	"",
	"+SENIOR ANIMATOR AND MODELER",
	"Jason Hoover",
	"",
	"+CHARACTER ANIMATION AND",
	"+MOTION CAPTURE SPECIALIST",
	"Amit Doron",
	"",
	"+ART",
	"Claire Praderie-Markham",
	"Viktor Antonov",
	"Corky Lehmkuhl",
	"",
	"+INTRODUCTION ANIMATION",
	"Dominique Drozdz",
	"",
	"+ADDITIONAL LEVEL DESIGN",
	"Aaron Barber",
	"Rhett Baldwin",
	"",
	"+3D CHARACTER ANIMATION TOOLS",
	"Gerry Tyra, SA Technology",
	"",
	"+ADDITIONAL EDITOR TOOL PROGRAMMING",
	"Robert Duffy",
	"",
	"+ADDITIONAL PROGRAMMING",
	"Ryan Feltrin",
	"",
	"+PRODUCTION COORDINATOR",
	"Victoria Sylvester",
	"",
	"+SOUND DESIGN",
	"Gary Bradfield",
	"",
	"+MUSIC BY",
	"Sonic Mayhem",
	"",
	"",
	"",
	"+SPECIAL THANKS",
	"+TO",
	"+OUR FRIENDS AT ID SOFTWARE",
	"",
	"John Carmack",
	"John Cash",
	"Brian Hook",
	"Adrian Carmack",
	"Kevin Cloud",
	"Paul Steed",
	"Tim Willits",
	"Christian Antkow",
	"Paul Jaquays",
	"Brandon James",
	"Todd Hollenshead",
	"Barrett (Bear) Alexander",
	"Dave \"Zoid\" Kirsch",
	"Donna Jackson",
	"",
	"",
	"",
	"+THANKS TO ACTIVISION",
	"+IN PARTICULAR:",
	"",
	"Marty Stratton",
	"Henk \"The Original Ripper\" Hartong",
	"Kevin Kraff",
	"Jamey Gottlieb",
	"Chris Hepburn",
	"",
	"+AND THE GAME TESTERS",
	"",
	"Tim Vanlaw",
	"Doug Jacobs",
	"Steven Rosenthal",
	"David Baker",
	"Chris Campbell",
	"Aaron Casillas",
	"Steve Elwell",
	"Derek Johnstone",
	"Igor Krinitskiy",
	"Samantha Lee",
	"Michael Spann",
	"Chris Toft",
	"Juan Valdes",
	"",
	"+THANKS TO INTERGRAPH COMPUTER SYTEMS",
	"+IN PARTICULAR:",
	"",
	"Michael T. Nicolaou",
	"",
	"",
	"Quake II Mission Pack: The Reckoning",
	"(tm) (C)1998 Id Software, Inc. All",
	"Rights Reserved. Developed by Xatrix",
	"Entertainment, Inc. for Id Software,",
	"Inc. Distributed by Activision Inc.",
	"under license. Quake(R) is a",
	"registered trademark of Id Software,",
	"Inc. Quake II Mission Pack: The",
	"Reckoning(tm), Quake II(tm), the Id",
	"Software name, the \"Q II\"(tm) logo",
	"and id(tm) logo are trademarks of Id",
	"Software, Inc. Activision(R) is a",
	"registered trademark of Activision,",
	"Inc. Xatrix(R) is a registered",
	"trademark of Xatrix Entertainment,",
	"Inc. All other trademarks and trade",
	"names are properties of their",
	"respective owners.",
	0
};

static const char *roguecredits[] =
{
	"+QUAKE II MISSION PACK 2: GROUND ZERO",
	"+BY",
	"+ROGUE ENTERTAINMENT, INC.",
	"",
	"+PRODUCED BY",
	"Jim Molinets",
	"",
	"+PROGRAMMING",
	"Peter Mack",
	"Patrick Magruder",
	"",
	"+LEVEL DESIGN",
	"Jim Molinets",
	"Cameron Lamprecht",
	"Berenger Fish",
	"Robert Selitto",
	"Steve Tietze",
	"Steve Thoms",
	"",
	"+ART DIRECTION",
	"Rich Fleider",
	"",
	"+ART",
	"Rich Fleider",
	"Steve Maines",
	"Won Choi",
	"",
	"+ANIMATION SEQUENCES",
	"Creat Studios",
	"Steve Maines",
	"",
	"+ADDITIONAL LEVEL DESIGN",
	"Rich Fleider",
	"Steve Maines",
	"Peter Mack",
	"",
	"+SOUND",
	"James Grunke",
	"",
	"+GROUND ZERO THEME",
	"+AND",
	"+MUSIC BY",
	"Sonic Mayhem",
	"",
	"+VWEP MODELS",
	"Brent \"Hentai\" Dill",
	"",
	"",
	"",
	"+SPECIAL THANKS",
	"+TO",
	"+OUR FRIENDS AT ID SOFTWARE",
	"",
	"John Carmack",
	"John Cash",
	"Brian Hook",
	"Adrian Carmack",
	"Kevin Cloud",
	"Paul Steed",
	"Tim Willits",
	"Christian Antkow",
	"Paul Jaquays",
	"Brandon James",
	"Todd Hollenshead",
	"Barrett (Bear) Alexander",
	"Katherine Anna Kang",
	"Donna Jackson",
	"Dave \"Zoid\" Kirsch",
	"",
	"",
	"",
	"+THANKS TO ACTIVISION",
	"+IN PARTICULAR:",
	"",
	"Marty Stratton",
	"Henk Hartong",
	"Mitch Lasky",
	"Steve Rosenthal",
	"Steve Elwell",
	"",
	"+AND THE GAME TESTERS",
	"",
	"The Ranger Clan",
	"Dave \"Zoid\" Kirsch",
	"Nihilistic Software",
	"Robert Duffy",
	"",
	"And Countless Others",
	"",
	"",
	"",
	"Quake II Mission Pack 2: Ground Zero",
	"(tm) (C)1998 Id Software, Inc. All",
	"Rights Reserved. Developed by Rogue",
	"Entertainment, Inc. for Id Software,",
	"Inc. Distributed by Activision Inc.",
	"under license. Quake(R) is a",
	"registered trademark of Id Software,",
	"Inc. Quake II Mission Pack 2: Ground",
	"Zero(tm), Quake II(tm), the Id",
	"Software name, the \"Q II\"(tm) logo",
	"and id(tm) logo are trademarks of Id",
	"Software, Inc. Activision(R) is a",
	"registered trademark of Activision,",
	"Inc. Rogue(R) is a registered",
	"trademark of Rogue Entertainment,",
	"Inc. All other trademarks and trade",
	"names are properties of their",
	"respective owners.",
	0
};


void M_Credits_MenuDraw( void )
{
	int i, y;

	/*
	** draw the credits
	*/
	for ( i = 0, y = vid_so.viddef.height - ( ( cl_main.cls.realtime - credits_start_time ) / 40.0F ); credits[i] && y < vid_so.viddef.height; y += 10, i++ )
	{
		int j, stringoffset = 0;
		int bold = false;

		if ( y <= -8 )
			continue;

		if ( credits[i][0] == '+' )
		{
			bold = true;
			stringoffset = 1;
		}
		else
		{
			bold = false;
			stringoffset = 0;
		}

		for ( j = 0; credits[i][j+stringoffset]; j++ )
		{
			int x;

			x = ( vid_so.viddef.width - strlen( credits[i] ) * 8 - stringoffset * 8 ) / 2 + ( j + stringoffset ) * 8;

			if ( bold )
				vid_so.re.DrawChar( x, y, credits[i][j+stringoffset] + 128 );
			else
				vid_so.re.DrawChar( x, y, credits[i][j+stringoffset] );
		}
	}

	if ( y < 0 )
		credits_start_time = cl_main.cls.realtime;
}

const char *M_Credits_Key( int key )
{
	switch (key)
	{
	case K_ESCAPE:
		if (creditsBuffer)
			FS_FreeFile (creditsBuffer);
		M_PopMenu ();
		break;
	}

	return menu_out_sound;

}

extern int Developer_searchpath (int who);

"""
credits_start_time = 0
credits = []
credits_index = []
credits_buffer = None

idcredits = [
	"+QUAKE II BY ID SOFTWARE",
	"",
	"+PROGRAMMING",
	"John Carmack",
	"John Cash",
	"Brian Hook",
	"",
	"+ART",
	"Adrian Carmack",
	"Kevin Cloud",
	"Paul Steed",
	"",
	"+LEVEL DESIGN",
	"Tim Willits",
	"American McGee",
	"Christian Antkow",
	"Paul Jaquays",
	"Brandon James",
	"",
	"+BIZ",
	"Todd Hollenshead",
	"Barrett (Bear) Alexander",
	"Donna Jackson",
	"",
	"",
	"+SPECIAL THANKS",
	"Ben Donges for beta testing",
	"",
	"",
	"",
	"",
	"",
	"",
	"+ADDITIONAL SUPPORT",
	"",
	"+LINUX PORT AND CTF",
	"Dave \"Zoid\" Kirsch",
	"",
	"+CINEMATIC SEQUENCES",
	"Ending Cinematic by Blur Studio - ",
	"Venice, CA",
	"",
	"Environment models for Introduction",
	"Cinematic by Karl Dolgener",
	"",
	"Assistance with environment design",
	"by Cliff Iwai",
	"",
	"+SOUND EFFECTS AND MUSIC",
	"Sound Design by Soundelux Media Labs.",
	"Music Composed and Produced by",
	"Soundelux Media Labs.  Special thanks",
	"to Bill Brown, Tom Ozanich, Brian",
	"Celano, Jeff Eisner, and The Soundelux",
	"Players.",
	"",
	"\"Level Music\" by Sonic Mayhem",
	"www.sonicmayhem.com",
	"",
	"\"Quake II Theme Song\"",
	"(C) 1997 Rob Zombie. All Rights",
	"Reserved.",
	"",
	"Track 10 (\"Climb\") by Jer Sypult",
	"",
	"Voice of computers by",
	"Carly Staehlin-Taylor",
	"",
	"+THANKS TO ACTIVISION",
	"+IN PARTICULAR:",
	"",
	"John Tam",
	"Steve Rosenthal",
	"Marty Stratton",
	"Henk Hartong",
	"",
	"Quake II(tm) (C)1997 Id Software, Inc.",
	"All Rights Reserved.  Distributed by",
	"Activision, Inc. under license.",
	"Quake II(tm), the Id Software name,",
	"the \"Q II\"(tm) logo and id(tm)",
	"logo are trademarks of Id Software,",
	"Inc. Activision(R) is a registered",
	"trademark of Activision, Inc. All",
	"other trademarks and trade names are",
	"properties of their respective owners.",
]

xatcredits = [
	"+QUAKE II MISSION PACK: THE RECKONING",
	"+BY",
	"+XATRIX ENTERTAINMENT, INC.",
	"",
	"+DESIGN AND DIRECTION",
	"Drew Markham",
	"",
	"+PRODUCED BY",
	"Greg Goodrich",
	"",
	"+PROGRAMMING",
	"Rafael Paiz",
	"",
	"+LEVEL DESIGN / ADDITIONAL GAME DESIGN",
	"Alex Mayberry",
	"",
	"+LEVEL DESIGN",
	"Mal Blackwell",
	"Dan Koppel",
	"",
	"+ART DIRECTION",
	"Michael \"Maxx\" Kaufman",
	"",
	"+COMPUTER GRAPHICS SUPERVISOR AND",
	"+CHARACTER ANIMATION DIRECTION",
	"Barry Dempsey",
	"",
	"+SENIOR ANIMATOR AND MODELER",
	"Jason Hoover",
	"",
	"+CHARACTER ANIMATION AND",
	"+MOTION CAPTURE SPECIALIST",
	"Amit Doron",
	"",
	"+ART",
	"Claire Praderie-Markham",
	"Viktor Antonov",
	"Corky Lehmkuhl",
	"",
	"+INTRODUCTION ANIMATION",
	"Dominique Drozdz",
	"",
	"+ADDITIONAL LEVEL DESIGN",
	"Aaron Barber",
	"Rhett Baldwin",
	"",
	"+3D CHARACTER ANIMATION TOOLS",
	"Gerry Tyra, SA Technology",
	"",
	"+ADDITIONAL EDITOR TOOL PROGRAMMING",
	"Robert Duffy",
	"",
	"+ADDITIONAL PROGRAMMING",
	"Ryan Feltrin",
	"",
	"+PRODUCTION COORDINATOR",
	"Victoria Sylvester",
	"",
	"+SOUND DESIGN",
	"Gary Bradfield",
	"",
	"+MUSIC BY",
	"Sonic Mayhem",
	"",
	"",
	"",
	"+SPECIAL THANKS",
	"+TO",
	"+OUR FRIENDS AT ID SOFTWARE",
	"",
	"John Carmack",
	"John Cash",
	"Brian Hook",
	"Adrian Carmack",
	"Kevin Cloud",
	"Paul Steed",
	"Tim Willits",
	"Christian Antkow",
	"Paul Jaquays",
	"Brandon James",
	"Todd Hollenshead",
	"Barrett (Bear) Alexander",
	"Dave \"Zoid\" Kirsch",
	"Donna Jackson",
	"",
	"",
	"",
	"+THANKS TO ACTIVISION",
	"+IN PARTICULAR:",
	"",
	"Marty Stratton",
	"Henk \"The Original Ripper\" Hartong",
	"Kevin Kraff",
	"Jamey Gottlieb",
	"Chris Hepburn",
	"",
	"+AND THE GAME TESTERS",
	"",
	"Tim Vanlaw",
	"Doug Jacobs",
	"Steven Rosenthal",
	"David Baker",
	"Chris Campbell",
	"Aaron Casillas",
	"Steve Elwell",
	"Derek Johnstone",
	"Igor Krinitskiy",
	"Samantha Lee",
	"Michael Spann",
	"Chris Toft",
	"Juan Valdes",
	"",
	"+THANKS TO INTERGRAPH COMPUTER SYTEMS",
	"+IN PARTICULAR:",
	"",
	"Michael T. Nicolaou",
	"",
	"",
	"Quake II Mission Pack: The Reckoning",
	"(tm) (C)1998 Id Software, Inc. All",
	"Rights Reserved. Developed by Xatrix",
	"Entertainment, Inc. for Id Software,",
	"Inc. Distributed by Activision Inc.",
	"under license. Quake(R) is a",
	"registered trademark of Id Software,",
	"Inc. Quake II Mission Pack: The",
	"Reckoning(tm), Quake II(tm), the Id",
	"Software name, the \"Q II\"(tm) logo",
	"and id(tm) logo are trademarks of Id",
	"Software, Inc. Activision(R) is a",
	"registered trademark of Activision,",
	"Inc. Xatrix(R) is a registered",
	"trademark of Xatrix Entertainment,",
	"Inc. All other trademarks and trade",
	"names are properties of their",
	"respective owners.",
]

roguecredits = [
	"+QUAKE II MISSION PACK 2: GROUND ZERO",
	"+BY",
	"+ROGUE ENTERTAINMENT, INC.",
	"",
	"+PRODUCED BY",
	"Jim Molinets",
	"",
	"+PROGRAMMING",
	"Peter Mack",
	"Patrick Magruder",
	"",
	"+LEVEL DESIGN",
	"Jim Molinets",
	"Cameron Lamprecht",
	"Berenger Fish",
	"Robert Selitto",
	"Steve Tietze",
	"Steve Thoms",
	"",
	"+ART DIRECTION",
	"Rich Fleider",
	"",
	"+ART",
	"Rich Fleider",
	"Steve Maines",
	"Won Choi",
	"",
	"+ANIMATION SEQUENCES",
	"Creat Studios",
	"Steve Maines",
	"",
	"+ADDITIONAL LEVEL DESIGN",
	"Rich Fleider",
	"Steve Maines",
	"Peter Mack",
	"",
	"+SOUND",
	"James Grunke",
	"",
	"+GROUND ZERO THEME",
	"+AND",
	"+MUSIC BY",
	"Sonic Mayhem",
	"",
	"+VWEP MODELS",
	"Brent \"Hentai\" Dill",
	"",
	"",
	"",
	"+SPECIAL THANKS",
	"+TO",
	"+OUR FRIENDS AT ID SOFTWARE",
	"",
	"John Carmack",
	"John Cash",
	"Brian Hook",
	"Adrian Carmack",
	"Kevin Cloud",
	"Paul Steed",
	"Tim Willits",
	"Christian Antkow",
	"Paul Jaquays",
	"Brandon James",
	"Todd Hollenshead",
	"Barrett (Bear) Alexander",
	"Katherine Anna Kang",
	"Donna Jackson",
	"Dave \"Zoid\" Kirsch",
	"",
	"",
	"",
	"+THANKS TO ACTIVISION",
	"+IN PARTICULAR:",
	"",
	"Marty Stratton",
	"Henk Hartong",
	"Mitch Lasky",
	"Steve Rosenthal",
	"Steve Elwell",
	"",
	"+AND THE GAME TESTERS",
	"",
	"The Ranger Clan",
	"Dave \"Zoid\" Kirsch",
	"Nihilistic Software",
	"Robert Duffy",
	"",
	"And Countless Others",
	"",
	"",
	"",
	"Quake II Mission Pack 2: Ground Zero",
	"(tm) (C)1998 Id Software, Inc. All",
	"Rights Reserved. Developed by Rogue",
	"Entertainment, Inc. for Id Software,",
	"Inc. Distributed by Activision Inc.",
	"under license. Quake(R) is a",
	"registered trademark of Id Software,",
	"Inc. Quake II Mission Pack 2: Ground",
	"Zero(tm), Quake II(tm), the Id",
	"Software name, the \"Q II\"(tm) logo",
	"and id(tm) logo are trademarks of Id",
	"Software, Inc. Activision(R) is a",
	"registered trademark of Activision,",
	"Inc. Rogue(R) is a registered",
	"trademark of Rogue Entertainment,",
	"Inc. All other trademarks and trade",
	"names are properties of their",
	"respective owners.",
]


def M_Credits_MenuDraw():

	global credits_start_time

	i = 0
	y = vid_so.viddef.height - ((cl_main.cls.realtime - credits_start_time) / 40.0)

	while i < len(credits) and y < vid_so.viddef.height:
		line = credits[i]
		if y <= -8:
			y += 10
			i += 1
			continue

		bold = False
		stringoffset = 0
		if line.startswith("+"):
			bold = True
			stringoffset = 1

		for j, ch in enumerate(line[stringoffset:]):
			x = (
				(vid_so.viddef.width - len(line) * 8 - stringoffset * 8) / 2
				+ (j + stringoffset) * 8
			)
			if bold:
				vid_so.re.DrawChar(int(x), int(y), ord(ch) + 128)
			else:
				vid_so.re.DrawChar(int(x), int(y), ord(ch))

		y += 10
		i += 1

	if y < 0:
		credits_start_time = cl_main.cls.realtime


def M_Credits_Key(key): #int (returns const char *)

	if key == keys.K_ESCAPE:
		global credits_buffer
		if credits_buffer is not None:
			files.FS_FreeFile(credits_buffer)
			credits_buffer = None
		M_PopMenu()

	return menu_out_sound


def M_Menu_Credits_f():

	global credits_start_time, credits, credits_buffer, credits_index

	credits_buffer = None
	count, credits_buffer = files.FS_LoadFile("credits")
	if count != -1 and credits_buffer is not None:
		text = credits_buffer.decode("utf-8", errors="replace")
		lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
		credits_index = lines[:255]
		credits = credits_index
	else:
		isdeveloper = files.Developer_searchpath(1)
		if isdeveloper == 1:
			credits = xatcredits
		elif isdeveloper == 2:
			credits = roguecredits
		else:
			credits = idcredits

	credits_start_time = cl_main.cls.realtime
	M_PushMenu(M_Credits_MenuDraw, M_Credits_Key)


"""
=============================================================================

GAME MENU

=============================================================================
"""
m_game_cursor = 0 #static int

s_game_menu = menuframework_s()

s_easy_game_action = menuaction_s() #static
s_medium_game_action = menuaction_s()
s_hard_game_action = menuaction_s()

s_load_game_action = menuaction_s()
s_save_game_action = menuaction_s()
s_credits_action = menuaction_s()

s_blankline = menuseparator_s()

def StartGame( ):

	# disable updates and start the cinematic going
	cl_main.cl.servercount = -1
	M_ForceMenuOff ()
	cvar.Cvar_SetValue( "deathmatch", 0 )
	cvar.Cvar_SetValue( "coop", 0 )

	cvar.Cvar_SetValue( "gamerules", 0 )		#PGM

	cmd.Cbuf_AddText ("loading ; killserver ; wait ; newgame\n")
	cl_main.cls.key_dest = client.keydest_t.key_game


def EasyGameFunc( data ): #void *

	cvar.Cvar_ForceSet( "skill", "0" )
	StartGame()


def MediumGameFunc( data ):

	cvar.Cvar_ForceSet( "skill", "1" )
	StartGame()


def HardGameFunc( data ):

	cvar.Cvar_ForceSet( "skill", "2" )
	StartGame()


def LoadGameFunc( unused ):

	M_Menu_LoadGame_f ()


def SaveGameFunc( unused ):

	M_Menu_SaveGame_f()


def CreditsFunc( unused ):

	M_Menu_Credits_f()


def Game_MenuInit( ):

	
	difficulty_names = [
		"easy",
		"medium",
		"hard",
		0
	] #static const char *[]

	s_game_menu.x = vid_so.viddef.width * 0.50
	s_game_menu.nitems = 0

	s_easy_game_action.flags  = QMF_LEFT_JUSTIFY
	s_easy_game_action.x		= 0
	s_easy_game_action.y		= 0
	s_easy_game_action.name	= "easy"
	s_easy_game_action.callback = EasyGameFunc

	s_medium_game_action.flags  = QMF_LEFT_JUSTIFY
	s_medium_game_action.x		= 0
	s_medium_game_action.y		= 10
	s_medium_game_action.name	= "medium"
	s_medium_game_action.callback = MediumGameFunc

	s_hard_game_action.flags  = QMF_LEFT_JUSTIFY
	s_hard_game_action.x		= 0
	s_hard_game_action.y		= 20
	s_hard_game_action.name	= "hard"
	s_hard_game_action.callback = HardGameFunc

	s_load_game_action.flags  = QMF_LEFT_JUSTIFY
	s_load_game_action.x		= 0
	s_load_game_action.y		= 40
	s_load_game_action.name	= "load game"
	s_load_game_action.callback = LoadGameFunc

	s_save_game_action.flags  = QMF_LEFT_JUSTIFY
	s_save_game_action.x		= 0
	s_save_game_action.y		= 50
	s_save_game_action.name	= "save game"
	s_save_game_action.callback = SaveGameFunc

	s_credits_action.flags  = QMF_LEFT_JUSTIFY
	s_credits_action.x		= 0
	s_credits_action.y		= 60
	s_credits_action.name	= "credits"
	s_credits_action.callback = CreditsFunc
	
	qmenu.Menu_AddItem( s_game_menu, s_easy_game_action )
	qmenu.Menu_AddItem( s_game_menu, s_medium_game_action )
	qmenu.Menu_AddItem( s_game_menu, s_hard_game_action )
	qmenu.Menu_AddItem( s_game_menu, s_blankline )
	
	qmenu.Menu_AddItem( s_game_menu, s_load_game_action )
	qmenu.Menu_AddItem( s_game_menu, s_save_game_action )
	qmenu.Menu_AddItem( s_game_menu, s_blankline )
	qmenu.Menu_AddItem( s_game_menu, s_credits_action )
	
	qmenu.Menu_Center( s_game_menu )

def Game_MenuDraw( ):

	M_Banner( "m_banner_game" )
	qmenu.Menu_AdjustCursor( s_game_menu, 1 )
	qmenu.Menu_Draw( s_game_menu )


def Game_MenuKey( key ):

	return Default_MenuKey( s_game_menu, key )


def M_Menu_Game_f ():

	global m_game_cursor

	Game_MenuInit()
	M_PushMenu( Game_MenuDraw, Game_MenuKey )
	m_game_cursor = 1

"""
=============================================================================

LOADGAME MENU

=============================================================================
*/

#define	MAX_SAVEGAMES	15

static menuframework_s	s_savegame_menu;

static menuframework_s	s_loadgame_menu;
static menuaction_s		s_loadgame_actions[MAX_SAVEGAMES];

char		m_savestrings[MAX_SAVEGAMES][32];
qboolean	m_savevalid[MAX_SAVEGAMES];

void Create_Savestrings (void)
{
	int		i;
	FILE	*f;
	char	name[MAX_OSPATH];

	for (i=0 ; i<MAX_SAVEGAMES ; i++)
	{
		Com_sprintf (name, sizeof(name), "%s/save/save%i/server.ssv", FS_Gamedir(), i);
		f = fopen (name, "rb");
		if (!f)
		{
			strcpy (m_savestrings[i], "<EMPTY>");
			m_savevalid[i] = false;
		}
		else
		{
			FS_Read (m_savestrings[i], sizeof(m_savestrings[i]), f);
			fclose (f);
			m_savevalid[i] = true;
		}
	}
}

void LoadGameCallback( void *self )
{
	menuaction_s *a = ( menuaction_s * ) self;

	if ( m_savevalid[ a->localdata[0] ] )
		Cbuf_AddText (va("load save%i\n",  a->localdata[0] ) );
	M_ForceMenuOff ();
}

void LoadGame_MenuInit( void )
{
	int i;

	s_loadgame_menu.x = vid_so.viddef.width / 2 - 120;
	s_loadgame_menu.y = vid_so.viddef.height / 2 - 58;
	s_loadgame_menu.nitems = 0;

	Create_Savestrings();

	for ( i = 0; i < MAX_SAVEGAMES; i++ )
	{
		s_loadgame_actions[i].name			= m_savestrings[i];
		s_loadgame_actions[i].flags			= QMF_LEFT_JUSTIFY;
		s_loadgame_actions[i].localdata[0]	= i;
		s_loadgame_actions[i].callback		= LoadGameCallback;

		s_loadgame_actions[i].x = 0;
		s_loadgame_actions[i].y = ( i ) * 10;
		if (i>0)	// separate from autosave
			s_loadgame_actions[i].y += 10;

		s_loadgame_actions[i].type = MTYPE_ACTION;

		qmenu.Menu_AddItem( &s_loadgame_menu, &s_loadgame_actions[i] );
	}
}

void LoadGame_MenuDraw( void )
{
	M_Banner( "m_banner_load_game" );
//	qmenu.Menu_AdjustCursor( &s_loadgame_menu, 1 );
	qmenu.Menu_Draw( &s_loadgame_menu );
}

const char *LoadGame_MenuKey( int key )
{
	if ( key == K_ESCAPE || key == K_ENTER )
	{
		s_savegame_menu.cursor = s_loadgame_menu.cursor - 1;
		if ( s_savegame_menu.cursor < 0 )
			s_savegame_menu.cursor = 0;
	}
	return Default_MenuKey( &s_loadgame_menu, key );
}

"""
MAX_SAVEGAMES = 15

s_savegame_menu = menuframework_s()
s_loadgame_menu = menuframework_s()
s_loadgame_actions = [menuaction_s() for _ in range(MAX_SAVEGAMES)]
s_savegame_actions = [menuaction_s() for _ in range(MAX_SAVEGAMES)]

m_savestrings = [""] * MAX_SAVEGAMES
m_savevalid = [False] * MAX_SAVEGAMES


def Create_Savestrings():

	for i in range(MAX_SAVEGAMES):
		name = "{}/save/save{}/server.ssv".format(files.FS_Gamedir(), i)
		try:
			with open(name, "rb") as f:
				data = files.FS_Read(32, f)
			m_savestrings[i] = data.decode("utf-8", errors="replace").split("\x00", 1)[0]
			m_savevalid[i] = True
		except FileNotFoundError:
			m_savestrings[i] = "<EMPTY>"
			m_savevalid[i] = False


def LoadGameCallback(self):

	if m_savevalid[self.localdata[0]]:
		cmd.Cbuf_AddText("load save{}\n".format(self.localdata[0]))
	M_ForceMenuOff()


def LoadGame_MenuInit():

	s_loadgame_menu.x = vid_so.viddef.width // 2 - 120
	s_loadgame_menu.y = vid_so.viddef.height // 2 - 58
	s_loadgame_menu.nitems = 0

	Create_Savestrings()

	for i in range(MAX_SAVEGAMES):
		action = s_loadgame_actions[i]
		action.name = m_savestrings[i]
		action.flags = QMF_LEFT_JUSTIFY
		action.localdata[0] = i
		action.callback = LoadGameCallback

		action.x = 0
		action.y = i * 10
		if i > 0:
			action.y += 10

		action.type = MTYPE_ACTION

		qmenu.Menu_AddItem(s_loadgame_menu, action)


def LoadGame_MenuDraw():

	M_Banner("m_banner_load_game")
	qmenu.Menu_Draw(s_loadgame_menu)


def LoadGame_MenuKey(key): #int (returns const char *)

	if key in (keys.K_ESCAPE, keys.K_ENTER):
		s_savegame_menu.cursor = s_loadgame_menu.cursor - 1
		if s_savegame_menu.cursor < 0:
			s_savegame_menu.cursor = 0

	return Default_MenuKey(s_loadgame_menu, key)


def M_Menu_LoadGame_f ():

	LoadGame_MenuInit()
	M_PushMenu(LoadGame_MenuDraw, LoadGame_MenuKey)

"""
=============================================================================

SAVEGAME MENU

=============================================================================
*/
static menuframework_s	s_savegame_menu;
static menuaction_s		s_savegame_actions[MAX_SAVEGAMES];

void SaveGameCallback( void *self )
{
	menuaction_s *a = ( menuaction_s * ) self;

	Cbuf_AddText (va("save save%i\n", a->localdata[0] ));
	M_ForceMenuOff ();
}

void SaveGame_MenuDraw( void )
{
	M_Banner( "m_banner_save_game" );
	qmenu.Menu_AdjustCursor( &s_savegame_menu, 1 );
	qmenu.Menu_Draw( &s_savegame_menu );
}

void SaveGame_MenuInit( void )
{
	int i;

	s_savegame_menu.x = vid_so.viddef.width / 2 - 120;
	s_savegame_menu.y = vid_so.viddef.height / 2 - 58;
	s_savegame_menu.nitems = 0;

	Create_Savestrings();

	// don't include the autosave slot
	for ( i = 0; i < MAX_SAVEGAMES-1; i++ )
	{
		s_savegame_actions[i].name = m_savestrings[i+1];
		s_savegame_actions[i].localdata[0] = i+1;
		s_savegame_actions[i].flags = QMF_LEFT_JUSTIFY;
		s_savegame_actions[i].callback = SaveGameCallback;

		s_savegame_actions[i].x = 0;
		s_savegame_actions[i].y = ( i ) * 10;

		s_savegame_actions[i].type = MTYPE_ACTION;

		qmenu.Menu_AddItem( &s_savegame_menu, &s_savegame_actions[i] );
	}
}

const char *SaveGame_MenuKey( int key )
{
	if ( key == K_ENTER || key == K_ESCAPE )
	{
		s_loadgame_menu.cursor = s_savegame_menu.cursor - 1;
		if ( s_loadgame_menu.cursor < 0 )
			s_loadgame_menu.cursor = 0;
	}
	return Default_MenuKey( &s_savegame_menu, key );
}

"""
def SaveGameCallback(self):

	cmd.Cbuf_AddText("save save{}\n".format(self.localdata[0]))
	M_ForceMenuOff()


def SaveGame_MenuDraw():

	M_Banner("m_banner_save_game")
	qmenu.Menu_AdjustCursor(s_savegame_menu, 1)
	qmenu.Menu_Draw(s_savegame_menu)


def SaveGame_MenuInit():

	s_savegame_menu.x = vid_so.viddef.width // 2 - 120
	s_savegame_menu.y = vid_so.viddef.height // 2 - 58
	s_savegame_menu.nitems = 0

	Create_Savestrings()

	for i in range(MAX_SAVEGAMES - 1):
		action = s_savegame_actions[i]
		action.name = m_savestrings[i + 1]
		action.localdata[0] = i + 1
		action.flags = QMF_LEFT_JUSTIFY
		action.callback = SaveGameCallback

		action.x = 0
		action.y = i * 10
		action.type = MTYPE_ACTION

		qmenu.Menu_AddItem(s_savegame_menu, action)


def SaveGame_MenuKey(key): #int (returns const char *)

	if key in (keys.K_ENTER, keys.K_ESCAPE):
		s_loadgame_menu.cursor = s_savegame_menu.cursor - 1
		if s_loadgame_menu.cursor < 0:
			s_loadgame_menu.cursor = 0

	return Default_MenuKey(s_savegame_menu, key)


def M_Menu_SaveGame_f ():

	if not common.Com_ServerState():
		return

	SaveGame_MenuInit()
	M_PushMenu(SaveGame_MenuDraw, SaveGame_MenuKey)
	Create_Savestrings()



"""
=============================================================================

JOIN SERVER MENU

=============================================================================
*/
#define MAX_LOCAL_SERVERS 8

static menuframework_s	s_joinserver_menu;
static menuseparator_s	s_joinserver_server_title;
static menuaction_s		s_joinserver_search_action;
static menuaction_s		s_joinserver_address_book_action;
static menuaction_s		s_joinserver_server_actions[MAX_LOCAL_SERVERS];

int		m_num_servers;
#define	NO_SERVER_STRING	"<no server>"

// user readable information
static char local_server_names[MAX_LOCAL_SERVERS][80];

// network address
static netadr_t local_server_netadr[MAX_LOCAL_SERVERS];

void M_AddToServerList (netadr_t adr, char *info)
{
	int		i;

	if (m_num_servers == MAX_LOCAL_SERVERS)
		return;
	while ( *info == ' ' )
		info++;

	// ignore if duplicated
	for (i=0 ; i<m_num_servers ; i++)
		if (!strcmp(info, local_server_names[i]))
			return;

	local_server_netadr[m_num_servers] = adr;
	strncpy (local_server_names[m_num_servers], info, sizeof(local_server_names[0])-1);
	m_num_servers++;
}


void JoinServerFunc( void *self )
{
	char	buffer[128];
	int		index;

	index = ( menuaction_s * ) self - s_joinserver_server_actions;

	if ( Q_stricmp( local_server_names[index], NO_SERVER_STRING ) == 0 )
		return;

	if (index >= m_num_servers)
		return;

	Com_sprintf (buffer, sizeof(buffer), "connect %s\n", NET_AdrToString (local_server_netadr[index]));
	Cbuf_AddText (buffer);
	M_ForceMenuOff ();
}

void AddressBookFunc( void *self )
{
	M_Menu_AddressBook_f();
}

void NullCursorDraw( void *self )
{
}

void SearchLocalGames( void )
{
	int		i;

	m_num_servers = 0;
	for (i=0 ; i<MAX_LOCAL_SERVERS ; i++)
		strcpy (local_server_names[i], NO_SERVER_STRING);

	M_DrawTextBox( 8, 120 - 48, 36, 3 );
	M_Print( 16 + 16, 120 - 48 + 8,  "Searching for local servers, this" );
	M_Print( 16 + 16, 120 - 48 + 16, "could take up to a minute, so" );
	M_Print( 16 + 16, 120 - 48 + 24, "please be patient." );

	// the text box won't show up unless we do a buffer swap
	vid_so.re.EndFrame();

	// send out info packets
	CL_PingServers_f();
}

void SearchLocalGamesFunc( void *self )
{
	SearchLocalGames();
}

void JoinServer_MenuInit( void )
{
	int i;

	s_joinserver_menu.x = vid_so.viddef.width * 0.50 - 120;
	s_joinserver_menu.nitems = 0;

	s_joinserver_address_book_action.type	= MTYPE_ACTION;
	s_joinserver_address_book_action.name	= "address book";
	s_joinserver_address_book_action.flags	= QMF_LEFT_JUSTIFY;
	s_joinserver_address_book_action.x		= 0;
	s_joinserver_address_book_action.y		= 0;
	s_joinserver_address_book_action.callback = AddressBookFunc;

	s_joinserver_search_action.type = MTYPE_ACTION;
	s_joinserver_search_action.name	= "refresh server list";
	s_joinserver_search_action.flags	= QMF_LEFT_JUSTIFY;
	s_joinserver_search_action.x	= 0;
	s_joinserver_search_action.y	= 10;
	s_joinserver_search_action.callback = SearchLocalGamesFunc;
	s_joinserver_search_action.statusbar = "search for servers";

	s_joinserver_server_title.type = MTYPE_SEPARATOR;
	s_joinserver_server_title.name = "connect to...";
	s_joinserver_server_title.x    = 80;
	s_joinserver_server_title.y	   = 30;

	for ( i = 0; i < MAX_LOCAL_SERVERS; i++ )
	{
		s_joinserver_server_actions[i].type	= MTYPE_ACTION;
		strcpy (local_server_names[i], NO_SERVER_STRING);
		s_joinserver_server_actions[i].name	= local_server_names[i];
		s_joinserver_server_actions[i].flags	= QMF_LEFT_JUSTIFY;
		s_joinserver_server_actions[i].x		= 0;
		s_joinserver_server_actions[i].y		= 40 + i*10;
		s_joinserver_server_actions[i].callback = JoinServerFunc;
		s_joinserver_server_actions[i].statusbar = "press ENTER to connect";
	}

	qmenu.Menu_AddItem( &s_joinserver_menu, &s_joinserver_address_book_action );
	qmenu.Menu_AddItem( &s_joinserver_menu, &s_joinserver_server_title );
	qmenu.Menu_AddItem( &s_joinserver_menu, &s_joinserver_search_action );

	for ( i = 0; i < 8; i++ )
		qmenu.Menu_AddItem( &s_joinserver_menu, &s_joinserver_server_actions[i] );

	qmenu.Menu_Center( &s_joinserver_menu );

	SearchLocalGames();
}

void JoinServer_MenuDraw(void)
{
	M_Banner( "m_banner_join_server" );
	qmenu.Menu_Draw( &s_joinserver_menu );
}


const char *JoinServer_MenuKey( int key )
{
	return Default_MenuKey( &s_joinserver_menu, key );
}

void M_Menu_JoinServer_f (void)
{
	JoinServer_MenuInit();
	M_PushMenu( JoinServer_MenuDraw, JoinServer_MenuKey );
}

MAX_LOCAL_SERVERS = 8
NO_SERVER_STRING = "<no server>"

s_joinserver_menu = menuframework_s()
s_joinserver_server_title = menuseparator_s()
s_joinserver_search_action = menuaction_s()
s_joinserver_address_book_action = menuaction_s()
s_joinserver_server_actions = [menuaction_s() for _ in range(MAX_LOCAL_SERVERS)]

m_num_servers = 0
local_server_names = [NO_SERVER_STRING for _ in range(MAX_LOCAL_SERVERS)]
local_server_netadr = [None for _ in range(MAX_LOCAL_SERVERS)]


def M_AddToServerList(adr, info):

	global m_num_servers

	if m_num_servers == MAX_LOCAL_SERVERS:
		return

	info = info.lstrip(" ")

	for i in range(m_num_servers):
		if q_shared.Q_stricmp(info, local_server_names[i]) == 0:
			return

	local_server_netadr[m_num_servers] = adr
	local_server_names[m_num_servers] = info[:79]
	if m_num_servers < len(s_joinserver_server_actions):
		s_joinserver_server_actions[m_num_servers].name = local_server_names[m_num_servers]
	m_num_servers += 1


def JoinServerFunc(self):

	index = s_joinserver_server_actions.index(self)

	if q_shared.Q_stricmp(local_server_names[index], NO_SERVER_STRING) == 0:
		return

	if index >= m_num_servers:
		return

	address = net_udp.NET_AdrToString(local_server_netadr[index])
	cmd.Cbuf_AddText("connect {}\n".format(address))
	M_ForceMenuOff()


def AddressBookFunc(unused):

	M_Menu_AddressBook_f()


def NullCursorDraw(unused):
	pass


def SearchLocalGames():

	global m_num_servers, local_server_names, local_server_netadr

	m_num_servers = 0
	local_server_names = [NO_SERVER_STRING for _ in range(MAX_LOCAL_SERVERS)]
	local_server_netadr = [None for _ in range(MAX_LOCAL_SERVERS)]
	for i in range(MAX_LOCAL_SERVERS):
		s_joinserver_server_actions[i].name = local_server_names[i]

	M_DrawTextBox(8, 120 - 48, 36, 3)
	M_Print(16 + 16, 120 - 48 + 8, "Searching for local servers, this")
	M_Print(16 + 16, 120 - 48 + 16, "could take up to a minute, so")
	M_Print(16 + 16, 120 - 48 + 24, "please be patient.")

	# the text box won't show up unless we do a buffer swap
	vid_so.re.EndFrame()

	# send out info packets
	if hasattr(cl_main, "CL_PingServers_f"):
		cl_main.CL_PingServers_f()
	else:
		common.Com_Printf("CL_PingServers_f not available.\n")


def SearchLocalGamesFunc(unused):

	SearchLocalGames()


def JoinServer_MenuInit():

	s_joinserver_menu.x = vid_so.viddef.width * 0.50 - 120
	s_joinserver_menu.nitems = 0

	s_joinserver_address_book_action.type = MTYPE_ACTION
	s_joinserver_address_book_action.name = "address book"
	s_joinserver_address_book_action.flags = QMF_LEFT_JUSTIFY
	s_joinserver_address_book_action.x = 0
	s_joinserver_address_book_action.y = 0
	s_joinserver_address_book_action.callback = AddressBookFunc

	s_joinserver_search_action.type = MTYPE_ACTION
	s_joinserver_search_action.name = "refresh server list"
	s_joinserver_search_action.flags = QMF_LEFT_JUSTIFY
	s_joinserver_search_action.x = 0
	s_joinserver_search_action.y = 10
	s_joinserver_search_action.callback = SearchLocalGamesFunc
	s_joinserver_search_action.statusbar = "search for servers"

	s_joinserver_server_title.type = MTYPE_SEPARATOR
	s_joinserver_server_title.name = "connect to..."
	s_joinserver_server_title.x = 80
	s_joinserver_server_title.y = 30

	for i in range(MAX_LOCAL_SERVERS):
		action = s_joinserver_server_actions[i]
		action.type = MTYPE_ACTION
		local_server_names[i] = NO_SERVER_STRING
		action.name = local_server_names[i]
		action.flags = QMF_LEFT_JUSTIFY
		action.x = 0
		action.y = 40 + i * 10
		action.callback = JoinServerFunc
		action.statusbar = "press ENTER to connect"

	qmenu.Menu_AddItem(s_joinserver_menu, s_joinserver_address_book_action)
	qmenu.Menu_AddItem(s_joinserver_menu, s_joinserver_server_title)
	qmenu.Menu_AddItem(s_joinserver_menu, s_joinserver_search_action)

	for i in range(MAX_LOCAL_SERVERS):
		qmenu.Menu_AddItem(s_joinserver_menu, s_joinserver_server_actions[i])

	qmenu.Menu_Center(s_joinserver_menu)
	SearchLocalGames()


def JoinServer_MenuDraw():

	M_Banner("m_banner_join_server")
	qmenu.Menu_Draw(s_joinserver_menu)


def JoinServer_MenuKey(key): #int (returns const char *)

	return Default_MenuKey(s_joinserver_menu, key)


def M_Menu_JoinServer_f():

	JoinServer_MenuInit()
	M_PushMenu(JoinServer_MenuDraw, JoinServer_MenuKey)


/*
=============================================================================

START SERVER MENU

=============================================================================
*/
static menuframework_s s_startserver_menu;
static char **mapnames;
static int	  nummaps;

static menuaction_s	s_startserver_start_action;
static menuaction_s	s_startserver_dmoptions_action;
static menufield_s	s_timelimit_field;
static menufield_s	s_fraglimit_field;
static menufield_s	s_maxclients_field;
static menufield_s	s_hostname_field;
static menulist_s	s_startmap_list;
static menulist_s	s_rules_box;

void DMOptionsFunc( void *self )
{
	if (s_rules_box.curvalue == 1)
		return;
	M_Menu_DMOptions_f();
}

void RulesChangeFunc ( void *self )
{
	// DM
	if (s_rules_box.curvalue == 0)
	{
		s_maxclients_field.statusbar = NULL;
		s_startserver_dmoptions_action.statusbar = NULL;
	}
	else if(s_rules_box.curvalue == 1)		// coop				// PGM
	{
		s_maxclients_field.statusbar = "4 maximum for cooperative";
		if (atoi(s_maxclients_field.buffer) > 4)
			strcpy( s_maxclients_field.buffer, "4" );
		s_startserver_dmoptions_action.statusbar = "N/A for cooperative";
	}
//=====
//PGM
	// ROGUE GAMES
	else if(Developer_searchpath(2) == 2)
	{
		if (s_rules_box.curvalue == 2)			// tag	
		{
			s_maxclients_field.statusbar = NULL;
			s_startserver_dmoptions_action.statusbar = NULL;
		}
/*
		else if(s_rules_box.curvalue == 3)		// deathball
		{
			s_maxclients_field.statusbar = NULL;
			s_startserver_dmoptions_action.statusbar = NULL;
		}
*/
	}
//PGM
//=====
}

void StartServerActionFunc( void *self )
{
	char	startmap[1024];
	int		timelimit;
	int		fraglimit;
	int		maxclients;
	char	*spot;

	strcpy( startmap, strchr( mapnames[s_startmap_list.curvalue], '\n' ) + 1 );

	maxclients  = atoi( s_maxclients_field.buffer );
	timelimit	= atoi( s_timelimit_field.buffer );
	fraglimit	= atoi( s_fraglimit_field.buffer );

	Cvar_SetValue( "maxclients", ClampCvar( 0, maxclients, maxclients ) );
	Cvar_SetValue ("timelimit", ClampCvar( 0, timelimit, timelimit ) );
	Cvar_SetValue ("fraglimit", ClampCvar( 0, fraglimit, fraglimit ) );
	Cvar_Set("hostname", s_hostname_field.buffer );
//	Cvar_SetValue ("deathmatch", !s_rules_box.curvalue );
//	Cvar_SetValue ("coop", s_rules_box.curvalue );

//PGM
	if((s_rules_box.curvalue < 2) || (Developer_searchpath(2) != 2))
	{
		Cvar_SetValue ("deathmatch", !s_rules_box.curvalue );
		Cvar_SetValue ("coop", s_rules_box.curvalue );
		Cvar_SetValue ("gamerules", 0 );
	}
	else
	{
		Cvar_SetValue ("deathmatch", 1 );	// deathmatch is always true for rogue games, right?
		Cvar_SetValue ("coop", 0 );			// FIXME - this might need to depend on which game we're running
		Cvar_SetValue ("gamerules", s_rules_box.curvalue );
	}
//PGM

	spot = NULL;
	if (s_rules_box.curvalue == 1)		// PGM
	{
 		if(Q_stricmp(startmap, "bunk1") == 0)
  			spot = "start";
 		else if(Q_stricmp(startmap, "mintro") == 0)
  			spot = "start";
 		else if(Q_stricmp(startmap, "fact1") == 0)
  			spot = "start";
 		else if(Q_stricmp(startmap, "power1") == 0)
  			spot = "pstart";
 		else if(Q_stricmp(startmap, "biggun") == 0)
  			spot = "bstart";
 		else if(Q_stricmp(startmap, "hangar1") == 0)
  			spot = "unitstart";
 		else if(Q_stricmp(startmap, "city1") == 0)
  			spot = "unitstart";
 		else if(Q_stricmp(startmap, "boss1") == 0)
			spot = "bosstart";
	}

	if (spot)
	{
		if (Com_ServerState())
			Cbuf_AddText ("disconnect\n");
		Cbuf_AddText (va("gamemap \"*%s$%s\"\n", startmap, spot));
	}
	else
	{
		Cbuf_AddText (va("map %s\n", startmap));
	}

	M_ForceMenuOff ();
}

void StartServer_MenuInit( void )
{
	static const char *dm_coop_names[] =
	{
		"deathmatch",
		"cooperative",
		0
	};
//=======
//PGM
	static const char *dm_coop_names_rogue[] =
	{
		"deathmatch",
		"cooperative",
		"tag",
//		"deathball",
		0
	};
//PGM
//=======
	char *buffer;
	char  mapsname[1024];
	char *s;
	int length;
	int i;
	FILE *fp;

	/*
	** load the list of map names
	*/
	Com_sprintf( mapsname, sizeof( mapsname ), "%s/maps.lst", FS_Gamedir() );
	if ( ( fp = fopen( mapsname, "rb" ) ) == 0 )
	{
		if ( ( length = FS_LoadFile( "maps.lst", ( void ** ) &buffer ) ) == -1 )
			Com_Error( ERR_DROP, "couldn't find maps.lst\n" );
	}
	else
	{
#ifdef _WIN32
		length = filelength( fileno( fp  ) );
#else
		fseek(fp, 0, SEEK_END);
		length = ftell(fp);
		fseek(fp, 0, SEEK_SET);
#endif
		buffer = malloc( length );
		fread( buffer, length, 1, fp );
	}

	s = buffer;

	i = 0;
	while ( i < length )
	{
		if ( s[i] == '\r' )
			nummaps++;
		i++;
	}

	if ( nummaps == 0 )
		Com_Error( ERR_DROP, "no maps in maps.lst\n" );

	mapnames = malloc( sizeof( char * ) * ( nummaps + 1 ) );
	memset( mapnames, 0, sizeof( char * ) * ( nummaps + 1 ) );

	s = buffer;

	for ( i = 0; i < nummaps; i++ )
	{
    char  shortname[MAX_TOKEN_CHARS];
    char  longname[MAX_TOKEN_CHARS];
		char  scratch[200];
		int		j, l;

		strcpy( shortname, COM_Parse( &s ) );
		l = strlen(shortname);
		for (j=0 ; j<l ; j++)
			shortname[j] = toupper(shortname[j]);
		strcpy( longname, COM_Parse( &s ) );
		Com_sprintf( scratch, sizeof( scratch ), "%s\n%s", longname, shortname );

		mapnames[i] = malloc( strlen( scratch ) + 1 );
		strcpy( mapnames[i], scratch );
	}
	mapnames[nummaps] = 0;

	if ( fp != 0 )
	{
		fp = 0;
		free( buffer );
	}
	else
	{
		FS_FreeFile( buffer );
	}

	/*
	** initialize the menu stuff
	*/
	s_startserver_menu.x = vid_so.viddef.width * 0.50;
	s_startserver_menu.nitems = 0;

	s_startmap_list.type = MTYPE_SPINCONTROL;
	s_startmap_list.x	= 0;
	s_startmap_list.y	= 0;
	s_startmap_list.name	= "initial map";
	s_startmap_list.itemnames = mapnames;

	s_rules_box.type = MTYPE_SPINCONTROL;
	s_rules_box.x	= 0;
	s_rules_box.y	= 20;
	s_rules_box.name	= "rules";
	
//PGM - rogue games only available with rogue DLL.
	if(Developer_searchpath(2) == 2)
		s_rules_box.itemnames = dm_coop_names_rogue;
	else
		s_rules_box.itemnames = dm_coop_names;
//PGM

	if (Cvar_VariableValue("coop"))
		s_rules_box.curvalue = 1;
	else
		s_rules_box.curvalue = 0;
	s_rules_box.callback = RulesChangeFunc;

	s_timelimit_field.type = MTYPE_FIELD;
	s_timelimit_field.name = "time limit";
	s_timelimit_field.flags = QMF_NUMBERSONLY;
	s_timelimit_field.x	= 0;
	s_timelimit_field.y	= 36;
	s_timelimit_field.statusbar = "0 = no limit";
	s_timelimit_field.length = 3;
	s_timelimit_field.visible_length = 3;
	strcpy( s_timelimit_field.buffer, Cvar_VariableString("timelimit") );

	s_fraglimit_field.type = MTYPE_FIELD;
	s_fraglimit_field.name = "frag limit";
	s_fraglimit_field.flags = QMF_NUMBERSONLY;
	s_fraglimit_field.x	= 0;
	s_fraglimit_field.y	= 54;
	s_fraglimit_field.statusbar = "0 = no limit";
	s_fraglimit_field.length = 3;
	s_fraglimit_field.visible_length = 3;
	strcpy( s_fraglimit_field.buffer, Cvar_VariableString("fraglimit") );

	/*
	** maxclients determines the maximum number of players that can join
	** the game.  If maxclients is only "1" then we should default the menu
	** option to 8 players, otherwise use whatever its current value is. 
	** Clamping will be done when the server is actually started.
	*/
	s_maxclients_field.type = MTYPE_FIELD;
	s_maxclients_field.name = "max players";
	s_maxclients_field.flags = QMF_NUMBERSONLY;
	s_maxclients_field.x	= 0;
	s_maxclients_field.y	= 72;
	s_maxclients_field.statusbar = NULL;
	s_maxclients_field.length = 3;
	s_maxclients_field.visible_length = 3;
	if ( Cvar_VariableValue( "maxclients" ) == 1 )
		strcpy( s_maxclients_field.buffer, "8" );
	else 
		strcpy( s_maxclients_field.buffer, Cvar_VariableString("maxclients") );

	s_hostname_field.type = MTYPE_FIELD;
	s_hostname_field.name = "hostname";
	s_hostname_field.flags = 0;
	s_hostname_field.x	= 0;
	s_hostname_field.y	= 90;
	s_hostname_field.statusbar = NULL;
	s_hostname_field.length = 12;
	s_hostname_field.visible_length = 12;
	strcpy( s_hostname_field.buffer, Cvar_VariableString("hostname") );

	s_startserver_dmoptions_action.type = MTYPE_ACTION;
	s_startserver_dmoptions_action.name	= " deathmatch flags";
	s_startserver_dmoptions_action.flags= QMF_LEFT_JUSTIFY;
	s_startserver_dmoptions_action.x	= 24;
	s_startserver_dmoptions_action.y	= 108;
	s_startserver_dmoptions_action.statusbar = NULL;
	s_startserver_dmoptions_action.callback = DMOptionsFunc;

	s_startserver_start_action.type = MTYPE_ACTION;
	s_startserver_start_action.name	= " begin";
	s_startserver_start_action.flags= QMF_LEFT_JUSTIFY;
	s_startserver_start_action.x	= 24;
	s_startserver_start_action.y	= 128;
	s_startserver_start_action.callback = StartServerActionFunc;

	qmenu.Menu_AddItem( &s_startserver_menu, &s_startmap_list );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_rules_box );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_timelimit_field );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_fraglimit_field );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_maxclients_field );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_hostname_field );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_startserver_dmoptions_action );
	qmenu.Menu_AddItem( &s_startserver_menu, &s_startserver_start_action );

	qmenu.Menu_Center( s_startserver_menu )

	// call this now to set proper inital state
	RulesChangeFunc ( NULL );
}

void StartServer_MenuDraw(void)
{
	qmenu.Menu_Draw( &s_startserver_menu );
}

const char *StartServer_MenuKey( int key )
{
	if ( key == K_ESCAPE )
	{
		if ( mapnames )
		{
			int i;

			for ( i = 0; i < nummaps; i++ )
				free( mapnames[i] );
			free( mapnames );
		}
		mapnames = 0;
		nummaps = 0;
	}

	return Default_MenuKey( &s_startserver_menu, key );
}

void M_Menu_StartServer_f (void)
{
	StartServer_MenuInit();
	M_PushMenu( StartServer_MenuDraw, StartServer_MenuKey );
}

mapnames = []
nummaps = 0

s_startserver_menu = menuframework_s()
s_startserver_start_action = menuaction_s()
s_startserver_dmoptions_action = menuaction_s()
s_timelimit_field = menufield_s()
s_fraglimit_field = menufield_s()
s_maxclients_field = menufield_s()
s_hostname_field = menufield_s()
s_startmap_list = menuspincontrol_s()
s_rules_box = menuspincontrol_s()


def DMOptionsFunc(unused):

	if s_rules_box.curvalue == 1:
		return
	M_Menu_DMOptions_f()


def RulesChangeFunc(unused):

	if s_rules_box.curvalue == 0:
		s_maxclients_field.statusbar = None
		s_startserver_dmoptions_action.statusbar = None
	elif s_rules_box.curvalue == 1:
		s_maxclients_field.statusbar = "4 maximum for cooperative"
		try:
			current_max = int(s_maxclients_field.buffer)
		except (TypeError, ValueError):
			current_max = 4
		if current_max > 4:
			s_maxclients_field.buffer = "4"
		s_startserver_dmoptions_action.statusbar = "N/A for cooperative"
	elif files.Developer_searchpath(2) == 2:
		if s_rules_box.curvalue == 2:
			s_maxclients_field.statusbar = None
			s_startserver_dmoptions_action.statusbar = None


def _parse_int_buffer(value, default=0):

	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def StartServerActionFunc(unused):

	if not mapnames:
		return

	entry = mapnames[s_startmap_list.curvalue]
	if "\n" in entry:
		startmap = entry.split("\n", 1)[1]
	else:
		startmap = entry

	maxclients = _parse_int_buffer(s_maxclients_field.buffer)
	timelimit = _parse_int_buffer(s_timelimit_field.buffer)
	fraglimit = _parse_int_buffer(s_fraglimit_field.buffer)

	cvar.Cvar_SetValue("maxclients", ClampCvar(0, maxclients, maxclients))
	cvar.Cvar_SetValue("timelimit", ClampCvar(0, timelimit, timelimit))
	cvar.Cvar_SetValue("fraglimit", ClampCvar(0, fraglimit, fraglimit))
	cvar.Cvar_Set("hostname", s_hostname_field.buffer)

	if (s_rules_box.curvalue < 2) or (files.Developer_searchpath(2) != 2):
		cvar.Cvar_SetValue("deathmatch", int(not s_rules_box.curvalue))
		cvar.Cvar_SetValue("coop", int(s_rules_box.curvalue))
		cvar.Cvar_SetValue("gamerules", 0)
	else:
		cvar.Cvar_SetValue("deathmatch", 1)
		cvar.Cvar_SetValue("coop", 0)
		cvar.Cvar_SetValue("gamerules", int(s_rules_box.curvalue))

	spot = None
	if s_rules_box.curvalue == 1:
		if q_shared.Q_stricmp(startmap, "bunk1") == 0:
			spot = "start"
		elif q_shared.Q_stricmp(startmap, "mintro") == 0:
			spot = "start"
		elif q_shared.Q_stricmp(startmap, "fact1") == 0:
			spot = "start"
		elif q_shared.Q_stricmp(startmap, "power1") == 0:
			spot = "pstart"
		elif q_shared.Q_stricmp(startmap, "biggun") == 0:
			spot = "bstart"
		elif q_shared.Q_stricmp(startmap, "hangar1") == 0:
			spot = "unitstart"
		elif q_shared.Q_stricmp(startmap, "city1") == 0:
			spot = "unitstart"
		elif q_shared.Q_stricmp(startmap, "boss1") == 0:
			spot = "bosstart"

	if spot:
		if common.Com_ServerState():
			cmd.Cbuf_AddText("disconnect\n")
		cmd.Cbuf_AddText("gamemap \"*{}${}\"\n".format(startmap, spot))
	else:
		cmd.Cbuf_AddText("map {}\n".format(startmap))

	M_ForceMenuOff()


def _load_maps_list():

	path = os.path.join(files.FS_Gamedir(), "maps.lst")
	data = None
	if os.path.exists(path):
		with open(path, "rb") as fp:
			data = fp.read()
	else:
		length, data = files.FS_LoadFile("maps.lst")
		if length == -1 or data is None:
			common.Com_Error(q_shared.ERR_DROP, "couldn't find maps.lst\n")
			return ""

	return data.decode("utf-8", errors="replace")


def StartServer_MenuInit():

	global mapnames, nummaps

	dm_coop_names = [
		"deathmatch",
		"cooperative",
	]

	dm_coop_names_rogue = [
		"deathmatch",
		"cooperative",
		"tag",
	]

	buffer = _load_maps_list()
	cursor = 0
	mapnames = []
	while True:
		shortname, cursor = q_shared.COM_Parse(buffer, cursor)
		if not shortname:
			break
		longname, cursor = q_shared.COM_Parse(buffer, cursor)
		if not longname:
			break
		mapnames.append("{}\n{}".format(longname, shortname.upper()))

	nummaps = len(mapnames)
	if nummaps == 0:
		common.Com_Error(q_shared.ERR_DROP, "no maps in maps.lst\n")
		return

	s_startserver_menu.x = vid_so.viddef.width * 0.50
	s_startserver_menu.nitems = 0

	s_startmap_list.type = MTYPE_SPINCONTROL
	s_startmap_list.x = 0
	s_startmap_list.y = 0
	s_startmap_list.name = "initial map"
	s_startmap_list.itemnames = mapnames

	s_rules_box.type = MTYPE_SPINCONTROL
	s_rules_box.x = 0
	s_rules_box.y = 20
	s_rules_box.name = "rules"

	if files.Developer_searchpath(2) == 2:
		s_rules_box.itemnames = dm_coop_names_rogue
	else:
		s_rules_box.itemnames = dm_coop_names

	if cvar.Cvar_VariableValue("coop"):
		s_rules_box.curvalue = 1
	else:
		s_rules_box.curvalue = 0
	s_rules_box.callback = RulesChangeFunc

	s_timelimit_field.type = MTYPE_FIELD
	s_timelimit_field.name = "time limit"
	s_timelimit_field.flags = QMF_NUMBERSONLY
	s_timelimit_field.x = 0
	s_timelimit_field.y = 36
	s_timelimit_field.statusbar = "0 = no limit"
	s_timelimit_field.length = 3
	s_timelimit_field.visible_length = 3
	s_timelimit_field.buffer = cvar.Cvar_VariableString("timelimit")

	s_fraglimit_field.type = MTYPE_FIELD
	s_fraglimit_field.name = "frag limit"
	s_fraglimit_field.flags = QMF_NUMBERSONLY
	s_fraglimit_field.x = 0
	s_fraglimit_field.y = 54
	s_fraglimit_field.statusbar = "0 = no limit"
	s_fraglimit_field.length = 3
	s_fraglimit_field.visible_length = 3
	s_fraglimit_field.buffer = cvar.Cvar_VariableString("fraglimit")

	s_maxclients_field.type = MTYPE_FIELD
	s_maxclients_field.name = "max players"
	s_maxclients_field.flags = QMF_NUMBERSONLY
	s_maxclients_field.x = 0
	s_maxclients_field.y = 72
	s_maxclients_field.statusbar = None
	s_maxclients_field.length = 3
	s_maxclients_field.visible_length = 3
	if cvar.Cvar_VariableValue("maxclients") == 1:
		s_maxclients_field.buffer = "8"
	else:
		s_maxclients_field.buffer = cvar.Cvar_VariableString("maxclients")

	s_hostname_field.type = MTYPE_FIELD
	s_hostname_field.name = "hostname"
	s_hostname_field.flags = 0
	s_hostname_field.x = 0
	s_hostname_field.y = 90
	s_hostname_field.statusbar = None
	s_hostname_field.length = 12
	s_hostname_field.visible_length = 12
	s_hostname_field.buffer = cvar.Cvar_VariableString("hostname")

	s_startserver_dmoptions_action.type = MTYPE_ACTION
	s_startserver_dmoptions_action.name = " deathmatch flags"
	s_startserver_dmoptions_action.flags = QMF_LEFT_JUSTIFY
	s_startserver_dmoptions_action.x = 24
	s_startserver_dmoptions_action.y = 108
	s_startserver_dmoptions_action.statusbar = None
	s_startserver_dmoptions_action.callback = DMOptionsFunc

	s_startserver_start_action.type = MTYPE_ACTION
	s_startserver_start_action.name = " begin"
	s_startserver_start_action.flags = QMF_LEFT_JUSTIFY
	s_startserver_start_action.x = 24
	s_startserver_start_action.y = 128
	s_startserver_start_action.callback = StartServerActionFunc

	qmenu.Menu_AddItem(s_startserver_menu, s_startmap_list)
	qmenu.Menu_AddItem(s_startserver_menu, s_rules_box)
	qmenu.Menu_AddItem(s_startserver_menu, s_timelimit_field)
	qmenu.Menu_AddItem(s_startserver_menu, s_fraglimit_field)
	qmenu.Menu_AddItem(s_startserver_menu, s_maxclients_field)
	qmenu.Menu_AddItem(s_startserver_menu, s_hostname_field)
	qmenu.Menu_AddItem(s_startserver_menu, s_startserver_dmoptions_action)
	qmenu.Menu_AddItem(s_startserver_menu, s_startserver_start_action)

	qmenu.Menu_Center(s_startserver_menu)

	RulesChangeFunc(None)


def StartServer_MenuDraw():

	qmenu.Menu_Draw(s_startserver_menu)


def StartServer_MenuKey(key): #int (returns const char *)

	global mapnames, nummaps

	if key == keys.K_ESCAPE:
		mapnames = []
		nummaps = 0

	return Default_MenuKey(s_startserver_menu, key)


def M_Menu_StartServer_f():

	StartServer_MenuInit()
	M_PushMenu(StartServer_MenuDraw, StartServer_MenuKey)

/*
=============================================================================

DMOPTIONS BOOK MENU

=============================================================================
*/
static char dmoptions_statusbar[128];

static menuframework_s s_dmoptions_menu;

static menulist_s	s_friendlyfire_box;
static menulist_s	s_falls_box;
static menulist_s	s_weapons_stay_box;
static menulist_s	s_instant_powerups_box;
static menulist_s	s_powerups_box;
static menulist_s	s_health_box;
static menulist_s	s_spawn_farthest_box;
static menulist_s	s_teamplay_box;
static menulist_s	s_samelevel_box;
static menulist_s	s_force_respawn_box;
static menulist_s	s_armor_box;
static menulist_s	s_allow_exit_box;
static menulist_s	s_infinite_ammo_box;
static menulist_s	s_fixed_fov_box;
static menulist_s	s_quad_drop_box;

//ROGUE
static menulist_s	s_no_mines_box;
static menulist_s	s_no_nukes_box;
static menulist_s	s_stack_double_box;
static menulist_s	s_no_spheres_box;
//ROGUE

static void DMFlagCallback( void *self )
{
	menulist_s *f = ( menulist_s * ) self;
	int flags;
	int bit = 0;

	flags = Cvar_VariableValue( "dmflags" );

	if ( f == &s_friendlyfire_box )
	{
		if ( f->curvalue )
			flags &= ~DF_NO_FRIENDLY_FIRE;
		else
			flags |= DF_NO_FRIENDLY_FIRE;
		goto setvalue;
	}
	else if ( f == &s_falls_box )
	{
		if ( f->curvalue )
			flags &= ~DF_NO_FALLING;
		else
			flags |= DF_NO_FALLING;
		goto setvalue;
	}
	else if ( f == &s_weapons_stay_box ) 
	{
		bit = DF_WEAPONS_STAY;
	}
	else if ( f == &s_instant_powerups_box )
	{
		bit = DF_INSTANT_ITEMS;
	}
	else if ( f == &s_allow_exit_box )
	{
		bit = DF_ALLOW_EXIT;
	}
	else if ( f == &s_powerups_box )
	{
		if ( f->curvalue )
			flags &= ~DF_NO_ITEMS;
		else
			flags |= DF_NO_ITEMS;
		goto setvalue;
	}
	else if ( f == &s_health_box )
	{
		if ( f->curvalue )
			flags &= ~DF_NO_HEALTH;
		else
			flags |= DF_NO_HEALTH;
		goto setvalue;
	}
	else if ( f == &s_spawn_farthest_box )
	{
		bit = DF_SPAWN_FARTHEST;
	}
	else if ( f == &s_teamplay_box )
	{
		if ( f->curvalue == 1 )
		{
			flags |=  DF_SKINTEAMS;
			flags &= ~DF_MODELTEAMS;
		}
		else if ( f->curvalue == 2 )
		{
			flags |=  DF_MODELTEAMS;
			flags &= ~DF_SKINTEAMS;
		}
		else
		{
			flags &= ~( DF_MODELTEAMS | DF_SKINTEAMS );
		}

		goto setvalue;
	}
	else if ( f == &s_samelevel_box )
	{
		bit = DF_SAME_LEVEL;
	}
	else if ( f == &s_force_respawn_box )
	{
		bit = DF_FORCE_RESPAWN;
	}
	else if ( f == &s_armor_box )
	{
		if ( f->curvalue )
			flags &= ~DF_NO_ARMOR;
		else
			flags |= DF_NO_ARMOR;
		goto setvalue;
	}
	else if ( f == &s_infinite_ammo_box )
	{
		bit = DF_INFINITE_AMMO;
	}
	else if ( f == &s_fixed_fov_box )
	{
		bit = DF_FIXED_FOV;
	}
	else if ( f == &s_quad_drop_box )
	{
		bit = DF_QUAD_DROP;
	}

//=======
//ROGUE
	else if (Developer_searchpath(2) == 2)
	{
		if ( f == &s_no_mines_box)
		{
			bit = DF_NO_MINES;
		}
		else if ( f == &s_no_nukes_box)
		{
			bit = DF_NO_NUKES;
		}
		else if ( f == &s_stack_double_box)
		{
			bit = DF_NO_STACK_DOUBLE;
		}
		else if ( f == &s_no_spheres_box)
		{
			bit = DF_NO_SPHERES;
		}
	}
//ROGUE
//=======

	if ( f )
	{
		if ( f->curvalue == 0 )
			flags &= ~bit;
		else
			flags |= bit;
	}

setvalue:
	Cvar_SetValue ("dmflags", flags);

	Com_sprintf( dmoptions_statusbar, sizeof( dmoptions_statusbar ), "dmflags = %d", flags );

}

void DMOptions_MenuInit( void )
{
	static const char *yes_no_names[] =
	{
		"no", "yes", 0
	};
	static const char *teamplay_names[] = 
	{
		"disabled", "by skin", "by model", 0
	};
	int dmflags = Cvar_VariableValue( "dmflags" );
	int y = 0;

	s_dmoptions_menu.x = vid_so.viddef.width * 0.50;
	s_dmoptions_menu.nitems = 0;

	s_falls_box.type = MTYPE_SPINCONTROL;
	s_falls_box.x	= 0;
	s_falls_box.y	= y;
	s_falls_box.name	= "falling damage";
	s_falls_box.callback = DMFlagCallback;
	s_falls_box.itemnames = yes_no_names;
	s_falls_box.curvalue = ( dmflags & DF_NO_FALLING ) == 0;

	s_weapons_stay_box.type = MTYPE_SPINCONTROL;
	s_weapons_stay_box.x	= 0;
	s_weapons_stay_box.y	= y += 10;
	s_weapons_stay_box.name	= "weapons stay";
	s_weapons_stay_box.callback = DMFlagCallback;
	s_weapons_stay_box.itemnames = yes_no_names;
	s_weapons_stay_box.curvalue = ( dmflags & DF_WEAPONS_STAY ) != 0;

	s_instant_powerups_box.type = MTYPE_SPINCONTROL;
	s_instant_powerups_box.x	= 0;
	s_instant_powerups_box.y	= y += 10;
	s_instant_powerups_box.name	= "instant powerups";
	s_instant_powerups_box.callback = DMFlagCallback;
	s_instant_powerups_box.itemnames = yes_no_names;
	s_instant_powerups_box.curvalue = ( dmflags & DF_INSTANT_ITEMS ) != 0;

	s_powerups_box.type = MTYPE_SPINCONTROL;
	s_powerups_box.x	= 0;
	s_powerups_box.y	= y += 10;
	s_powerups_box.name	= "allow powerups";
	s_powerups_box.callback = DMFlagCallback;
	s_powerups_box.itemnames = yes_no_names;
	s_powerups_box.curvalue = ( dmflags & DF_NO_ITEMS ) == 0;

	s_health_box.type = MTYPE_SPINCONTROL;
	s_health_box.x	= 0;
	s_health_box.y	= y += 10;
	s_health_box.callback = DMFlagCallback;
	s_health_box.name	= "allow health";
	s_health_box.itemnames = yes_no_names;
	s_health_box.curvalue = ( dmflags & DF_NO_HEALTH ) == 0;

	s_armor_box.type = MTYPE_SPINCONTROL;
	s_armor_box.x	= 0;
	s_armor_box.y	= y += 10;
	s_armor_box.name	= "allow armor";
	s_armor_box.callback = DMFlagCallback;
	s_armor_box.itemnames = yes_no_names;
	s_armor_box.curvalue = ( dmflags & DF_NO_ARMOR ) == 0;

	s_spawn_farthest_box.type = MTYPE_SPINCONTROL;
	s_spawn_farthest_box.x	= 0;
	s_spawn_farthest_box.y	= y += 10;
	s_spawn_farthest_box.name	= "spawn farthest";
	s_spawn_farthest_box.callback = DMFlagCallback;
	s_spawn_farthest_box.itemnames = yes_no_names;
	s_spawn_farthest_box.curvalue = ( dmflags & DF_SPAWN_FARTHEST ) != 0;

	s_samelevel_box.type = MTYPE_SPINCONTROL;
	s_samelevel_box.x	= 0;
	s_samelevel_box.y	= y += 10;
	s_samelevel_box.name	= "same map";
	s_samelevel_box.callback = DMFlagCallback;
	s_samelevel_box.itemnames = yes_no_names;
	s_samelevel_box.curvalue = ( dmflags & DF_SAME_LEVEL ) != 0;

	s_force_respawn_box.type = MTYPE_SPINCONTROL;
	s_force_respawn_box.x	= 0;
	s_force_respawn_box.y	= y += 10;
	s_force_respawn_box.name	= "force respawn";
	s_force_respawn_box.callback = DMFlagCallback;
	s_force_respawn_box.itemnames = yes_no_names;
	s_force_respawn_box.curvalue = ( dmflags & DF_FORCE_RESPAWN ) != 0;

	s_teamplay_box.type = MTYPE_SPINCONTROL;
	s_teamplay_box.x	= 0;
	s_teamplay_box.y	= y += 10;
	s_teamplay_box.name	= "teamplay";
	s_teamplay_box.callback = DMFlagCallback;
	s_teamplay_box.itemnames = teamplay_names;

	s_allow_exit_box.type = MTYPE_SPINCONTROL;
	s_allow_exit_box.x	= 0;
	s_allow_exit_box.y	= y += 10;
	s_allow_exit_box.name	= "allow exit";
	s_allow_exit_box.callback = DMFlagCallback;
	s_allow_exit_box.itemnames = yes_no_names;
	s_allow_exit_box.curvalue = ( dmflags & DF_ALLOW_EXIT ) != 0;

	s_infinite_ammo_box.type = MTYPE_SPINCONTROL;
	s_infinite_ammo_box.x	= 0;
	s_infinite_ammo_box.y	= y += 10;
	s_infinite_ammo_box.name	= "infinite ammo";
	s_infinite_ammo_box.callback = DMFlagCallback;
	s_infinite_ammo_box.itemnames = yes_no_names;
	s_infinite_ammo_box.curvalue = ( dmflags & DF_INFINITE_AMMO ) != 0;

	s_fixed_fov_box.type = MTYPE_SPINCONTROL;
	s_fixed_fov_box.x	= 0;
	s_fixed_fov_box.y	= y += 10;
	s_fixed_fov_box.name	= "fixed FOV";
	s_fixed_fov_box.callback = DMFlagCallback;
	s_fixed_fov_box.itemnames = yes_no_names;
	s_fixed_fov_box.curvalue = ( dmflags & DF_FIXED_FOV ) != 0;

	s_quad_drop_box.type = MTYPE_SPINCONTROL;
	s_quad_drop_box.x	= 0;
	s_quad_drop_box.y	= y += 10;
	s_quad_drop_box.name	= "quad drop";
	s_quad_drop_box.callback = DMFlagCallback;
	s_quad_drop_box.itemnames = yes_no_names;
	s_quad_drop_box.curvalue = ( dmflags & DF_QUAD_DROP ) != 0;

	s_friendlyfire_box.type = MTYPE_SPINCONTROL;
	s_friendlyfire_box.x	= 0;
	s_friendlyfire_box.y	= y += 10;
	s_friendlyfire_box.name	= "friendly fire";
	s_friendlyfire_box.callback = DMFlagCallback;
	s_friendlyfire_box.itemnames = yes_no_names;
	s_friendlyfire_box.curvalue = ( dmflags & DF_NO_FRIENDLY_FIRE ) == 0;

//============
//ROGUE
	if(Developer_searchpath(2) == 2)
	{
		s_no_mines_box.type = MTYPE_SPINCONTROL;
		s_no_mines_box.x	= 0;
		s_no_mines_box.y	= y += 10;
		s_no_mines_box.name	= "remove mines";
		s_no_mines_box.callback = DMFlagCallback;
		s_no_mines_box.itemnames = yes_no_names;
		s_no_mines_box.curvalue = ( dmflags & DF_NO_MINES ) != 0;

		s_no_nukes_box.type = MTYPE_SPINCONTROL;
		s_no_nukes_box.x	= 0;
		s_no_nukes_box.y	= y += 10;
		s_no_nukes_box.name	= "remove nukes";
		s_no_nukes_box.callback = DMFlagCallback;
		s_no_nukes_box.itemnames = yes_no_names;
		s_no_nukes_box.curvalue = ( dmflags & DF_NO_NUKES ) != 0;

		s_stack_double_box.type = MTYPE_SPINCONTROL;
		s_stack_double_box.x	= 0;
		s_stack_double_box.y	= y += 10;
		s_stack_double_box.name	= "2x/4x stacking off";
		s_stack_double_box.callback = DMFlagCallback;
		s_stack_double_box.itemnames = yes_no_names;
		s_stack_double_box.curvalue = ( dmflags & DF_NO_STACK_DOUBLE ) != 0;

		s_no_spheres_box.type = MTYPE_SPINCONTROL;
		s_no_spheres_box.x	= 0;
		s_no_spheres_box.y	= y += 10;
		s_no_spheres_box.name	= "remove spheres";
		s_no_spheres_box.callback = DMFlagCallback;
		s_no_spheres_box.itemnames = yes_no_names;
		s_no_spheres_box.curvalue = ( dmflags & DF_NO_SPHERES ) != 0;

	}
//ROGUE
//============

	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_falls_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_weapons_stay_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_instant_powerups_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_powerups_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_health_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_armor_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_spawn_farthest_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_samelevel_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_force_respawn_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_teamplay_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_allow_exit_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_infinite_ammo_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_fixed_fov_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_quad_drop_box );
	qmenu.Menu_AddItem( &s_dmoptions_menu, &s_friendlyfire_box );

//=======
//ROGUE
	if(Developer_searchpath(2) == 2)
	{
		qmenu.Menu_AddItem( &s_dmoptions_menu, &s_no_mines_box );
		qmenu.Menu_AddItem( &s_dmoptions_menu, &s_no_nukes_box );
		qmenu.Menu_AddItem( &s_dmoptions_menu, &s_stack_double_box );
		qmenu.Menu_AddItem( &s_dmoptions_menu, &s_no_spheres_box );
	}
//ROGUE
//=======

	qmenu.Menu_Center( &s_dmoptions_menu );

	// set the original dmflags statusbar
	DMFlagCallback( 0 );
	Menu_SetStatusBar( &s_dmoptions_menu, dmoptions_statusbar );
}

void DMOptions_MenuDraw(void)
{
	qmenu.Menu_Draw( &s_dmoptions_menu );
}

const char *DMOptions_MenuKey( int key )
{
	return Default_MenuKey( &s_dmoptions_menu, key );
}

void M_Menu_DMOptions_f (void)
{
	DMOptions_MenuInit();
	M_PushMenu( DMOptions_MenuDraw, DMOptions_MenuKey );
}

dmoptions_statusbar = ""

s_dmoptions_menu = menuframework_s()
s_friendlyfire_box = menuspincontrol_s()
s_falls_box = menuspincontrol_s()
s_weapons_stay_box = menuspincontrol_s()
s_instant_powerups_box = menuspincontrol_s()
s_powerups_box = menuspincontrol_s()
s_health_box = menuspincontrol_s()
s_spawn_farthest_box = menuspincontrol_s()
s_teamplay_box = menuspincontrol_s()
s_samelevel_box = menuspincontrol_s()
s_force_respawn_box = menuspincontrol_s()
s_armor_box = menuspincontrol_s()
s_allow_exit_box = menuspincontrol_s()
s_infinite_ammo_box = menuspincontrol_s()
s_fixed_fov_box = menuspincontrol_s()
s_quad_drop_box = menuspincontrol_s()
s_no_mines_box = menuspincontrol_s()
s_no_nukes_box = menuspincontrol_s()
s_stack_double_box = menuspincontrol_s()
s_no_spheres_box = menuspincontrol_s()

DF_NO_MINES = getattr(q_shared, "DF_NO_MINES", 0x00020000)
DF_NO_STACK_DOUBLE = getattr(q_shared, "DF_NO_STACK_DOUBLE", 0x00040000)
DF_NO_NUKES = getattr(q_shared, "DF_NO_NUKES", 0x00080000)
DF_NO_SPHERES = getattr(q_shared, "DF_NO_SPHERES", 0x00100000)


def DMFlagCallback(self):

	global dmoptions_statusbar

	flags = int(cvar.Cvar_VariableValue("dmflags"))
	bit = 0

	if self is s_friendlyfire_box:
		if self.curvalue:
			flags &= ~q_shared.DF_NO_FRIENDLY_FIRE
		else:
			flags |= q_shared.DF_NO_FRIENDLY_FIRE
	elif self is s_falls_box:
		if self.curvalue:
			flags &= ~q_shared.DF_NO_FALLING
		else:
			flags |= q_shared.DF_NO_FALLING
	elif self is s_weapons_stay_box:
		bit = q_shared.DF_WEAPONS_STAY
	elif self is s_instant_powerups_box:
		bit = q_shared.DF_INSTANT_ITEMS
	elif self is s_allow_exit_box:
		bit = q_shared.DF_ALLOW_EXIT
	elif self is s_powerups_box:
		if self.curvalue:
			flags &= ~q_shared.DF_NO_ITEMS
		else:
			flags |= q_shared.DF_NO_ITEMS
	elif self is s_health_box:
		if self.curvalue:
			flags &= ~q_shared.DF_NO_HEALTH
		else:
			flags |= q_shared.DF_NO_HEALTH
	elif self is s_spawn_farthest_box:
		bit = q_shared.DF_SPAWN_FARTHEST
	elif self is s_teamplay_box:
		if self.curvalue == 1:
			flags |= q_shared.DF_SKINTEAMS
			flags &= ~q_shared.DF_MODELTEAMS
		elif self.curvalue == 2:
			flags |= q_shared.DF_MODELTEAMS
			flags &= ~q_shared.DF_SKINTEAMS
		else:
			flags &= ~(q_shared.DF_MODELTEAMS | q_shared.DF_SKINTEAMS)
	elif self is s_samelevel_box:
		bit = q_shared.DF_SAME_LEVEL
	elif self is s_force_respawn_box:
		bit = q_shared.DF_FORCE_RESPAWN
	elif self is s_armor_box:
		if self.curvalue:
			flags &= ~q_shared.DF_NO_ARMOR
		else:
			flags |= q_shared.DF_NO_ARMOR
	elif self is s_infinite_ammo_box:
		bit = q_shared.DF_INFINITE_AMMO
	elif self is s_fixed_fov_box:
		bit = q_shared.DF_FIXED_FOV
	elif self is s_quad_drop_box:
		bit = q_shared.DF_QUAD_DROP
	elif files.Developer_searchpath(2) == 2:
		if self is s_no_mines_box:
			bit = DF_NO_MINES
		elif self is s_no_nukes_box:
			bit = DF_NO_NUKES
		elif self is s_stack_double_box:
			bit = DF_NO_STACK_DOUBLE
		elif self is s_no_spheres_box:
			bit = DF_NO_SPHERES

	if bit:
		if self.curvalue == 0:
			flags &= ~bit
		else:
			flags |= bit

	cvar.Cvar_SetValue("dmflags", flags)
	dmoptions_statusbar = "dmflags = {}".format(flags)


def DMOptions_MenuInit():

	yes_no_names = ["no", "yes"]
	teamplay_names = ["disabled", "by skin", "by model"]
	dmflags = int(cvar.Cvar_VariableValue("dmflags"))
	y = 0

	s_dmoptions_menu.x = vid_so.viddef.width * 0.50
	s_dmoptions_menu.nitems = 0

	s_falls_box.type = MTYPE_SPINCONTROL
	s_falls_box.x = 0
	s_falls_box.y = y
	s_falls_box.name = "falling damage"
	s_falls_box.callback = DMFlagCallback
	s_falls_box.itemnames = yes_no_names
	s_falls_box.curvalue = int((dmflags & q_shared.DF_NO_FALLING) == 0)

	s_weapons_stay_box.type = MTYPE_SPINCONTROL
	s_weapons_stay_box.x = 0
	s_weapons_stay_box.y = y + 10
	s_weapons_stay_box.name = "weapons stay"
	s_weapons_stay_box.callback = DMFlagCallback
	s_weapons_stay_box.itemnames = yes_no_names
	s_weapons_stay_box.curvalue = int((dmflags & q_shared.DF_WEAPONS_STAY) != 0)

	y += 10

	s_instant_powerups_box.type = MTYPE_SPINCONTROL
	s_instant_powerups_box.x = 0
	s_instant_powerups_box.y = y + 10
	s_instant_powerups_box.name = "instant powerups"
	s_instant_powerups_box.callback = DMFlagCallback
	s_instant_powerups_box.itemnames = yes_no_names
	s_instant_powerups_box.curvalue = int((dmflags & q_shared.DF_INSTANT_ITEMS) != 0)

	y += 10

	s_powerups_box.type = MTYPE_SPINCONTROL
	s_powerups_box.x = 0
	s_powerups_box.y = y + 10
	s_powerups_box.name = "allow powerups"
	s_powerups_box.callback = DMFlagCallback
	s_powerups_box.itemnames = yes_no_names
	s_powerups_box.curvalue = int((dmflags & q_shared.DF_NO_ITEMS) == 0)

	y += 10

	s_health_box.type = MTYPE_SPINCONTROL
	s_health_box.x = 0
	s_health_box.y = y + 10
	s_health_box.callback = DMFlagCallback
	s_health_box.name = "allow health"
	s_health_box.itemnames = yes_no_names
	s_health_box.curvalue = int((dmflags & q_shared.DF_NO_HEALTH) == 0)

	y += 10

	s_armor_box.type = MTYPE_SPINCONTROL
	s_armor_box.x = 0
	s_armor_box.y = y + 10
	s_armor_box.name = "allow armor"
	s_armor_box.callback = DMFlagCallback
	s_armor_box.itemnames = yes_no_names
	s_armor_box.curvalue = int((dmflags & q_shared.DF_NO_ARMOR) == 0)

	y += 10

	s_spawn_farthest_box.type = MTYPE_SPINCONTROL
	s_spawn_farthest_box.x = 0
	s_spawn_farthest_box.y = y + 10
	s_spawn_farthest_box.name = "spawn farthest"
	s_spawn_farthest_box.callback = DMFlagCallback
	s_spawn_farthest_box.itemnames = yes_no_names
	s_spawn_farthest_box.curvalue = int((dmflags & q_shared.DF_SPAWN_FARTHEST) != 0)

	y += 10

	s_samelevel_box.type = MTYPE_SPINCONTROL
	s_samelevel_box.x = 0
	s_samelevel_box.y = y + 10
	s_samelevel_box.name = "same map"
	s_samelevel_box.callback = DMFlagCallback
	s_samelevel_box.itemnames = yes_no_names
	s_samelevel_box.curvalue = int((dmflags & q_shared.DF_SAME_LEVEL) != 0)

	y += 10

	s_force_respawn_box.type = MTYPE_SPINCONTROL
	s_force_respawn_box.x = 0
	s_force_respawn_box.y = y + 10
	s_force_respawn_box.name = "force respawn"
	s_force_respawn_box.callback = DMFlagCallback
	s_force_respawn_box.itemnames = yes_no_names
	s_force_respawn_box.curvalue = int((dmflags & q_shared.DF_FORCE_RESPAWN) != 0)

	y += 10

	s_teamplay_box.type = MTYPE_SPINCONTROL
	s_teamplay_box.x = 0
	s_teamplay_box.y = y + 10
	s_teamplay_box.name = "teamplay"
	s_teamplay_box.callback = DMFlagCallback
	s_teamplay_box.itemnames = teamplay_names
	if dmflags & q_shared.DF_SKINTEAMS:
		s_teamplay_box.curvalue = 1
	elif dmflags & q_shared.DF_MODELTEAMS:
		s_teamplay_box.curvalue = 2
	else:
		s_teamplay_box.curvalue = 0

	y += 10

	s_allow_exit_box.type = MTYPE_SPINCONTROL
	s_allow_exit_box.x = 0
	s_allow_exit_box.y = y + 10
	s_allow_exit_box.name = "allow exit"
	s_allow_exit_box.callback = DMFlagCallback
	s_allow_exit_box.itemnames = yes_no_names
	s_allow_exit_box.curvalue = int((dmflags & q_shared.DF_ALLOW_EXIT) != 0)

	y += 10

	s_infinite_ammo_box.type = MTYPE_SPINCONTROL
	s_infinite_ammo_box.x = 0
	s_infinite_ammo_box.y = y + 10
	s_infinite_ammo_box.name = "infinite ammo"
	s_infinite_ammo_box.callback = DMFlagCallback
	s_infinite_ammo_box.itemnames = yes_no_names
	s_infinite_ammo_box.curvalue = int((dmflags & q_shared.DF_INFINITE_AMMO) != 0)

	y += 10

	s_fixed_fov_box.type = MTYPE_SPINCONTROL
	s_fixed_fov_box.x = 0
	s_fixed_fov_box.y = y + 10
	s_fixed_fov_box.name = "fixed FOV"
	s_fixed_fov_box.callback = DMFlagCallback
	s_fixed_fov_box.itemnames = yes_no_names
	s_fixed_fov_box.curvalue = int((dmflags & q_shared.DF_FIXED_FOV) != 0)

	y += 10

	s_quad_drop_box.type = MTYPE_SPINCONTROL
	s_quad_drop_box.x = 0
	s_quad_drop_box.y = y + 10
	s_quad_drop_box.name = "quad drop"
	s_quad_drop_box.callback = DMFlagCallback
	s_quad_drop_box.itemnames = yes_no_names
	s_quad_drop_box.curvalue = int((dmflags & q_shared.DF_QUAD_DROP) != 0)

	y += 10

	s_friendlyfire_box.type = MTYPE_SPINCONTROL
	s_friendlyfire_box.x = 0
	s_friendlyfire_box.y = y + 10
	s_friendlyfire_box.name = "friendly fire"
	s_friendlyfire_box.callback = DMFlagCallback
	s_friendlyfire_box.itemnames = yes_no_names
	s_friendlyfire_box.curvalue = int((dmflags & q_shared.DF_NO_FRIENDLY_FIRE) == 0)

	if files.Developer_searchpath(2) == 2:
		s_no_mines_box.type = MTYPE_SPINCONTROL
		s_no_mines_box.x = 0
		s_no_mines_box.y = y + 20
		s_no_mines_box.name = "remove mines"
		s_no_mines_box.callback = DMFlagCallback
		s_no_mines_box.itemnames = yes_no_names
		s_no_mines_box.curvalue = int((dmflags & DF_NO_MINES) != 0)

		s_no_nukes_box.type = MTYPE_SPINCONTROL
		s_no_nukes_box.x = 0
		s_no_nukes_box.y = y + 30
		s_no_nukes_box.name = "remove nukes"
		s_no_nukes_box.callback = DMFlagCallback
		s_no_nukes_box.itemnames = yes_no_names
		s_no_nukes_box.curvalue = int((dmflags & DF_NO_NUKES) != 0)

		s_stack_double_box.type = MTYPE_SPINCONTROL
		s_stack_double_box.x = 0
		s_stack_double_box.y = y + 40
		s_stack_double_box.name = "2x/4x stacking off"
		s_stack_double_box.callback = DMFlagCallback
		s_stack_double_box.itemnames = yes_no_names
		s_stack_double_box.curvalue = int((dmflags & DF_NO_STACK_DOUBLE) != 0)

		s_no_spheres_box.type = MTYPE_SPINCONTROL
		s_no_spheres_box.x = 0
		s_no_spheres_box.y = y + 50
		s_no_spheres_box.name = "remove spheres"
		s_no_spheres_box.callback = DMFlagCallback
		s_no_spheres_box.itemnames = yes_no_names
		s_no_spheres_box.curvalue = int((dmflags & DF_NO_SPHERES) != 0)

	qmenu.Menu_AddItem(s_dmoptions_menu, s_falls_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_weapons_stay_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_instant_powerups_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_powerups_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_health_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_armor_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_spawn_farthest_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_samelevel_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_force_respawn_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_teamplay_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_allow_exit_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_infinite_ammo_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_fixed_fov_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_quad_drop_box)
	qmenu.Menu_AddItem(s_dmoptions_menu, s_friendlyfire_box)

	if files.Developer_searchpath(2) == 2:
		qmenu.Menu_AddItem(s_dmoptions_menu, s_no_mines_box)
		qmenu.Menu_AddItem(s_dmoptions_menu, s_no_nukes_box)
		qmenu.Menu_AddItem(s_dmoptions_menu, s_stack_double_box)
		qmenu.Menu_AddItem(s_dmoptions_menu, s_no_spheres_box)

	qmenu.Menu_Center(s_dmoptions_menu)

	DMFlagCallback(s_falls_box)
	qmenu.Menu_SetStatusBar(s_dmoptions_menu, dmoptions_statusbar)


def DMOptions_MenuDraw():

	qmenu.Menu_Draw(s_dmoptions_menu)


def DMOptions_MenuKey(key): #int (returns const char *)

	return Default_MenuKey(s_dmoptions_menu, key)


def M_Menu_DMOptions_f():

	DMOptions_MenuInit()
	M_PushMenu(DMOptions_MenuDraw, DMOptions_MenuKey)

"""
"""
s_downloadoptions_menu = menuframework_s()
s_download_title = menuseparator_s()
s_allow_download_box = menuspincontrol_s()
s_allow_download_maps_box = menuspincontrol_s()
s_allow_download_models_box = menuspincontrol_s()
s_allow_download_players_box = menuspincontrol_s()
s_allow_download_sounds_box = menuspincontrol_s()


def DownloadCallback(self):

	if self is s_allow_download_box:
		cvar.Cvar_SetValue("allow_download", int(self.curvalue))
	elif self is s_allow_download_maps_box:
		cvar.Cvar_SetValue("allow_download_maps", int(self.curvalue))
	elif self is s_allow_download_models_box:
		cvar.Cvar_SetValue("allow_download_models", int(self.curvalue))
	elif self is s_allow_download_players_box:
		cvar.Cvar_SetValue("allow_download_players", int(self.curvalue))
	elif self is s_allow_download_sounds_box:
		cvar.Cvar_SetValue("allow_download_sounds", int(self.curvalue))


def DownloadOptions_MenuInit():

	yes_no_names = ["no", "yes"]
	y = 0

	s_downloadoptions_menu.x = vid_so.viddef.width * 0.50
	s_downloadoptions_menu.nitems = 0

	s_download_title.type = MTYPE_SEPARATOR
	s_download_title.name = "Download Options"
	s_download_title.x = 48
	s_download_title.y = y

	s_allow_download_box.type = MTYPE_SPINCONTROL
	s_allow_download_box.x = 0
	s_allow_download_box.y = y + 20
	s_allow_download_box.name = "allow downloading"
	s_allow_download_box.callback = DownloadCallback
	s_allow_download_box.itemnames = yes_no_names
	s_allow_download_box.curvalue = int(cvar.Cvar_VariableValue("allow_download") != 0)

	y += 20

	s_allow_download_maps_box.type = MTYPE_SPINCONTROL
	s_allow_download_maps_box.x = 0
	s_allow_download_maps_box.y = y + 20
	s_allow_download_maps_box.name = "maps"
	s_allow_download_maps_box.callback = DownloadCallback
	s_allow_download_maps_box.itemnames = yes_no_names
	s_allow_download_maps_box.curvalue = int(cvar.Cvar_VariableValue("allow_download_maps") != 0)

	y += 20

	s_allow_download_players_box.type = MTYPE_SPINCONTROL
	s_allow_download_players_box.x = 0
	s_allow_download_players_box.y = y + 10
	s_allow_download_players_box.name = "player models/skins"
	s_allow_download_players_box.callback = DownloadCallback
	s_allow_download_players_box.itemnames = yes_no_names
	s_allow_download_players_box.curvalue = int(cvar.Cvar_VariableValue("allow_download_players") != 0)

	y += 10

	s_allow_download_models_box.type = MTYPE_SPINCONTROL
	s_allow_download_models_box.x = 0
	s_allow_download_models_box.y = y + 10
	s_allow_download_models_box.name = "models"
	s_allow_download_models_box.callback = DownloadCallback
	s_allow_download_models_box.itemnames = yes_no_names
	s_allow_download_models_box.curvalue = int(cvar.Cvar_VariableValue("allow_download_models") != 0)

	y += 10

	s_allow_download_sounds_box.type = MTYPE_SPINCONTROL
	s_allow_download_sounds_box.x = 0
	s_allow_download_sounds_box.y = y + 10
	s_allow_download_sounds_box.name = "sounds"
	s_allow_download_sounds_box.callback = DownloadCallback
	s_allow_download_sounds_box.itemnames = yes_no_names
	s_allow_download_sounds_box.curvalue = int(cvar.Cvar_VariableValue("allow_download_sounds") != 0)

	qmenu.Menu_AddItem(s_downloadoptions_menu, s_download_title)
	qmenu.Menu_AddItem(s_downloadoptions_menu, s_allow_download_box)
	qmenu.Menu_AddItem(s_downloadoptions_menu, s_allow_download_maps_box)
	qmenu.Menu_AddItem(s_downloadoptions_menu, s_allow_download_players_box)
	qmenu.Menu_AddItem(s_downloadoptions_menu, s_allow_download_models_box)
	qmenu.Menu_AddItem(s_downloadoptions_menu, s_allow_download_sounds_box)

	qmenu.Menu_Center(s_downloadoptions_menu)

	if s_downloadoptions_menu.cursor == 0:
		s_downloadoptions_menu.cursor = 1


def DownloadOptions_MenuDraw():

	qmenu.Menu_Draw(s_downloadoptions_menu)


def DownloadOptions_MenuKey(key): #int (returns const char *)

	return Default_MenuKey(s_downloadoptions_menu, key)


def M_Menu_DownloadOptions_f():

	DownloadOptions_MenuInit()
	M_PushMenu(DownloadOptions_MenuDraw, DownloadOptions_MenuKey)

/*
=============================================================================

DOWNLOADOPTIONS BOOK MENU

=============================================================================
*/
static menuframework_s s_downloadoptions_menu;

static menuseparator_s	s_download_title;
static menulist_s	s_allow_download_box;
static menulist_s	s_allow_download_maps_box;
static menulist_s	s_allow_download_models_box;
static menulist_s	s_allow_download_players_box;
static menulist_s	s_allow_download_sounds_box;

static void DownloadCallback( void *self )
{
	menulist_s *f = ( menulist_s * ) self;

	if (f == &s_allow_download_box)
	{
		Cvar_SetValue("allow_download", f->curvalue);
	}

	else if (f == &s_allow_download_maps_box)
	{
		Cvar_SetValue("allow_download_maps", f->curvalue);
	}

	else if (f == &s_allow_download_models_box)
	{
		Cvar_SetValue("allow_download_models", f->curvalue);
	}

	else if (f == &s_allow_download_players_box)
	{
		Cvar_SetValue("allow_download_players", f->curvalue);
	}

	else if (f == &s_allow_download_sounds_box)
	{
		Cvar_SetValue("allow_download_sounds", f->curvalue);
	}
}

void DownloadOptions_MenuInit( void )
{
	static const char *yes_no_names[] =
	{
		"no", "yes", 0
	};
	int y = 0;

	s_downloadoptions_menu.x = vid_so.viddef.width * 0.50;
	s_downloadoptions_menu.nitems = 0;

	s_download_title.type = MTYPE_SEPARATOR;
	s_download_title.name = "Download Options";
	s_download_title.x    = 48;
	s_download_title.y	 = y;

	s_allow_download_box.type = MTYPE_SPINCONTROL;
	s_allow_download_box.x	= 0;
	s_allow_download_box.y	= y += 20;
	s_allow_download_box.name	= "allow downloading";
	s_allow_download_box.callback = DownloadCallback;
	s_allow_download_box.itemnames = yes_no_names;
	s_allow_download_box.curvalue = (Cvar_VariableValue("allow_download") != 0);

	s_allow_download_maps_box.type = MTYPE_SPINCONTROL;
	s_allow_download_maps_box.x	= 0;
	s_allow_download_maps_box.y	= y += 20;
	s_allow_download_maps_box.name	= "maps";
	s_allow_download_maps_box.callback = DownloadCallback;
	s_allow_download_maps_box.itemnames = yes_no_names;
	s_allow_download_maps_box.curvalue = (Cvar_VariableValue("allow_download_maps") != 0);

	s_allow_download_players_box.type = MTYPE_SPINCONTROL;
	s_allow_download_players_box.x	= 0;
	s_allow_download_players_box.y	= y += 10;
	s_allow_download_players_box.name	= "player models/skins";
	s_allow_download_players_box.callback = DownloadCallback;
	s_allow_download_players_box.itemnames = yes_no_names;
	s_allow_download_players_box.curvalue = (Cvar_VariableValue("allow_download_players") != 0);

	s_allow_download_models_box.type = MTYPE_SPINCONTROL;
	s_allow_download_models_box.x	= 0;
	s_allow_download_models_box.y	= y += 10;
	s_allow_download_models_box.name	= "models";
	s_allow_download_models_box.callback = DownloadCallback;
	s_allow_download_models_box.itemnames = yes_no_names;
	s_allow_download_models_box.curvalue = (Cvar_VariableValue("allow_download_models") != 0);

	s_allow_download_sounds_box.type = MTYPE_SPINCONTROL;
	s_allow_download_sounds_box.x	= 0;
	s_allow_download_sounds_box.y	= y += 10;
	s_allow_download_sounds_box.name	= "sounds";
	s_allow_download_sounds_box.callback = DownloadCallback;
	s_allow_download_sounds_box.itemnames = yes_no_names;
	s_allow_download_sounds_box.curvalue = (Cvar_VariableValue("allow_download_sounds") != 0);

	qmenu.Menu_AddItem( &s_downloadoptions_menu, &s_download_title );
	qmenu.Menu_AddItem( &s_downloadoptions_menu, &s_allow_download_box );
	qmenu.Menu_AddItem( &s_downloadoptions_menu, &s_allow_download_maps_box );
	qmenu.Menu_AddItem( &s_downloadoptions_menu, &s_allow_download_players_box );
	qmenu.Menu_AddItem( &s_downloadoptions_menu, &s_allow_download_models_box );
	qmenu.Menu_AddItem( &s_downloadoptions_menu, &s_allow_download_sounds_box );

	qmenu.Menu_Center( &s_downloadoptions_menu );

	// skip over title
	if (s_downloadoptions_menu.cursor == 0)
		s_downloadoptions_menu.cursor = 1;
}

void DownloadOptions_MenuDraw(void)
{
	qmenu.Menu_Draw( &s_downloadoptions_menu );
}

const char *DownloadOptions_MenuKey( int key )
{
	return Default_MenuKey( &s_downloadoptions_menu, key );
}

void M_Menu_DownloadOptions_f (void)
{
	DownloadOptions_MenuInit();
	M_PushMenu( DownloadOptions_MenuDraw, DownloadOptions_MenuKey );
}
/*
=============================================================================

ADDRESS BOOK MENU

=============================================================================
*/
#define NUM_ADDRESSBOOK_ENTRIES 9

static menuframework_s	s_addressbook_menu;
static menufield_s		s_addressbook_fields[NUM_ADDRESSBOOK_ENTRIES];

void AddressBook_MenuInit( void )
{
	int i;

	s_addressbook_menu.x = vid_so.viddef.width / 2 - 142;
	s_addressbook_menu.y = vid_so.viddef.height / 2 - 58;
	s_addressbook_menu.nitems = 0;

	for ( i = 0; i < NUM_ADDRESSBOOK_ENTRIES; i++ )
	{
		cvar_t *adr;
		char buffer[20];

		Com_sprintf( buffer, sizeof( buffer ), "adr%d", i );

		adr = Cvar_Get( buffer, "", q_shared.CVAR_ARCHIVE );

		s_addressbook_fields[i].type = MTYPE_FIELD;
		s_addressbook_fields[i].name = 0;
		s_addressbook_fields[i].callback = 0;
		s_addressbook_fields[i].x		= 0;
		s_addressbook_fields[i].y		= i * 18 + 0;
		s_addressbook_fields[i].localdata[0] = i;
		s_addressbook_fields[i].cursor			= 0;
		s_addressbook_fields[i].length			= 60;
		s_addressbook_fields[i].visible_length	= 30;

		strcpy( s_addressbook_fields[i].buffer, adr->string );

		qmenu.Menu_AddItem( &s_addressbook_menu, &s_addressbook_fields[i] );
	}
}

const char *AddressBook_MenuKey( int key )
{
	if ( key == K_ESCAPE )
	{
		int index;
		char buffer[20];

		for ( index = 0; index < NUM_ADDRESSBOOK_ENTRIES; index++ )
		{
			Com_sprintf( buffer, sizeof( buffer ), "adr%d", index );
			Cvar_Set( buffer, s_addressbook_fields[index].buffer );
		}
	}
	return Default_MenuKey( &s_addressbook_menu, key );
}

void AddressBook_MenuDraw(void)
{
	M_Banner( "m_banner_addressbook" );
	qmenu.Menu_Draw( &s_addressbook_menu );
}

void M_Menu_AddressBook_f(void)
{
	AddressBook_MenuInit();
	M_PushMenu( AddressBook_MenuDraw, AddressBook_MenuKey );
}

NUM_ADDRESSBOOK_ENTRIES = 9

s_addressbook_menu = menuframework_s()
s_addressbook_fields = [menufield_s() for _ in range(NUM_ADDRESSBOOK_ENTRIES)]


def AddressBook_MenuInit():

	s_addressbook_menu.x = vid_so.viddef.width // 2 - 142
	s_addressbook_menu.y = vid_so.viddef.height // 2 - 58
	s_addressbook_menu.nitems = 0

	for i in range(NUM_ADDRESSBOOK_ENTRIES):
		adr_name = "adr{}".format(i)
		adr = cvar.Cvar_Get(adr_name, "", q_shared.CVAR_ARCHIVE)

		field = s_addressbook_fields[i]
		field.type = MTYPE_FIELD
		field.name = None
		field.callback = None
		field.x = 0
		field.y = i * 18 + 0
		field.localdata[0] = i
		field.cursor = 0
		field.length = 60
		field.visible_length = 30
		field.visible_offset = 0
		field.buffer = adr.string if adr is not None else ""

		qmenu.Menu_AddItem(s_addressbook_menu, field)


def AddressBook_MenuKey(key): #int (returns const char *)

	if key == keys.K_ESCAPE:
		for index in range(NUM_ADDRESSBOOK_ENTRIES):
			adr_name = "adr{}".format(index)
			cvar.Cvar_Set(adr_name, s_addressbook_fields[index].buffer)

	return Default_MenuKey(s_addressbook_menu, key)


def AddressBook_MenuDraw():

	M_Banner("m_banner_addressbook")
	qmenu.Menu_Draw(s_addressbook_menu)


def M_Menu_AddressBook_f():

	AddressBook_MenuInit()
	M_PushMenu(AddressBook_MenuDraw, AddressBook_MenuKey)

MAX_DISPLAYNAME = 16
MAX_PLAYERMODELS = 1024


class PlayerModelInfo(object):

	def __init__(self):
		self.nskins = 0
		self.skindisplaynames = []
		self.displayname = ""
		self.directory = ""


s_player_config_menu = menuframework_s()
s_player_name_field = menufield_s()
s_player_model_box = menuspincontrol_s()
s_player_skin_box = menuspincontrol_s()
s_player_handedness_box = menuspincontrol_s()
s_player_rate_box = menuspincontrol_s()
s_player_skin_title = menuseparator_s()
s_player_model_title = menuseparator_s()
s_player_hand_title = menuseparator_s()
s_player_rate_title = menuseparator_s()
s_player_download_action = menuaction_s()

s_pmi = []
s_pmnames = []
s_numplayermodels = 0
player_config_yaw = 0

rate_tbl = [2500, 3200, 5000, 10000, 25000, 0]
rate_names = [
	"28.8 Modem",
	"33.6 Modem",
	"Single ISDN",
	"Dual ISDN/Cable",
	"T1/LAN",
	"User defined",
]


def DownloadOptionsFunc(unused):

	M_Menu_DownloadOptions_f()


def HandednessCallback(unused):

	cvar.Cvar_SetValue("hand", s_player_handedness_box.curvalue)


def RateCallback(unused):

	if s_player_rate_box.curvalue != len(rate_tbl) - 1:
		cvar.Cvar_SetValue("rate", rate_tbl[s_player_rate_box.curvalue])


def ModelCallback(unused):

	s_player_skin_box.itemnames = s_pmi[s_player_model_box.curvalue].skindisplaynames
	s_player_skin_box.curvalue = 0


def FreeFileList(list_in):

	if not list_in:
		return
	list_in.clear()


def IconOfSkinExists(skin, pcxfiles):

	base = os.path.basename(skin)
	root, _ext = os.path.splitext(base)
	icon = root + "_i.pcx"
	for name in pcxfiles:
		if os.path.basename(name) == icon:
			return True
	return False


def PlayerConfig_ScanDirectories():

	global s_pmi, s_numplayermodels

	s_pmi = []
	s_numplayermodels = 0

	path = None
	dirnames = None
	while True:
		path = files.FS_NextPath(path)
		if path is None:
			break
		findname = os.path.join(path, "players", "*.*")
		dirnames = files.FS_ListFiles(findname, q_shared.SFF_SUBDIR, 0)
		if dirnames:
			break

	if not dirnames:
		return False

	npms = min(len(dirnames), MAX_PLAYERMODELS)

	for dirname in dirnames[:npms]:
		if not dirname:
			continue

		tris_path = os.path.join(dirname, "tris.md2")
		if not os.path.exists(tris_path):
			continue

		pcxnames = files.FS_ListFiles(
			os.path.join(dirname, "*.pcx"),
			0,
			q_shared.SFF_SUBDIR | q_shared.SFF_HIDDEN | q_shared.SFF_SYSTEM,
		)
		if not pcxnames:
			continue

		valid_skins = []
		for pcxname in pcxnames:
			if "_i.pcx" in pcxname:
				continue
			if IconOfSkinExists(pcxname, pcxnames):
				valid_skins.append(pcxname)

		if not valid_skins:
			continue

		skinnames = []
		for pcxname in valid_skins:
			base = os.path.basename(pcxname)
			name = os.path.splitext(base)[0]
			skinnames.append(name)

		info = PlayerModelInfo()
		info.nskins = len(skinnames)
		info.skindisplaynames = skinnames

		base_dir = os.path.basename(dirname.rstrip("/\\"))
		info.displayname = base_dir[: MAX_DISPLAYNAME - 1]
		info.directory = base_dir

		s_pmi.append(info)

	s_numplayermodels = len(s_pmi)
	return s_numplayermodels > 0


def _pm_sort_key(info):

	directory = info.directory.lower()
	if directory == "male":
		return (0, directory)
	if directory == "female":
		return (1, directory)
	return (2, directory)


def PlayerConfig_MenuInit():

	global s_pmnames

	name_var = cvar.Cvar_Get("name", "unnamed", q_shared.CVAR_USERINFO | q_shared.CVAR_ARCHIVE)
	skin_var = cvar.Cvar_Get("skin", "male/grunt", q_shared.CVAR_USERINFO | q_shared.CVAR_ARCHIVE)
	hand_var = cvar.Cvar_Get("hand", "0", q_shared.CVAR_USERINFO | q_shared.CVAR_ARCHIVE)

	handedness = ["right", "left", "center"]

	if not PlayerConfig_ScanDirectories():
		return False

	if hand_var.value < 0 or hand_var.value > 2:
		cvar.Cvar_SetValue("hand", 0)

	currentdirectory = skin_var.string
	currentskin = ""
	if "/" in currentdirectory:
		currentdirectory, currentskin = currentdirectory.split("/", 1)
	elif "\\" in currentdirectory:
		currentdirectory, currentskin = currentdirectory.split("\\", 1)
	else:
		currentdirectory = "male"
		currentskin = "grunt"

	s_pmi.sort(key=_pm_sort_key)

	s_pmnames = []
	currentdirectoryindex = 0
	currentskinindex = 0
	for i, info in enumerate(s_pmi):
		s_pmnames.append(info.displayname)
		if q_shared.Q_stricmp(info.directory, currentdirectory) == 0:
			currentdirectoryindex = i
			for j, skin_name in enumerate(info.skindisplaynames):
				if q_shared.Q_stricmp(skin_name, currentskin) == 0:
					currentskinindex = j
					break

	s_player_config_menu.x = vid_so.viddef.width // 2 - 95
	s_player_config_menu.y = vid_so.viddef.height // 2 - 97
	s_player_config_menu.nitems = 0

	s_player_name_field.type = MTYPE_FIELD
	s_player_name_field.name = "name"
	s_player_name_field.callback = None
	s_player_name_field.x = 0
	s_player_name_field.y = 0
	s_player_name_field.length = 20
	s_player_name_field.visible_length = 20
	s_player_name_field.buffer = name_var.string
	s_player_name_field.cursor = len(name_var.string)

	s_player_model_title.type = MTYPE_SEPARATOR
	s_player_model_title.name = "model"
	s_player_model_title.x = -8
	s_player_model_title.y = 60

	s_player_model_box.type = MTYPE_SPINCONTROL
	s_player_model_box.x = -56
	s_player_model_box.y = 70
	s_player_model_box.callback = ModelCallback
	s_player_model_box.cursor_offset = -48
	s_player_model_box.curvalue = currentdirectoryindex
	s_player_model_box.itemnames = s_pmnames

	s_player_skin_title.type = MTYPE_SEPARATOR
	s_player_skin_title.name = "skin"
	s_player_skin_title.x = -16
	s_player_skin_title.y = 84

	s_player_skin_box.type = MTYPE_SPINCONTROL
	s_player_skin_box.x = -56
	s_player_skin_box.y = 94
	s_player_skin_box.name = None
	s_player_skin_box.callback = None
	s_player_skin_box.cursor_offset = -48
	s_player_skin_box.curvalue = currentskinindex
	s_player_skin_box.itemnames = s_pmi[currentdirectoryindex].skindisplaynames

	s_player_hand_title.type = MTYPE_SEPARATOR
	s_player_hand_title.name = "handedness"
	s_player_hand_title.x = 32
	s_player_hand_title.y = 108

	s_player_handedness_box.type = MTYPE_SPINCONTROL
	s_player_handedness_box.x = -56
	s_player_handedness_box.y = 118
	s_player_handedness_box.name = None
	s_player_handedness_box.cursor_offset = -48
	s_player_handedness_box.callback = HandednessCallback
	s_player_handedness_box.curvalue = cvar.Cvar_VariableValue("hand")
	s_player_handedness_box.itemnames = handedness

	rate_index = len(rate_tbl) - 1
	for i in range(len(rate_tbl) - 1):
		if cvar.Cvar_VariableValue("rate") == rate_tbl[i]:
			rate_index = i
			break

	s_player_rate_title.type = MTYPE_SEPARATOR
	s_player_rate_title.name = "connect speed"
	s_player_rate_title.x = 56
	s_player_rate_title.y = 156

	s_player_rate_box.type = MTYPE_SPINCONTROL
	s_player_rate_box.x = -56
	s_player_rate_box.y = 166
	s_player_rate_box.name = None
	s_player_rate_box.cursor_offset = -48
	s_player_rate_box.callback = RateCallback
	s_player_rate_box.curvalue = rate_index
	s_player_rate_box.itemnames = rate_names

	s_player_download_action.type = MTYPE_ACTION
	s_player_download_action.name = "download options"
	s_player_download_action.flags = QMF_LEFT_JUSTIFY
	s_player_download_action.x = -24
	s_player_download_action.y = 186
	s_player_download_action.statusbar = None
	s_player_download_action.callback = DownloadOptionsFunc

	qmenu.Menu_AddItem(s_player_config_menu, s_player_name_field)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_model_title)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_model_box)
	if s_player_skin_box.itemnames:
		qmenu.Menu_AddItem(s_player_config_menu, s_player_skin_title)
		qmenu.Menu_AddItem(s_player_config_menu, s_player_skin_box)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_hand_title)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_handedness_box)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_rate_title)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_rate_box)
	qmenu.Menu_AddItem(s_player_config_menu, s_player_download_action)

	return True


def PlayerConfig_MenuDraw():

	global player_config_yaw

	refdef = ref.refdef_t()
	refdef.x = vid_so.viddef.width // 2
	refdef.y = vid_so.viddef.height // 2 - 72
	refdef.width = 144
	refdef.height = 168
	refdef.fov_x = 40
	refdef.fov_y = cl_view.CalcFov(refdef.fov_x, refdef.width, refdef.height)
	refdef.time = cl_main.cls.realtime * 0.001

	if s_pmi[s_player_model_box.curvalue].skindisplaynames:
		entity = ref.entity_t()
		model_dir = s_pmi[s_player_model_box.curvalue].directory
		skin_name = s_pmi[s_player_model_box.curvalue].skindisplaynames[s_player_skin_box.curvalue]

		model_path = "players/{}/tris.md2".format(model_dir)
		skin_path = "players/{}/{}.pcx".format(model_dir, skin_name)

		entity.model = vid_so.re.RegisterModel(model_path)
		entity.skin = vid_so.re.RegisterSkin(skin_path)
		entity.flags = q_shared.RF_FULLBRIGHT
		entity.origin[0] = 80
		entity.origin[1] = 0
		entity.origin[2] = 0
		q_shared.VectorCopy(entity.origin, entity.oldorigin)
		entity.frame = 0
		entity.oldframe = 0
		entity.backlerp = 0.0
		entity.angles[1] = player_config_yaw
		player_config_yaw += 1
		if player_config_yaw > 360:
			player_config_yaw -= 360

		refdef.areabits = None
		refdef.num_entities = 1
		refdef.entities = [entity]
		refdef.lightstyles = None
		refdef.rdflags = q_shared.RDF_NOWORLDMODEL

		qmenu.Menu_Draw(s_player_config_menu)

		x = int(refdef.x * (320.0 / vid_so.viddef.width) - 8)
		y = int((vid_so.viddef.height / 2) * (240.0 / vid_so.viddef.height) - 77)
		M_DrawTextBox(x, y, refdef.width // 8, refdef.height // 8)
		refdef.height += 4

		vid_so.re.RenderFrame(refdef)

		icon_path = "/players/{}/{}_i.pcx".format(model_dir, skin_name)
		vid_so.re.DrawPic(s_player_config_menu.x - 40, refdef.y, icon_path)


def PlayerConfig_MenuKey(key): #int (returns const char *)

	if key == keys.K_ESCAPE:
		name_var = cvar.Cvar_Get("name", "unnamed", q_shared.CVAR_USERINFO | q_shared.CVAR_ARCHIVE)
		skin_var = cvar.Cvar_Get("skin", "male/grunt", q_shared.CVAR_USERINFO | q_shared.CVAR_ARCHIVE)

		cvar.Cvar_Set("name", s_player_name_field.buffer)

		model_dir = s_pmi[s_player_model_box.curvalue].directory
		skin_name = s_pmi[s_player_model_box.curvalue].skindisplaynames[s_player_skin_box.curvalue]
		skin_value = "{}/{}".format(model_dir, skin_name)
		cvar.Cvar_Set("skin", skin_value)

		name_var.modified = True
		skin_var.modified = True

		for info in s_pmi:
			info.skindisplaynames = []
			info.nskins = 0

	return Default_MenuKey(s_player_config_menu, key)


def M_Menu_PlayerConfig_f():

	if not PlayerConfig_MenuInit():
		qmenu.Menu_SetStatusBar(s_multiplayer_menu, "No valid player models found")
		return
	qmenu.Menu_SetStatusBar(s_multiplayer_menu, None)
	M_PushMenu(PlayerConfig_MenuDraw, PlayerConfig_MenuKey)

/*
=============================================================================

PLAYER CONFIG MENU

=============================================================================
*/
static menuframework_s	s_player_config_menu;
static menufield_s		s_player_name_field;
static menulist_s		s_player_model_box;
static menulist_s		s_player_skin_box;
static menulist_s		s_player_handedness_box;
static menulist_s		s_player_rate_box;
static menuseparator_s	s_player_skin_title;
static menuseparator_s	s_player_model_title;
static menuseparator_s	s_player_hand_title;
static menuseparator_s	s_player_rate_title;
static menuaction_s		s_player_download_action;

#define MAX_DISPLAYNAME 16
#define MAX_PLAYERMODELS 1024

typedef struct
{
	int		nskins;
	char	**skindisplaynames;
	char	displayname[MAX_DISPLAYNAME];
	char	directory[MAX_QPATH];
} playermodelinfo_s;

static playermodelinfo_s s_pmi[MAX_PLAYERMODELS];
static char *s_pmnames[MAX_PLAYERMODELS];
static int s_numplayermodels;

static int rate_tbl[] = { 2500, 3200, 5000, 10000, 25000, 0 };
static const char *rate_names[] = { "28.8 Modem", "33.6 Modem", "Single ISDN",
	"Dual ISDN/Cable", "T1/LAN", "User defined", 0 };

void DownloadOptionsFunc( void *self )
{
	M_Menu_DownloadOptions_f();
}

static void HandednessCallback( void *unused )
{
	Cvar_SetValue( "hand", s_player_handedness_box.curvalue );
}

static void RateCallback( void *unused )
{
	if (s_player_rate_box.curvalue != sizeof(rate_tbl) / sizeof(*rate_tbl) - 1)
		Cvar_SetValue( "rate", rate_tbl[s_player_rate_box.curvalue] );
}

static void ModelCallback( void *unused )
{
	s_player_skin_box.itemnames = s_pmi[s_player_model_box.curvalue].skindisplaynames;
	s_player_skin_box.curvalue = 0;
}

static void FreeFileList( char **list, int n )
{
	int i;

	for ( i = 0; i < n; i++ )
	{
		if ( list[i] )
		{
			free( list[i] );
			list[i] = 0;
		}
	}
	free( list );
}

static qboolean IconOfSkinExists( char *skin, char **pcxfiles, int npcxfiles )
{
	int i;
	char scratch[1024];

	strcpy( scratch, skin );
	*strrchr( scratch, '.' ) = 0;
	strcat( scratch, "_i.pcx" );

	for ( i = 0; i < npcxfiles; i++ )
	{
		if ( strcmp( pcxfiles[i], scratch ) == 0 )
			return true;
	}

	return false;
}

static qboolean PlayerConfig_ScanDirectories( void )
{
	char findname[1024];
	char scratch[1024];
	int ndirs = 0, npms = 0;
	char **dirnames;
	char *path = NULL;
	int i;

	extern char **FS_ListFiles( char *, int *, unsigned, unsigned );

	s_numplayermodels = 0;

	/*
	** get a list of directories
	*/
	do 
	{
		path = FS_NextPath( path );
		Com_sprintf( findname, sizeof(findname), "%s/players/*.*", path );

		if ( ( dirnames = FS_ListFiles( findname, &ndirs, SFF_SUBDIR, 0 ) ) != 0 )
			break;
	} while ( path );

	if ( !dirnames )
		return false;

	/*
	** go through the subdirectories
	*/
	npms = ndirs;
	if ( npms > MAX_PLAYERMODELS )
		npms = MAX_PLAYERMODELS;

	for ( i = 0; i < npms; i++ )
	{
		int k, s;
		char *a, *b, *c;
		char **pcxnames;
		char **skinnames;
		int npcxfiles;
		int nskins = 0;

		if ( dirnames[i] == 0 )
			continue;

		// verify the existence of tris.md2
		strcpy( scratch, dirnames[i] );
		strcat( scratch, "/tris.md2" );
		if ( !Sys_FindFirst( scratch, 0, SFF_SUBDIR | SFF_HIDDEN | SFF_SYSTEM ) )
		{
			free( dirnames[i] );
			dirnames[i] = 0;
			Sys_FindClose();
			continue;
		}
		Sys_FindClose();

		// verify the existence of at least one pcx skin
		strcpy( scratch, dirnames[i] );
		strcat( scratch, "/*.pcx" );
		pcxnames = FS_ListFiles( scratch, &npcxfiles, 0, SFF_SUBDIR | SFF_HIDDEN | SFF_SYSTEM );

		if ( !pcxnames )
		{
			free( dirnames[i] );
			dirnames[i] = 0;
			continue;
		}

		// count valid skins, which consist of a skin with a matching "_i" icon
		for ( k = 0; k < npcxfiles-1; k++ )
		{
			if ( !strstr( pcxnames[k], "_i.pcx" ) )
			{
				if ( IconOfSkinExists( pcxnames[k], pcxnames, npcxfiles - 1 ) )
				{
					nskins++;
				}
			}
		}
		if ( !nskins )
			continue;

		skinnames = malloc( sizeof( char * ) * ( nskins + 1 ) );
		memset( skinnames, 0, sizeof( char * ) * ( nskins + 1 ) );

		// copy the valid skins
		for ( s = 0, k = 0; k < npcxfiles-1; k++ )
		{
			char *a, *b, *c;

			if ( !strstr( pcxnames[k], "_i.pcx" ) )
			{
				if ( IconOfSkinExists( pcxnames[k], pcxnames, npcxfiles - 1 ) )
				{
					a = strrchr( pcxnames[k], '/' );
					b = strrchr( pcxnames[k], '\\' );

					if ( a > b )
						c = a;
					else
						c = b;

					strcpy( scratch, c + 1 );

					if ( strrchr( scratch, '.' ) )
						*strrchr( scratch, '.' ) = 0;

					skinnames[s] = strdup( scratch );
					s++;
				}
			}
		}

		// at this point we have a valid player model
		s_pmi[s_numplayermodels].nskins = nskins;
		s_pmi[s_numplayermodels].skindisplaynames = skinnames;

		// make short name for the model
		a = strrchr( dirnames[i], '/' );
		b = strrchr( dirnames[i], '\\' );

		if ( a > b )
			c = a;
		else
			c = b;

		strncpy( s_pmi[s_numplayermodels].displayname, c + 1, MAX_DISPLAYNAME-1 );
		strcpy( s_pmi[s_numplayermodels].directory, c + 1 );

		FreeFileList( pcxnames, npcxfiles );

		s_numplayermodels++;
	}
	if ( dirnames )
		FreeFileList( dirnames, ndirs );
}

static int pmicmpfnc( const void *_a, const void *_b )
{
	const playermodelinfo_s *a = ( const playermodelinfo_s * ) _a;
	const playermodelinfo_s *b = ( const playermodelinfo_s * ) _b;

	/*
	** sort by male, female, then alphabetical
	*/
	if ( strcmp( a->directory, "male" ) == 0 )
		return -1;
	else if ( strcmp( b->directory, "male" ) == 0 )
		return 1;

	if ( strcmp( a->directory, "female" ) == 0 )
		return -1;
	else if ( strcmp( b->directory, "female" ) == 0 )
		return 1;

	return strcmp( a->directory, b->directory );
}


qboolean PlayerConfig_MenuInit( void )
{
	extern cvar_t *name;
	extern cvar_t *team;
	extern cvar_t *skin;
	char currentdirectory[1024];
	char currentskin[1024];
	int i = 0;

	int currentdirectoryindex = 0;
	int currentskinindex = 0;

	cvar_t *hand = Cvar_Get( "hand", "0", CVAR_USERINFO | q_shared.CVAR_ARCHIVE );

	static const char *handedness[] = { "right", "left", "center", 0 };

	PlayerConfig_ScanDirectories();

	if (s_numplayermodels == 0)
		return false;

	if ( hand->value < 0 || hand->value > 2 )
		Cvar_SetValue( "hand", 0 );

	strcpy( currentdirectory, skin->string );

	if ( strchr( currentdirectory, '/' ) )
	{
		strcpy( currentskin, strchr( currentdirectory, '/' ) + 1 );
		*strchr( currentdirectory, '/' ) = 0;
	}
	else if ( strchr( currentdirectory, '\\' ) )
	{
		strcpy( currentskin, strchr( currentdirectory, '\\' ) + 1 );
		*strchr( currentdirectory, '\\' ) = 0;
	}
	else
	{
		strcpy( currentdirectory, "male" );
		strcpy( currentskin, "grunt" );
	}

	qsort( s_pmi, s_numplayermodels, sizeof( s_pmi[0] ), pmicmpfnc );

	memset( s_pmnames, 0, sizeof( s_pmnames ) );
	for ( i = 0; i < s_numplayermodels; i++ )
	{
		s_pmnames[i] = s_pmi[i].displayname;
		if ( Q_stricmp( s_pmi[i].directory, currentdirectory ) == 0 )
		{
			int j;

			currentdirectoryindex = i;

			for ( j = 0; j < s_pmi[i].nskins; j++ )
			{
				if ( Q_stricmp( s_pmi[i].skindisplaynames[j], currentskin ) == 0 )
				{
					currentskinindex = j;
					break;
				}
			}
		}
	}

	s_player_config_menu.x = vid_so.viddef.width / 2 - 95; 
	s_player_config_menu.y = vid_so.viddef.height / 2 - 97;
	s_player_config_menu.nitems = 0;

	s_player_name_field.type = MTYPE_FIELD;
	s_player_name_field.name = "name";
	s_player_name_field.callback = 0;
	s_player_name_field.x		= 0;
	s_player_name_field.y		= 0;
	s_player_name_field.length	= 20;
	s_player_name_field.visible_length = 20;
	strcpy( s_player_name_field.buffer, name->string );
	s_player_name_field.cursor = strlen( name->string );

	s_player_model_title.type = MTYPE_SEPARATOR;
	s_player_model_title.name = "model";
	s_player_model_title.x    = -8;
	s_player_model_title.y	 = 60;

	s_player_model_box.type = MTYPE_SPINCONTROL;
	s_player_model_box.x	= -56;
	s_player_model_box.y	= 70;
	s_player_model_box.callback = ModelCallback;
	s_player_model_box.cursor_offset = -48;
	s_player_model_box.curvalue = currentdirectoryindex;
	s_player_model_box.itemnames = s_pmnames;

	s_player_skin_title.type = MTYPE_SEPARATOR;
	s_player_skin_title.name = "skin";
	s_player_skin_title.x    = -16;
	s_player_skin_title.y	 = 84;

	s_player_skin_box.type = MTYPE_SPINCONTROL;
	s_player_skin_box.x	= -56;
	s_player_skin_box.y	= 94;
	s_player_skin_box.name	= 0;
	s_player_skin_box.callback = 0;
	s_player_skin_box.cursor_offset = -48;
	s_player_skin_box.curvalue = currentskinindex;
	s_player_skin_box.itemnames = s_pmi[currentdirectoryindex].skindisplaynames;

	s_player_hand_title.type = MTYPE_SEPARATOR;
	s_player_hand_title.name = "handedness";
	s_player_hand_title.x    = 32;
	s_player_hand_title.y	 = 108;

	s_player_handedness_box.type = MTYPE_SPINCONTROL;
	s_player_handedness_box.x	= -56;
	s_player_handedness_box.y	= 118;
	s_player_handedness_box.name	= 0;
	s_player_handedness_box.cursor_offset = -48;
	s_player_handedness_box.callback = HandednessCallback;
	s_player_handedness_box.curvalue = Cvar_VariableValue( "hand" );
	s_player_handedness_box.itemnames = handedness;

	for (i = 0; i < sizeof(rate_tbl) / sizeof(*rate_tbl) - 1; i++)
		if (Cvar_VariableValue("rate") == rate_tbl[i])
			break;

	s_player_rate_title.type = MTYPE_SEPARATOR;
	s_player_rate_title.name = "connect speed";
	s_player_rate_title.x    = 56;
	s_player_rate_title.y	 = 156;

	s_player_rate_box.type = MTYPE_SPINCONTROL;
	s_player_rate_box.x	= -56;
	s_player_rate_box.y	= 166;
	s_player_rate_box.name	= 0;
	s_player_rate_box.cursor_offset = -48;
	s_player_rate_box.callback = RateCallback;
	s_player_rate_box.curvalue = i;
	s_player_rate_box.itemnames = rate_names;

	s_player_download_action.type = MTYPE_ACTION;
	s_player_download_action.name	= "download options";
	s_player_download_action.flags= QMF_LEFT_JUSTIFY;
	s_player_download_action.x	= -24;
	s_player_download_action.y	= 186;
	s_player_download_action.statusbar = NULL;
	s_player_download_action.callback = DownloadOptionsFunc;

	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_name_field );
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_model_title );
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_model_box );
	if ( s_player_skin_box.itemnames )
	{
		qmenu.Menu_AddItem( &s_player_config_menu, &s_player_skin_title );
		qmenu.Menu_AddItem( &s_player_config_menu, &s_player_skin_box );
	}
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_hand_title );
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_handedness_box );
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_rate_title );
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_rate_box );
	qmenu.Menu_AddItem( &s_player_config_menu, &s_player_download_action );

	return true;
}

void PlayerConfig_MenuDraw( void )
{
	extern float CalcFov( float fov_x, float w, float h );
	refdef_t refdef;
	char scratch[MAX_QPATH];

	memset( &refdef, 0, sizeof( refdef ) );

	refdef.x = vid_so.viddef.width / 2;
	refdef.y = vid_so.viddef.height / 2 - 72;
	refdef.width = 144;
	refdef.height = 168;
	refdef.fov_x = 40;
	refdef.fov_y = CalcFov( refdef.fov_x, refdef.width, refdef.height );
	refdef.time = cl_main.cls.realtime*0.001;

	if ( s_pmi[s_player_model_box.curvalue].skindisplaynames )
	{
		static int yaw;
		int maxframe = 29;
		entity_t entity;

		memset( &entity, 0, sizeof( entity ) );

		Com_sprintf( scratch, sizeof( scratch ), "players/%s/tris.md2", s_pmi[s_player_model_box.curvalue].directory );
		entity.model = vid_so.re.RegisterModel( scratch );
		Com_sprintf( scratch, sizeof( scratch ), "players/%s/%s.pcx", s_pmi[s_player_model_box.curvalue].directory, s_pmi[s_player_model_box.curvalue].skindisplaynames[s_player_skin_box.curvalue] );
		entity.skin = vid_so.re.RegisterSkin( scratch );
		entity.flags = RF_FULLBRIGHT;
		entity.origin[0] = 80;
		entity.origin[1] = 0;
		entity.origin[2] = 0;
		q_shared.VectorCopy( entity.origin, entity.oldorigin );
		entity.frame = 0;
		entity.oldframe = 0;
		entity.backlerp = 0.0;
		entity.angles[1] = yaw++;
		if ( ++yaw > 360 )
			yaw -= 360;

		refdef.areabits = 0;
		refdef.num_entities = 1;
		refdef.entities = &entity;
		refdef.lightstyles = 0;
		refdef.rdflags = RDF_NOWORLDMODEL;

		qmenu.Menu_Draw( &s_player_config_menu );

		M_DrawTextBox( ( refdef.x ) * ( 320.0F / vid_so.viddef.width ) - 8, ( vid_so.viddef.height / 2 ) * ( 240.0F / vid_so.viddef.height) - 77, refdef.width / 8, refdef.height / 8 );
		refdef.height += 4;

		vid_so.re.RenderFrame( &refdef );

		Com_sprintf( scratch, sizeof( scratch ), "/players/%s/%s_i.pcx", 
			s_pmi[s_player_model_box.curvalue].directory,
			s_pmi[s_player_model_box.curvalue].skindisplaynames[s_player_skin_box.curvalue] );
		vid_so.re.DrawPic( s_player_config_menu.x - 40, refdef.y, scratch );
	}
}

const char *PlayerConfig_MenuKey (int key)
{
	int i;

	if ( key == K_ESCAPE )
	{
		char scratch[1024];

		Cvar_Set( "name", s_player_name_field.buffer );

		Com_sprintf( scratch, sizeof( scratch ), "%s/%s", 
			s_pmi[s_player_model_box.curvalue].directory, 
			s_pmi[s_player_model_box.curvalue].skindisplaynames[s_player_skin_box.curvalue] );

		Cvar_Set( "skin", scratch );

		for ( i = 0; i < s_numplayermodels; i++ )
		{
			int j;

			for ( j = 0; j < s_pmi[i].nskins; j++ )
			{
				if ( s_pmi[i].skindisplaynames[j] )
					free( s_pmi[i].skindisplaynames[j] );
				s_pmi[i].skindisplaynames[j] = 0;
			}
			free( s_pmi[i].skindisplaynames );
			s_pmi[i].skindisplaynames = 0;
			s_pmi[i].nskins = 0;
		}
	}
	return Default_MenuKey( &s_player_config_menu, key );
}


void M_Menu_PlayerConfig_f (void)
{
	if (!PlayerConfig_MenuInit())
	{
		Menu_SetStatusBar( &s_multiplayer_menu, "No valid player models found" );
		return;
	}
	Menu_SetStatusBar( &s_multiplayer_menu, NULL );
	M_PushMenu( PlayerConfig_MenuDraw, PlayerConfig_MenuKey );
}


/*
=======================================================================

GALLERY MENU

=======================================================================
*/
#if 0
void M_Menu_Gallery_f( void )
{
	extern void Gallery_MenuDraw( void );
	extern const char *Gallery_MenuKey( int key );

	M_PushMenu( Gallery_MenuDraw, Gallery_MenuKey );
}
#endif

/*
=======================================================================

QUIT MENU

=======================================================================
"""

def M_Quit_Key (key): #int (returns const char *)

	if key in [keys.K_ESCAPE, ord('n'), ord('N')]:
		M_PopMenu ()
	elif key in [ord('Y'), ord('y')]:
		cl_main.cls.key_dest = client.keydest_t.key_console
		cl_main.CL_Quit_f ()

	return None

def M_Quit_Draw ():

	#int		w, h;

	w, h = vid_so.re.DrawGetPicSize ("quit")
	vid_so.re.DrawPic ( (vid_so.viddef.width-w)//2, (vid_so.viddef.height-h)//2, "quit")

def M_Menu_Quit_f ():

	M_PushMenu (M_Quit_Draw, M_Quit_Key)

"""


//=============================================================================
/* Menu Subsystem */


/*
=================
M_Init
=================
"""
def M_Init ():

	cmd.Cmd_AddCommand ("menu_main", M_Menu_Main_f)
	cmd.Cmd_AddCommand ("menu_game", M_Menu_Game_f)
	if 1: #Keep indent as in original c code
		cmd.Cmd_AddCommand ("menu_loadgame", M_Menu_LoadGame_f)
		cmd.Cmd_AddCommand ("menu_savegame", M_Menu_SaveGame_f)
		#cmd.Cmd_AddCommand ("menu_joinserver", M_Menu_JoinServer_f)
		#	cmd.Cmd_AddCommand ("menu_addressbook", M_Menu_AddressBook_f)
		#cmd.Cmd_AddCommand ("menu_startserver", M_Menu_StartServer_f)
		#	cmd.Cmd_AddCommand ("menu_dmoptions", M_Menu_DMOptions_f)
		#cmd.Cmd_AddCommand ("menu_playerconfig", M_Menu_PlayerConfig_f)
		#	cmd.Cmd_AddCommand ("menu_downloadoptions", M_Menu_DownloadOptions_f)
		cmd.Cmd_AddCommand ("menu_credits", M_Menu_Credits_f )
	cmd.Cmd_AddCommand ("menu_multiplayer", M_Menu_Multiplayer_f )
	cmd.Cmd_AddCommand ("menu_video", M_Menu_Video_f)
	cmd.Cmd_AddCommand ("menu_options", M_Menu_Options_f)
	if 1:
		cmd.Cmd_AddCommand ("menu_keys", M_Menu_Keys_f)
	cmd.Cmd_AddCommand ("menu_quit", M_Menu_Quit_f)



"""
=================
M_Draw
=================
"""
def M_Draw ():

	global m_entersound

	if cl_main.cls.key_dest != client.keydest_t.key_menu:
		return

	# repaint everything next frame
	cl_scrn.SCR_DirtyScreen ()

	# dim everything behind it down
	if cl_main.cl.cinematictime > 0:
		vid_so.re.DrawFill (0,0,vid_so.viddef.width, vid_so.viddef.height, 0)
	else:
		vid_so.re.DrawFadeScreen ()

	m_drawfunc ()

	# delay playing the enter sound until after the
	# menu has been drawn, to avoid delay while
	# caching images
	if m_entersound:
	
		snd_dma.S_StartLocalSound( menu_in_sound )
		m_entersound = False
	



"""
=================
M_Keydown
=================
"""
def M_Keydown (key): #int

	#const char *s;

	if m_keyfunc is not None:
		s = m_keyfunc( key )
		if s is not None:
			snd_dma.S_StartLocalSound( s )

