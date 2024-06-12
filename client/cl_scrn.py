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
from qcommon import cvar, cmd, qcommon, common
from client import console, cl_main, client, menu, cl_cin, snd_dma, cl_view
from linux import q_shlinux, vid_so, cd_linux
from game import q_shared
"""
// cl_scrn.c -- master for refresh, status bar, console, chat, notify, etc

/*

  full screen console
  put up loading plaque
  blanked background with loading plaque
  blanked background with menu
  cinematics
  full screen image for quit and victory

  end of unit intermissions

  */

#include "client.h"
"""

class vrect_t(object):

	def __init__(self):
		self.x = 0
		self.y = 0
		self.width = 0
		self.height = 0

scr_con_current = 0.0 #float, aproaches scr_conlines at scr_conspeed
scr_conlines = 0.0 #float, 0.0 to 1.0 lines of console to display

scr_initialized = False # qboolean, ready to draw
scr_draw_loading = 0 #int

scr_vrect = vrect_t() #position of render window on screen

scr_viewsize = None #cvar_t		*
scr_conspeed = None #cvar_t		*
scr_centertime = None #cvar_t		*
scr_showturtle = None #cvar_t		*
scr_showpause = None #cvar_t		*
scr_printspeed = None #cvar_t		*

scr_netgraph = None #cvar_t		*
scr_timegraph = None #cvar_t		*
scr_debuggraph = None #cvar_t		*
scr_graphheight = None #cvar_t		*
scr_graphscale = None #cvar_t		*
scr_graphshift = None #cvar_t		*
scr_drawall = None #cvar_t		*


class dirty_t(object):

	def __init__(self):
		self.x1 = 0
		self.y1 = 0
		self.x2 = 0
		self.y2 = 0


scr_dirty = dirty_t()
scr_old_dirty = [dirty_t(), dirty_t()]
"""
char		crosshair_pic[MAX_QPATH];
int			crosshair_width, crosshair_height;

void SCR_TimeRefresh_f (void);
void SCR_Loading_f (void);


/*
===============================================================================

BAR GRAPHS

===============================================================================
*/

/*
==============
CL_AddNetgraph

A new packet was just parsed
==============
"""
def CL_AddNetgraph ():

	pass
	"""

	int		i;
	int		in;
	int		ping;

	// if using the debuggraph for something else, don't
	// add the net lines
	if (scr_debuggraph->value || scr_timegraph->value)
		return;

	for (i=0 ; i<cl_main.cls.netchan.dropped ; i++)
		SCR_DebugGraph (30, 0x40);

	for (i=0 ; i<cl_main.cl.surpressCount ; i++)
		SCR_DebugGraph (30, 0xdf);

	// see what the latency was on this packet
	in = cl_main.cls.netchan.incoming_acknowledged & (CMD_BACKUP-1);
	ping = cl_main.cls.realtime - cl_main.cl.cmd_time[in];
	ping /= 30;
	if (ping > 30)
		ping = 30;
	SCR_DebugGraph (ping, 0xd0);



typedef struct
{
	float	value;
	int		color;
} graphsamp_t;

static	int			current;
static	graphsamp_t	values[1024];

/*
==============
SCR_DebugGraph
==============
*/
void SCR_DebugGraph (float value, int color)
{
	values[current&1023].value = value;
	values[current&1023].color = color;
	current++;
}

/*
==============
SCR_DrawDebugGraph
==============
*/
void SCR_DrawDebugGraph (void)
{
	int		a, x, y, w, i, h;
	float	v;
	int		color;

	//
	// draw the graph
	//
	w = scr_vrect.width;

	x = scr_vrect.x;
	y = scr_vrect.y+scr_vrect.height;
	vid_so.re.DrawFill (x, y-scr_graphheight->value,
		w, scr_graphheight->value, 8);

	for (a=0 ; a<w ; a++)
	{
		i = (current-1-a+1024) & 1023;
		v = values[i].value;
		color = values[i].color;
		v = v*scr_graphscale->value + scr_graphshift->value;
		
		if (v < 0)
			v += scr_graphheight->value * (1+(int)(-v/scr_graphheight->value));
		h = (int)v % (int)scr_graphheight->value;
		vid_so.re.DrawFill (x+w-1-a, y - h, 1,	h, color);
	}
}

/*
===============================================================================

CENTER PRINTING

===============================================================================
*/

char		scr_centerstring[1024];
float		scr_centertime_start;	// for slow victory printing
float		scr_centertime_off;
int			scr_center_lines;
int			scr_erase_center;

/*
==============
SCR_CenterPrint

Called for important messages that should stay in the center of the screen
for a few moments
==============
*/
void SCR_CenterPrint (char *str)
{
	char	*s;
	char	line[64];
	int		i, j, l;

	strncpy (scr_centerstring, str, sizeof(scr_centerstring)-1);
	scr_centertime_off = scr_centertime->value;
	scr_centertime_start = cl_main.cl.time;

	// count the number of lines for centering
	scr_center_lines = 1;
	s = str;
	while (*s)
	{
		if (*s == '\n')
			scr_center_lines++;
		s++;
	}

	// echo it to the console
	Com_Printf("\n\n\35\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\37\n\n");

	s = str;
	do	
	{
	// scan the width of the line
		for (l=0 ; l<40 ; l++)
			if (s[l] == '\n' || !s[l])
				break;
		for (i=0 ; i<(40-l)/2 ; i++)
			line[i] = ' ';

		for (j=0 ; j<l ; j++)
		{
			line[i++] = s[j];
		}

		line[i] = '\n';
		line[i+1] = 0;

		Com_Printf ("%s", line);

		while (*s && *s != '\n')
			s++;

		if (!*s)
			break;
		s++;		// skip the \n
	} while (1);
	Com_Printf("\n\n\35\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\36\37\n\n");
	Con_ClearNotify ();
}


void SCR_DrawCenterString (void)
{
	char	*start;
	int		l;
	int		j;
	int		x, y;
	int		remaining;

// the finale prints the characters one at a time
	remaining = 9999;

	scr_erase_center = 0;
	start = scr_centerstring;

	if (scr_center_lines <= 4)
		y = vid_so.viddef.height*0.35;
	else
		y = 48;

	do	
	{
	// scan the width of the line
		for (l=0 ; l<40 ; l++)
			if (start[l] == '\n' || !start[l])
				break;
		x = (vid_so.viddef.width - l*8)/2;
		SCR_AddDirtyPoint (x, y);
		for (j=0 ; j<l ; j++, x+=8)
		{
			vid_so.re.DrawChar (x, y, start[j]);	
			if (!remaining--)
				return;
		}
		SCR_AddDirtyPoint (x, y+8);
			
		y += 8;

		while (*start && *start != '\n')
			start++;

		if (!*start)
			break;
		start++;		// skip the \n
	} while (1);
}

void SCR_CheckDrawCenterString (void)
{
	scr_centertime_off -= cl_main.cls.frametime;
	
	if (scr_centertime_off <= 0)
		return;

	SCR_DrawCenterString ();
}

//=============================================================================

/*
=================
SCR_CalcVrect

Sets scr_vrect, the coordinates of the rendered window
=================
"""
def SCR_CalcVrect ():
	
	global scr_vrect
	"""
	int		size;
	"""

	# bound viewsize
	if scr_viewsize.value < 40:
		Cvar_Set ("viewsize","40")
	if scr_viewsize.value > 100:
		Cvar_Set ("viewsize","100")

	size = int(scr_viewsize.value)

	scr_vrect.width = vid_so.viddef.width*size//100
	scr_vrect.width &= ~7

	scr_vrect.height = vid_so.viddef.height*size//100
	scr_vrect.height &= ~1

	scr_vrect.x = (vid_so.viddef.width - scr_vrect.width)//2
	scr_vrect.y = (vid_so.viddef.height - scr_vrect.height)//2



"""
=================
SCR_SizeUp_f

Keybinding command
=================
"""
def SCR_SizeUp_f ():

	cvar.Cvar_SetValue ("viewsize", scr_viewsize.value+10)


"""
=================
SCR_SizeDown_f

Keybinding command
=================
"""
def SCR_SizeDown_f ():

	cvar.Cvar_SetValue ("viewsize",scr_viewsize.value-10)


"""
=================
SCR_Sky_f

Set a specific sky and rotation speed
=================
"""
def SCR_Sky_f ():

	#float	rotate;
	#vec3_t	axis;

	pass
	"""
	if (Cmd_Argc() < 2)
	{
		Com_Printf ("Usage: sky <basename> <rotate> <axis x y z>\n");
		return;
	}
	if (Cmd_Argc() > 2)
		rotate = atof(Cmd_Argv(2));
	else
		rotate = 0;
	if (Cmd_Argc() == 6)
	{
		axis[0] = atof(Cmd_Argv(3));
		axis[1] = atof(Cmd_Argv(4));
		axis[2] = atof(Cmd_Argv(5));
	}
	else
	{
		axis[0] = 0;
		axis[1] = 0;
		axis[2] = 1;
	}

	vid_so.re.SetSky (Cmd_Argv(1), rotate, axis);
	"""

"""
//============================================================================

/*
==================
SCR_Init
==================
"""
def SCR_Init ():

	global scr_initialized
	global scr_viewsize, scr_conspeed, scr_centertime, scr_showturtle, scr_showpause, scr_printspeed
	global scr_netgraph, scr_timegraph, scr_debuggraph, scr_graphheight, scr_graphscale, scr_graphshift, scr_drawall

	scr_viewsize = cvar.Cvar_Get ("viewsize", "100", q_shared.CVAR_ARCHIVE)
	scr_conspeed = cvar.Cvar_Get ("scr_conspeed", "3", 0)
	scr_showturtle = cvar.Cvar_Get ("scr_showturtle", "0", 0)
	scr_showpause = cvar.Cvar_Get ("scr_showpause", "1", 0)
	scr_centertime = cvar.Cvar_Get ("scr_centertime", "2.5", 0)
	scr_printspeed = cvar.Cvar_Get ("scr_printspeed", "8", 0)
	scr_netgraph = cvar.Cvar_Get ("netgraph", "0", 0)
	scr_timegraph = cvar.Cvar_Get ("timegraph", "0", 0)
	scr_debuggraph = cvar.Cvar_Get ("debuggraph", "0", 0)
	scr_graphheight = cvar.Cvar_Get ("graphheight", "32", 0)
	scr_graphscale = cvar.Cvar_Get ("graphscale", "1", 0)
	scr_graphshift = cvar.Cvar_Get ("graphshift", "0", 0)
	scr_drawall = cvar.Cvar_Get ("scr_drawall", "0", 0)

	#
	# register our commands
	#
	cmd.Cmd_AddCommand ("timerefresh",SCR_TimeRefresh_f)
	cmd.Cmd_AddCommand ("loading",SCR_Loading_f)
	cmd.Cmd_AddCommand ("sizeup",SCR_SizeUp_f)
	cmd.Cmd_AddCommand ("sizedown",SCR_SizeDown_f)
	cmd.Cmd_AddCommand ("sky",SCR_Sky_f)

	scr_initialized = True

"""
==============
SCR_DrawNet
==============
*/
void SCR_DrawNet (void)
{
	if (cl_main.cls.netchan.outgoing_sequence - cl_main.cls.netchan.incoming_acknowledged 
		< CMD_BACKUP-1)
		return;

	vid_so.re.DrawPic (scr_vrect.x+64, scr_vrect.y, "net");
}

/*
==============
SCR_DrawPause
==============
*/
void SCR_DrawPause (void)
{
	int		w, h;

	if (!scr_showpause->value)		// turn off for screenshots
		return;

	if (!cl_paused->value)
		return;

	vid_so.re.DrawGetPicSize (&w, &h, "pause");
	vid_so.re.DrawPic ((vid_so.viddef.width-w)/2, vid_so.viddef.height/2 + 8, "pause");
}

/*
==============
SCR_DrawLoading
==============
"""
def SCR_DrawLoading ():

	global scr_draw_loading

	#int		w, h;

	if scr_draw_loading == 0:
		return

	scr_draw_loading = 0
	w, h = vid_so.re.DrawGetPicSize ("loading")
	vid_so.re.DrawPic ((vid_so.viddef.width-w)//2, (vid_so.viddef.height-h)//2, "loading")


"""
//=============================================================================

/*
==================
SCR_RunConsole

Scroll it up or down
==================
"""
def SCR_RunConsole ():
	global scr_conlines, scr_con_current

	# decide on the height of the console
	if cl_main.cls.key_dest == client.keydest_t.key_console:
		scr_conlines = 0.5		# half screen
	else:
		scr_conlines = 0				# none visible
	
	if scr_conlines < scr_con_current:
	
		scr_con_current -= scr_conspeed.value*cl_main.cls.frametime
		if scr_conlines > scr_con_current:
			scr_con_current = scr_conlines

	
	elif scr_conlines > scr_con_current:
	
		scr_con_current += scr_conspeed.value*cl_main.cls.frametime
		if scr_conlines < scr_con_current:
			scr_con_current = scr_conlines
	

"""
==================
SCR_DrawConsole
==================
"""
def SCR_DrawConsole ():

	global scr_con_current

	console.Con_CheckResize ()

	if cl_main.cls.state == client.connstate_t.ca_disconnected or cl_main.cls.state == client.connstate_t.ca_connecting:
		# forced full screen console
		console.Con_DrawConsole (1.0)
		return
	

	if cl_main.cls.state != client.connstate_t.ca_active or not cl_main.cl.refresh_prepped:
		# connected, but can't render
		console.Con_DrawConsole (0.5)
		vid_so.re.DrawFill (0, vid_so.viddef.height//2, vid_so.viddef.width, vid_so.viddef.height//2, 0)
		return
	

	if scr_con_current:
	
		console.Con_DrawConsole (scr_con_current)
	
	else:
	
		if cl_main.cls.key_dest == client.keydest_t.key_game or cl_main.cls.key_dest == client.keydest_t.key_message:
			console.Con_DrawNotify ()	# only draw notify in game
	


"""
//=============================================================================

================
SCR_BeginLoadingPlaque
================
"""
def SCR_BeginLoadingPlaque ():

	global scr_draw_loading

	snd_dma.S_StopAllSounds ()
	cl_main.cl.sound_prepped = False		# don't play ambients
	cd_linux.CDAudio_Stop ()
	if cl_main.cls.disable_screen:
		return
	if common.developer.value:
		return
	if cl_main.cls.state == client.connstate_t.ca_disconnected:
		return	# if at console, don't bring up the plaque
	if cl_main.cls.key_dest == client.keydest_t.key_console:
		return

	if cl_main.cl.cinematictime > 0:
		scr_draw_loading = 2	# clear to black first
	else:
		scr_draw_loading = 1

	SCR_UpdateScreen ()
	cl_main.cls.disable_screen = q_shlinux.Sys_Milliseconds ()
	#cl_main.cls.disable_servercount = cl_main.cl.servercount;


"""
================
SCR_EndLoadingPlaque
================
"""
def SCR_EndLoadingPlaque ():

	cl_main.cls.disable_screen = 0
	console.Con_ClearNotify ()

"""
================
SCR_Loading_f
================
"""
def SCR_Loading_f ():

	SCR_BeginLoadingPlaque ()


"""
================
SCR_TimeRefresh_f
================
"""
def entitycmpfnc( a, b )-> int: #(const entity_t *, const entity_t *)

	#
	# all other models are sorted by model then skin
	#

	amid = id(a.model)
	bmid = id(b.model)

	if amid == bmid:
		
		aid = id(a.skin)
		bid = id(b.skin)
		if aid == bid: return 0

		if aid > bid: return 1
		return -1
	
	else:
		if amid > bmid: return 1
		return -1

def SCR_TimeRefresh_f ():

	#int		i;
	#int		start, stop;
	#float	time;
	pass
	"""
	if ( cl_main.cls.state != ca_active )
		return;

	start = q_shlinux.Sys_Milliseconds ();

	if (Cmd_Argc() == 2)
	{	// run without page flipping
		vid_so.re.BeginFrame( 0 );
		for (i=0 ; i<128 ; i++)
		{
			cl_main.cl.refdef.viewangles[1] = i/128.0*360.0;
			vid_so.re.RenderFrame (&cl_main.cl.refdef);
		}
		vid_so.re.EndFrame();
	}
	else
	{
		for (i=0 ; i<128 ; i++)
		{
			cl_main.cl.refdef.viewangles[1] = i/128.0*360.0;

			vid_so.re.BeginFrame( 0 );
			vid_so.re.RenderFrame (&cl_main.cl.refdef);
			vid_so.re.EndFrame();
		}
	}

	stop = q_shlinux.Sys_Milliseconds ();
	time = (stop-start)/1000.0;
	Com_Printf ("%f seconds (%f fps)\n", time, 128/time);
"""

"""
=================
SCR_AddDirtyPoint
=================
"""
def SCR_AddDirtyPoint (x, y):

	global scr_dirty
	
	if x < scr_dirty.x1:
		scr_dirty.x1 = x
	if x > scr_dirty.x2:
		scr_dirty.x2 = x
	if y < scr_dirty.y1:
		scr_dirty.y1 = y
	if y > scr_dirty.y2:
		scr_dirty.y2 = y

def SCR_DirtyScreen ():

	SCR_AddDirtyPoint (0, 0)
	SCR_AddDirtyPoint (vid_so.viddef.width-1, vid_so.viddef.height-1)


"""
==============
SCR_TileClear

Clear any parts of the tiled background that were drawn on last frame
==============
"""
def SCR_TileClear ():

	global scr_vrect
	"""
	int		i;
	int		top, bottom, left, right;
	dirty_t	clear;
	"""

	global scr_drawall, scr_con_current

	if int(scr_drawall.value):
		SCR_DirtyScreen ()	# for power vr or broken page flippers...

	if scr_con_current == 1.0:
		return		# full screen console
	if scr_viewsize.value == 100:
		return		# full screen rendering
	if cl_main.cl.cinematictime > 0:
		return		# full screen cinematic

	# erase rect will be the union of the past three frames
	# so triple buffering works properly
	clear = copy.copy(scr_dirty)
	for i in range(2):
	
		if scr_old_dirty[i].x1 < clear.x1:
			clear.x1 = scr_old_dirty[i].x1
		if scr_old_dirty[i].x2 > clear.x2:
			clear.x2 = scr_old_dirty[i].x2
		if scr_old_dirty[i].y1 < clear.y1:
			clear.y1 = scr_old_dirty[i].y1
		if scr_old_dirty[i].y2 > clear.y2:
			clear.y2 = scr_old_dirty[i].y2

	scr_old_dirty[1] = scr_old_dirty[0]
	scr_old_dirty[0] = scr_dirty

	scr_dirty.x1 = 9999
	scr_dirty.x2 = -9999
	scr_dirty.y1 = 9999
	scr_dirty.y2 = -9999

	# don't bother with anything convered by the console)
	top = scr_con_current*vid_so.viddef.height
	if top >= clear.y1:
		clear.y1 = top;

	if clear.y2 <= clear.y1:
		return		# nothing disturbed

	top = scr_vrect.y
	bottom = top + scr_vrect.height-1
	left = scr_vrect.x
	right = left + scr_vrect.width-1

	if clear.y1 < top:
		# clear above view screen
		i = min(clear.y2, top-1)
		vid_so.re.DrawTileClear (clear.x1 , clear.y1,
			clear.x2 - clear.x1 + 1, i - clear.y1+1, "backtile")
		clear.y1 = top
	
	if clear.y2 > bottom:
		# clear below view screen
		i = max(clear.y1, bottom+1)
		vid_so.re.DrawTileClear (clear.x1, i,
			clear.x2-clear.x1+1, clear.y2-i+1, "backtile")
		clear.y2 = bottom
	
	if clear.x1 < left:
		# clear left of view screen
		i = min(clear.x2, left-1)
		vid_so.re.DrawTileClear (clear.x1, clear.y1,
			i-clear.x1+1, clear.y2 - clear.y1 + 1, "backtile")
		clear.x1 = left
	
	if clear.x2 > right:
		# clear left of view screen
		i = max(clear.x1, right+1)
		vid_so.re.DrawTileClear (i, clear.y1,
			clear.x2-i+1, clear.y2 - clear.y1 + 1, "backtile")
		clear.x2 = right
	



"""
//===============================================================


#define STAT_MINUS		10	// num frame for '-' stats digit
char		*sb_nums[2][11] = 
{
	{"num_0", "num_1", "num_2", "num_3", "num_4", "num_5",
	"num_6", "num_7", "num_8", "num_9", "num_minus"},
	{"anum_0", "anum_1", "anum_2", "anum_3", "anum_4", "anum_5",
	"anum_6", "anum_7", "anum_8", "anum_9", "anum_minus"}
};

#define	ICON_WIDTH	24
#define	ICON_HEIGHT	24
#define	CHAR_WIDTH	16
#define	ICON_SPACE	8



/*
================
SizeHUDString

Allow embedded \n in the string
================
*/
void SizeHUDString (char *string, int *w, int *h)
{
	int		lines, width, current;

	lines = 1;
	width = 0;

	current = 0;
	while (*string)
	{
		if (*string == '\n')
		{
			lines++;
			current = 0;
		}
		else
		{
			current++;
			if (current > width)
				width = current;
		}
		string++;
	}

	*w = width * 8;
	*h = lines * 8;
}

void DrawHUDString (char *string, int x, int y, int centerwidth, int xor)
{
	int		margin;
	char	line[1024];
	int		width;
	int		i;

	margin = x;

	while (*string)
	{
		// scan out one line of text from the string
		width = 0;
		while (*string && *string != '\n')
			line[width++] = *string++;
		line[width] = 0;

		if (centerwidth)
			x = margin + (centerwidth - width*8)/2;
		else
			x = margin;
		for (i=0 ; i<width ; i++)
		{
			vid_so.re.DrawChar (x, y, line[i]^xor);
			x += 8;
		}
		if (*string)
		{
			string++;	// skip the \n
			x = margin;
			y += 8;
		}
	}
}


/*
==============
SCR_DrawField
==============
*/
void SCR_DrawField (int x, int y, int color, int width, int value)
{
	char	num[16], *ptr;
	int		l;
	int		frame;

	if (width < 1)
		return;

	// draw number string
	if (width > 5)
		width = 5;

	SCR_AddDirtyPoint (x, y);
	SCR_AddDirtyPoint (x+width*CHAR_WIDTH+2, y+23);

	Com_sprintf (num, sizeof(num), "%i", value);
	l = strlen(num);
	if (l > width)
		l = width;
	x += 2 + CHAR_WIDTH*(width - l);

	ptr = num;
	while (*ptr && l)
	{
		if (*ptr == '-')
			frame = STAT_MINUS;
		else
			frame = *ptr -'0';

		vid_so.re.DrawPic (x,y,sb_nums[color][frame]);
		x += CHAR_WIDTH;
		ptr++;
		l--;
	}
}


/*
===============
SCR_TouchPics

Allows rendering code to cache all needed sbar graphics
===============
*/
void SCR_TouchPics (void)
{
	int		i, j;

	for (i=0 ; i<2 ; i++)
		for (j=0 ; j<11 ; j++)
			vid_so.re.RegisterPic (sb_nums[i][j]);

	if (crosshair->value)
	{
		if (crosshair->value > 3 || crosshair->value < 0)
			crosshair->value = 3;

		Com_sprintf (crosshair_pic, sizeof(crosshair_pic), "ch%i", (int)(crosshair->value));
		vid_so.re.DrawGetPicSize (&crosshair_width, &crosshair_height, crosshair_pic);
		if (!crosshair_width)
			crosshair_pic[0] = 0;
	}
}

/*
================
SCR_ExecuteLayoutString 

================
*/
void SCR_ExecuteLayoutString (char *s)
{
	int		x, y;
	int		value;
	char	*token;
	int		width;
	int		index;
	clientinfo_t	*ci;

	if (cl_main.cls.state != ca_active || !cl_main.cl.refresh_prepped)
		return;

	if (!s[0])
		return;

	x = 0;
	y = 0;
	width = 3;

	while (s)
	{
		token = COM_Parse (&s);
		if (!strcmp(token, "xl"))
		{
			token = COM_Parse (&s);
			x = atoi(token);
			continue;
		}
		if (!strcmp(token, "xr"))
		{
			token = COM_Parse (&s);
			x = vid_so.viddef.width + atoi(token);
			continue;
		}
		if (!strcmp(token, "xv"))
		{
			token = COM_Parse (&s);
			x = vid_so.viddef.width/2 - 160 + atoi(token);
			continue;
		}

		if (!strcmp(token, "yt"))
		{
			token = COM_Parse (&s);
			y = atoi(token);
			continue;
		}
		if (!strcmp(token, "yb"))
		{
			token = COM_Parse (&s);
			y = vid_so.viddef.height + atoi(token);
			continue;
		}
		if (!strcmp(token, "yv"))
		{
			token = COM_Parse (&s);
			y = vid_so.viddef.height/2 - 120 + atoi(token);
			continue;
		}

		if (!strcmp(token, "pic"))
		{	// draw a pic from a stat number
			token = COM_Parse (&s);
			value = cl_main.cl.frame.playerstate.stats[atoi(token)];
			if (value >= MAX_IMAGES)
				Com_Error (q_shared.ERR_DROP, "Pic >= MAX_IMAGES");
			if (cl_main.cl.configstrings[CS_IMAGES+value])
			{
				SCR_AddDirtyPoint (x, y);
				SCR_AddDirtyPoint (x+23, y+23);
				vid_so.re.DrawPic (x, y, cl_main.cl.configstrings[CS_IMAGES+value]);
			}
			continue;
		}

		if (!strcmp(token, "client"))
		{	// draw a deathmatch client block
			int		score, ping, time;

			token = COM_Parse (&s);
			x = vid_so.viddef.width/2 - 160 + atoi(token);
			token = COM_Parse (&s);
			y = vid_so.viddef.height/2 - 120 + atoi(token);
			SCR_AddDirtyPoint (x, y);
			SCR_AddDirtyPoint (x+159, y+31);

			token = COM_Parse (&s);
			value = atoi(token);
			if (value >= MAX_CLIENTS || value < 0)
				Com_Error (q_shared.ERR_DROP, "client >= MAX_CLIENTS");
			ci = &cl_main.cl.clientinfo[value];

			token = COM_Parse (&s);
			score = atoi(token);

			token = COM_Parse (&s);
			ping = atoi(token);

			token = COM_Parse (&s);
			time = atoi(token);

			DrawAltString (x+32, y, ci->name);
			DrawString (x+32, y+8,  "Score: ");
			DrawAltString (x+32+7*8, y+8,  va("%i", score));
			DrawString (x+32, y+16, va("Ping:  %i", ping));
			DrawString (x+32, y+24, va("Time:  %i", time));

			if (!ci->icon)
				ci = &cl_main.cl.baseclientinfo;
			vid_so.re.DrawPic (x, y, ci->iconname);
			continue;
		}

		if (!strcmp(token, "ctf"))
		{	// draw a ctf client block
			int		score, ping;
			char	block[80];

			token = COM_Parse (&s);
			x = vid_so.viddef.width/2 - 160 + atoi(token);
			token = COM_Parse (&s);
			y = vid_so.viddef.height/2 - 120 + atoi(token);
			SCR_AddDirtyPoint (x, y);
			SCR_AddDirtyPoint (x+159, y+31);

			token = COM_Parse (&s);
			value = atoi(token);
			if (value >= MAX_CLIENTS || value < 0)
				Com_Error (q_shared.ERR_DROP, "client >= MAX_CLIENTS");
			ci = &cl_main.cl.clientinfo[value];

			token = COM_Parse (&s);
			score = atoi(token);

			token = COM_Parse (&s);
			ping = atoi(token);
			if (ping > 999)
				ping = 999;

			sprintf(block, "%3d %3d %-12.12s", score, ping, ci->name);

			if (value == cl_main.cl.playernum)
				DrawAltString (x, y, block);
			else
				DrawString (x, y, block);
			continue;
		}

		if (!strcmp(token, "picn"))
		{	// draw a pic from a name
			token = COM_Parse (&s);
			SCR_AddDirtyPoint (x, y);
			SCR_AddDirtyPoint (x+23, y+23);
			vid_so.re.DrawPic (x, y, token);
			continue;
		}

		if (!strcmp(token, "num"))
		{	// draw a number
			token = COM_Parse (&s);
			width = atoi(token);
			token = COM_Parse (&s);
			value = cl_main.cl.frame.playerstate.stats[atoi(token)];
			SCR_DrawField (x, y, 0, width, value);
			continue;
		}

		if (!strcmp(token, "hnum"))
		{	// health number
			int		color;

			width = 3;
			value = cl_main.cl.frame.playerstate.stats[STAT_HEALTH];
			if (value > 25)
				color = 0;	// green
			else if (value > 0)
				color = (cl_main.cl.frame.serverframe>>2) & 1;		// flash
			else
				color = 1;

			if (cl_main.cl.frame.playerstate.stats[STAT_FLASHES] & 1)
				vid_so.re.DrawPic (x, y, "field_3");

			SCR_DrawField (x, y, color, width, value);
			continue;
		}

		if (!strcmp(token, "anum"))
		{	// ammo number
			int		color;

			width = 3;
			value = cl_main.cl.frame.playerstate.stats[STAT_AMMO];
			if (value > 5)
				color = 0;	// green
			else if (value >= 0)
				color = (cl_main.cl.frame.serverframe>>2) & 1;		// flash
			else
				continue;	// negative number = don't show

			if (cl_main.cl.frame.playerstate.stats[STAT_FLASHES] & 4)
				vid_so.re.DrawPic (x, y, "field_3");

			SCR_DrawField (x, y, color, width, value);
			continue;
		}

		if (!strcmp(token, "rnum"))
		{	// armor number
			int		color;

			width = 3;
			value = cl_main.cl.frame.playerstate.stats[STAT_ARMOR];
			if (value < 1)
				continue;

			color = 0;	// green

			if (cl_main.cl.frame.playerstate.stats[STAT_FLASHES] & 2)
				vid_so.re.DrawPic (x, y, "field_3");

			SCR_DrawField (x, y, color, width, value);
			continue;
		}


		if (!strcmp(token, "stat_string"))
		{
			token = COM_Parse (&s);
			index = atoi(token);
			if (index < 0 || index >= MAX_CONFIGSTRINGS)
				Com_Error (q_shared.ERR_DROP, "Bad stat_string index");
			index = cl_main.cl.frame.playerstate.stats[index];
			if (index < 0 || index >= MAX_CONFIGSTRINGS)
				Com_Error (q_shared.ERR_DROP, "Bad stat_string index");
			DrawString (x, y, cl_main.cl.configstrings[index]);
			continue;
		}

		if (!strcmp(token, "cstring"))
		{
			token = COM_Parse (&s);
			DrawHUDString (token, x, y, 320, 0);
			continue;
		}

		if (!strcmp(token, "string"))
		{
			token = COM_Parse (&s);
			DrawString (x, y, token);
			continue;
		}

		if (!strcmp(token, "cstring2"))
		{
			token = COM_Parse (&s);
			DrawHUDString (token, x, y, 320,0x80);
			continue;
		}

		if (!strcmp(token, "string2"))
		{
			token = COM_Parse (&s);
			DrawAltString (x, y, token);
			continue;
		}

		if (!strcmp(token, "if"))
		{	// draw a number
			token = COM_Parse (&s);
			value = cl_main.cl.frame.playerstate.stats[atoi(token)];
			if (!value)
			{	// skip to endif
				while (s && strcmp(token, "endif") )
				{
					token = COM_Parse (&s);
				}
			}

			continue;
		}


	}
}


/*
================
SCR_DrawStats

The status bar is a small layout program that
is based on the stats array
================
*/
void SCR_DrawStats (void)
{
	SCR_ExecuteLayoutString (cl_main.cl.configstrings[CS_STATUSBAR]);
}


/*
================
SCR_DrawLayout

================
*/
#define	STAT_LAYOUTS		13

void SCR_DrawLayout (void)
{
	if (!cl_main.cl.frame.playerstate.stats[STAT_LAYOUTS])
		return;
	SCR_ExecuteLayoutString (cl_main.cl.layout);
}

//=======================================================

/*
==================
SCR_UpdateScreen

This is called every frame, and can also be called explicitly to flush
text to the screen.
==================
"""
def SCR_UpdateScreen ():

	global scr_initialized, scr_draw_loading

	#int numframes;
	#int i;
	separation = [0.0, 0.0] #float [2]

	# if the screen is disabled (loading plaque is up, or vid mode changing)
	# do nothing at all

	if cl_main.cls.disable_screen != 0:
	
		if q_shlinux.Sys_Milliseconds () - cl_main.cls.disable_screen > 120000:
		
			cl_main.cls.disable_screen = 0
			common.Com_Printf ("Loading plaque timed out.\n")
		
		return

	if not scr_initialized or not console.con.initialized:
		return				# not initialized yet

	
	#
	# range check cl_camera_separation so we don't inadvertently fry someone's
	# brain
	#
	if cl_main.cl_stereo_separation.value > 1.0 :
		cvar.Cvar_SetValue( "cl_stereo_separation", 1.0 )
	elif cl_main.cl_stereo_separation.value < 0 :
		cvar.Cvar_SetValue( "cl_stereo_separation", 0.0 )

	if cl_main.cl_stereo.value:
	
		numframes = 2
		separation[0] = -cl_main.cl_stereo_separation.value / 2
		separation[1] =  cl_main.cl_stereo_separation.value / 2
			
	else:
	
		separation[0] = 0
		separation[1] = 0
		numframes = 1
	
	
	for i in range(numframes):
		
		vid_so.re.BeginFrame( separation[i] )
		
		if scr_draw_loading == 2:
			#  loading plaque over black screen
			#int		w, h;

			vid_so.re.CinematicSetPalette(None)
			scr_draw_loading = 0
			w, h = vid_so.re.DrawGetPicSize ("loading")
			vid_so.re.DrawPic ((vid_so.viddef.width-w)//2, (vid_so.viddef.height-h)//2, "loading")
			##vid_so.re.EndFrame();
			##return;

		# if a cinematic is supposed to be running, handle menus
		# and console specially
		elif cl_main.cl.cinematictime > 0:
		
			
			if cl_main.cls.key_dest == client.keydest_t.key_menu:

				if cl_main.cl.cinematicpalette_active:
				
					vid_so.re.CinematicSetPalette(None)
					cl_main.cl.cinematicpalette_active = False
				
				menu.M_Draw ()
				##vid_so.re.EndFrame()
				##return

			elif cl_main.cls.key_dest == client.keydest_t.key_console:

				if cl_main.cl.cinematicpalette_active:
				
					vid_so.re.CinematicSetPalette(None)
					cl_main.cl.cinematicpalette_active = False
				
				SCR_DrawConsole ()
				##vid_so.re.EndFrame()
				##return

			else:
			
				cl_cin.SCR_DrawCinematic()
				##vid_so.re.EndFrame()
				##return
			

		
		else:

			# make sure the game palette is active
			if cl_main.cl.cinematicpalette_active:
			
				vid_so.re.CinematicSetPalette(None)
				cl_main.cl.cinematicpalette_active = False
			

			# do 3D refresh drawing, and then update the screen
			SCR_CalcVrect ()

			# clear any dirty part of the background
			SCR_TileClear ()

			cl_view.V_RenderView ( separation[i] )
			"""
			SCR_DrawStats ()
			if (cl_main.cl.frame.playerstate.stats[STAT_LAYOUTS] & 1)
				SCR_DrawLayout ()
			if (cl_main.cl.frame.playerstate.stats[STAT_LAYOUTS] & 2)
				CL_DrawInventory ()

			SCR_DrawNet ()
			SCR_CheckDrawCenterString ()

			if (scr_timegraph->value)
				SCR_DebugGraph (cl_main.cls.frametime*300, 0)

			if (scr_debuggraph->value || scr_timegraph->value || scr_netgraph->value)
				SCR_DrawDebugGraph ()

			SCR_DrawPause ()
			"""
			SCR_DrawConsole ()

			menu.M_Draw ()

			SCR_DrawLoading ()

		
	
	vid_so.re.EndFrame()

