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

# cl_view.c -- player rendering positioning

import math
import functools
import numpy as np
from qcommon import cvar, common, cmd
from game import q_shared
from client import cl_tent, cl_main, client, console, cl_scrn, cl_ents, ref
from linux import vid_so, cd_linux
"""
#include "client.h"

//=============
//
// development tools for weapons
//
int			gun_frame;
struct model_s	*gun_model;

//=============
"""
crosshair = None #cvar_t *
cl_testparticles = None #cvar_t *
cl_testentities = None #cvar_t *
cl_testlights = None #cvar_t *
cl_testblend = None #cvar_t *

cl_stats = None #cvar_t *


r_numdlights: int = 0
r_dlights = []
for i in range(ref.MAX_DLIGHTS):
	r_dlights.append(ref.dlight_t())

r_numentities: int = 0
r_entities = []
for i in range(ref.MAX_ENTITIES):
	r_entities.append(ref.entity_t())

r_numparticles: int = 0
r_particles = []
for i in range(ref.MAX_PARTICLES):
	r_particles.append(ref.particle_t())

r_lightstyles = []
for i in range(ref.MAX_LIGHTSTYLES):
	r_lightstyles.append(ref.lightstyle_t())

"""
char cl_weaponmodels[MAX_CLIENTWEAPONMODELS][MAX_QPATH];
int num_cl_weaponmodels;

/*
====================
V_ClearScene

Specifies the model that will be used as the world
====================
"""
def V_ClearScene ():

	global r_numdlights, r_numentities, r_numparticles

	r_numdlights = 0
	r_numentities = 0
	r_numparticles = 0



"""
=====================
V_AddEntity

=====================
*/
void V_AddEntity (entity_t *ent)
{
	if (r_numentities >= MAX_ENTITIES)
		return;
	r_entities[r_numentities++] = *ent;
}


/*
=====================
V_AddParticle

=====================
*/
void V_AddParticle (vec3_t org, int color, float alpha)
{
	particle_t	*p;

	if (r_numparticles >= MAX_PARTICLES)
		return;
	p = &r_particles[r_numparticles++];
	VectorCopy (org, p->origin);
	p->color = color;
	p->alpha = alpha;
}

/*
=====================
V_AddLight

=====================
*/
void V_AddLight (vec3_t org, float intensity, float r, float g, float b)
{
	dlight_t	*dl;

	if (r_numdlights >= MAX_DLIGHTS)
		return;
	dl = &r_dlights[r_numdlights++];
	VectorCopy (org, dl->origin);
	dl->intensity = intensity;
	dl->color[0] = r;
	dl->color[1] = g;
	dl->color[2] = b;
}


/*
=====================
V_AddLightStyle

=====================
*/
void V_AddLightStyle (int style, float r, float g, float b)
{
	lightstyle_t	*ls;

	if (style < 0 || style > MAX_LIGHTSTYLES)
		Com_Error (q_shared.ERR_DROP, "Bad light style %i", style);
	ls = &r_lightstyles[style];

	ls->white = r+g+b;
	ls->rgb[0] = r;
	ls->rgb[1] = g;
	ls->rgb[2] = b;
}

/*
================
V_TestParticles

If cl_testparticles is set, create 4096 particles in the view
================
*/
void V_TestParticles (void)
{
	particle_t	*p;
	int			i, j;
	float		d, r, u;

	r_numparticles = MAX_PARTICLES;
	for (i=0 ; i<r_numparticles ; i++)
	{
		d = i*0.25;
		r = 4*((i&7)-3.5);
		u = 4*(((i>>3)&7)-3.5);
		p = &r_particles[i];

		for (j=0 ; j<3 ; j++)
			p->origin[j] = cl_main.cl.refdef.vieworg[j] + cl_main.cl.v_forward[j]*d +
			cl_main.cl.v_right[j]*r + cl_main.cl.v_up[j]*u;

		p->color = 8;
		p->alpha = cl_testparticles->value;
	}
}

/*
================
V_TestEntities

If cl_testentities is set, create 32 player models
================
*/
void V_TestEntities (void)
{
	int			i, j;
	float		f, r;
	entity_t	*ent;

	r_numentities = 32;
	memset (r_entities, 0, sizeof(r_entities));

	for (i=0 ; i<r_numentities ; i++)
	{
		ent = &r_entities[i];

		r = 64 * ( (i%4) - 1.5 );
		f = 64 * (i/4) + 128;

		for (j=0 ; j<3 ; j++)
			ent->origin[j] = cl_main.cl.refdef.vieworg[j] + cl_main.cl.v_forward[j]*f +
			cl_main.cl.v_right[j]*r;

		ent->model = cl_main.cl.baseclientinfo.model;
		ent->skin = cl_main.cl.baseclientinfo.skin;
	}
}

/*
================
V_TestLights

If cl_testlights is set, create 32 lights models
================
*/
void V_TestLights (void)
{
	int			i, j;
	float		f, r;
	dlight_t	*dl;

	r_numdlights = 32;
	memset (r_dlights, 0, sizeof(r_dlights));

	for (i=0 ; i<r_numdlights ; i++)
	{
		dl = &r_dlights[i];

		r = 64 * ( (i%4) - 1.5 );
		f = 64 * (i/4) + 128;

		for (j=0 ; j<3 ; j++)
			dl->origin[j] = cl_main.cl.refdef.vieworg[j] + cl_main.cl.v_forward[j]*f +
			cl_main.cl.v_right[j]*r;
		dl->color[0] = ((i%6)+1) & 1;
		dl->color[1] = (((i%6)+1) & 2)>>1;
		dl->color[2] = (((i%6)+1) & 4)>>2;
		dl->intensity = 200;
	}
}

//===================================================================

/*
=================
CL_PrepRefresh

Call before entering a new level, or after changing dlls
=================
"""
def CL_PrepRefresh ():
	
	"""
	char		mapname[32];
	int			i;
	char		name[MAX_QPATH];
	float		rotate;
	"""
	axis = np.zeros((3,), dtype=np.float32)

	if cl_main.cl.configstrings[q_shared.CS_MODELS+1] is None:
		return		# no map loaded

	cl_scrn.SCR_AddDirtyPoint (0, 0)
	cl_scrn.SCR_AddDirtyPoint (vid_so.viddef.width-1, vid_so.viddef.height-1)
	"""
	// let the render dll load the map
	strcpy (mapname, cl_main.cl.configstrings[q_shared.CS_MODELS+1] + 5);	// skip "maps/"
	mapname[strlen(mapname)-4] = 0;		// cut off ".bsp"

	// register models, pics, and skins
	Com_Printf ("Map: %s\r", mapname); 
	SCR_UpdateScreen ();
	vid_so.re.BeginRegistration (mapname);
	Com_Printf ("                                     \r");

	// precache status bar pics
	Com_Printf ("pics\r"); 
	SCR_UpdateScreen ();
	SCR_TouchPics ();
	Com_Printf ("                                     \r");
	"""
	cl_tent.CL_RegisterTEntModels ()
	"""
	num_cl_weaponmodels = 1;
	strcpy(cl_weaponmodels[0], "weapon.md2");

	for (i=1 ; i<MAX_MODELS && cl_main.cl.configstrings[q_shared.CS_MODELS+i][0] ; i++)
	{
		strcpy (name, cl_main.cl.configstrings[q_shared.CS_MODELS+i]);
		name[37] = 0;	// never go beyond one line
		if (name[0] != '*')
			Com_Printf ("%s\r", name); 
		SCR_UpdateScreen ();
		Sys_SendKeyEvents ();	// pump message loop
		if (name[0] == '#')
		{
			// special player weapon model
			if (num_cl_weaponmodels < MAX_CLIENTWEAPONMODELS)
			{
				strncpy(cl_weaponmodels[num_cl_weaponmodels], cl_main.cl.configstrings[q_shared.CS_MODELS+i]+1,
					sizeof(cl_weaponmodels[num_cl_weaponmodels]) - 1);
				num_cl_weaponmodels++;
			}
		} 
		else
		{
			cl_main.cl.model_draw[i] = vid_so.re.RegisterModel (cl_main.cl.configstrings[q_shared.CS_MODELS+i]);
			if (name[0] == '*')
				cl_main.cl.model_clip[i] = CM_InlineModel (cl_main.cl.configstrings[q_shared.CS_MODELS+i]);
			else
				cl_main.cl.model_clip[i] = NULL;
		}
		if (name[0] != '*')
			Com_Printf ("                                     \r");
	}

	Com_Printf ("images\r", i); 
	SCR_UpdateScreen ();
	for (i=1 ; i<MAX_IMAGES && cl_main.cl.configstrings[q_shared.CS_IMAGES+i][0] ; i++)
	{
		cl_main.cl.image_precache[i] = vid_so.re.RegisterPic (cl_main.cl.configstrings[q_shared.CS_IMAGES+i]);
		Sys_SendKeyEvents ();	// pump message loop
	}
	
	Com_Printf ("                                     \r");
	for (i=0 ; i<MAX_CLIENTS ; i++)
	{
		if (!cl_main.cl.configstrings[q_shared.CS_PLAYERSKINS+i][0])
			continue;
		Com_Printf ("client %i\r", i); 
		SCR_UpdateScreen ();
		Sys_SendKeyEvents ();	// pump message loop
		CL_ParseClientinfo (i);
		Com_Printf ("                                     \r");
	}

	CL_LoadClientinfo (&cl_main.cl.baseclientinfo, "unnamed\\male/grunt");
	"""
	i=0 # DEBUG What should this be?

	# set sky textures and speed
	common.Com_Printf ("sky\r".format(i))
	cl_scrn.SCR_UpdateScreen ()
	rotate = float(cl_main.cl.configstrings[q_shared.CS_SKYROTATE])
	axis[0], axis[1], axis[2] = tuple(map(float, cl_main.cl.configstrings[q_shared.CS_SKYAXIS].split(" ")))
	vid_so.re.SetSky (cl_main.cl.configstrings[q_shared.CS_SKY], rotate, axis)
	common.Com_Printf ("                                     \r")

	# the renderer can now free unneeded stuff
	vid_so.re.EndRegistration ()

	# clear any lines of console text
	console.Con_ClearNotify ()

	cl_scrn.SCR_UpdateScreen ()
	cl_main.cl.refresh_prepped = True
	cl_main.cl.force_refdef = True # make sure we have a valid refdef

	# start the cd track
	cd_linux.CDAudio_Play (cl_main.cl.configstrings[q_shared.CS_CDTRACK], True)


"""
====================
CalcFov
====================
"""
def CalcFov (fov_x: float, width: float, height: float)->float:

	#float	a;
	#float	x;

	if fov_x < 1 or fov_x > 179:
		common.Com_Error (q_shared.ERR_DROP, "Bad fov: {}".format(fov_x))

	x = width/math.tan(fov_x/360*math.pi)

	a = math.atan (height/x)

	a = a*360.0/math.pi

	return a


"""
//============================================================================
"""
# gun frame debugging functions
def V_Gun_Next_f ():
	pass
	"""
	gun_frame++;
	Com_Printf ("frame %i\n", gun_frame);
	"""

def V_Gun_Prev_f ():
	pass
	"""
	gun_frame--;
	if (gun_frame < 0)
		gun_frame = 0;
	Com_Printf ("frame %i\n", gun_frame);
	"""

def V_Gun_Model_f ():

	pass
	"""
	char	name[MAX_QPATH];

	if (Cmd_Argc() != 2)
	{
		gun_model = NULL;
		return;
	}
	Com_sprintf (name, sizeof(name), "models/%s/tris.md2", Cmd_Argv(1));
	gun_model = vid_so.re.RegisterModel (name);
	"""

"""
//============================================================================


/*
=================
SCR_DrawCrosshair
=================
"""
def SCR_DrawCrosshair ():

	pass
	"""
	if (!crosshair->value)
		return;

	if (crosshair->modified)
	{
		crosshair->modified = false;
		SCR_TouchPics ();
	}

	if (!crosshair_pic[0])
		return;

	vid_so.re.DrawPic (cl_scrn.scr_vrect.x + ((cl_scrn.scr_vrect.width - crosshair_width)>>1)
	, cl_scrn.scr_vrect.y + ((cl_scrn.scr_vrect.height - crosshair_height)>>1), crosshair_pic);
	"""

"""
==================
V_RenderView

==================
"""
def V_RenderView( stereo_separation: float ):

	global r_numdlights, r_numentities, r_numparticles

	#extern int entitycmpfnc( const entity_t *, const entity_t * );

	if cl_main.cls.state != client.connstate_t.ca_active:
		return

	if not cl_main.cl.refresh_prepped:
		return			# still loading

	if int(cl_main.cl_timedemo.value):
	
		if not cl_main.cl.timedemo_start:
			cl_main.cl.timedemo_start = q_shlinux.Sys_Milliseconds ()
		cl_main.cl.timedemo_frames+=1
	
	# an invalid frame will just use the exact previous refdef
	# we can't use the old frame if the video mode has changed, though...
	if cl_main.cl.frame.valid and (cl_main.cl.force_refdef or not int(cl_main.cl_paused.value)):
	
		cl_main.cl.force_refdef = False

		V_ClearScene ()

		# build a refresh entity list and calc cl_main.cl.sim*
		# this also calls CL_CalcViewValues which loads
		# v_forward, etc.
		cl_ents.CL_AddEntities ()

		if int(cl_testparticles.value):
			V_TestParticles ()
		if int(cl_testentities.value):
			V_TestEntities ()
		if int(cl_testlights.value):
			V_TestLights ()
		if int(cl_testblend.value):
		
			cl_main.cl.refdef.blend[0] = 1
			cl_main.cl.refdef.blend[1] = 0.5
			cl_main.cl.refdef.blend[2] = 0.25
			cl_main.cl.refdef.blend[3] = 0.5
		

		# offset vieworg appropriately if we're doing stereo separation
		if stereo_separation != 0:
		
			tmp = VectorScale( cl_main.cl.v_right, stereo_separation, tmp )
			VectorAdd( cl_main.cl.refdef.vieworg, tmp, cl_main.cl.refdef.vieworg )
		

		# never let it sit exactly on a node line, because a water plane can
		# dissapear when viewed with the eye exactly on it.
		# the server protocol only specifies to 1/8 pixel, so add 1/16 in each axis
		cl_main.cl.refdef.vieworg[0] += 1.0/16
		cl_main.cl.refdef.vieworg[1] += 1.0/16
		cl_main.cl.refdef.vieworg[2] += 1.0/16

		cl_main.cl.refdef.x = cl_scrn.scr_vrect.x
		cl_main.cl.refdef.y = cl_scrn.scr_vrect.y
		cl_main.cl.refdef.width = cl_scrn.scr_vrect.width
		cl_main.cl.refdef.height = cl_scrn.scr_vrect.height
		cl_main.cl.refdef.fov_y = CalcFov (cl_main.cl.refdef.fov_x, cl_main.cl.refdef.width, cl_main.cl.refdef.height)
		cl_main.cl.refdef.time = cl_main.cl.time*0.001

		cl_main.cl.refdef.areabits = cl_main.cl.frame.areabits

		if not int(cl_main.cl_add_entities.value):
			r_numentities = 0
		if not int(cl_main.cl_add_particles.value):
			r_numparticles = 0
		if not int(cl_main.cl_add_lights.value):
			r_numdlights = 0
		if not int(cl_main.cl_add_blend.value):
			VectorClear (cl_main.cl.refdef.blend)	

		cl_main.cl.refdef.num_entities = r_numentities
		cl_main.cl.refdef.entities = r_entities
		cl_main.cl.refdef.num_particles = r_numparticles
		cl_main.cl.refdef.particles = r_particles
		cl_main.cl.refdef.num_dlights = r_numdlights
		cl_main.cl.refdef.dlights = r_dlights
		cl_main.cl.refdef.lightstyles = r_lightstyles

		cl_main.cl.refdef.rdflags = cl_main.cl.frame.playerstate.rdflags

		# sort entities for better cache locality
		cl_main.cl.refdef.entities.sort(key=functools.cmp_to_key(cl_scrn.entitycmpfnc))
	
	vid_so.re.RenderFrame (cl_main.cl.refdef)
	if cl_stats.value:
		common.Com_Printf ("ent:{}  lt:{}  part:{}\n".format(r_numentities, r_numdlights, r_numparticles))
	if int(common.log_stats.value) and ( log_stats_file != 0 ):
		log_stats_file = "{},{},{},".format(r_numentities, r_numdlights, r_numparticles)

	cl_scrn.SCR_AddDirtyPoint (cl_scrn.scr_vrect.x, cl_scrn.scr_vrect.y)
	cl_scrn.SCR_AddDirtyPoint (cl_scrn.scr_vrect.x+cl_scrn.scr_vrect.width-1,
		cl_scrn.scr_vrect.y+cl_scrn.scr_vrect.height-1)

	SCR_DrawCrosshair ()



"""
=============
V_Viewpos_f
=============
"""
def V_Viewpos_f ():

	common.Com_Printf ("({} {} {}) : {}\n".format(int(cl_main.cl.refdef.vieworg[0]),
		int(cl_main.cl.refdef.vieworg[1]), int(cl_main.cl.refdef.vieworg[2]), 
		int(cl_main.cl.refdef.viewangles[YAW])))

"""
=============
V_Init
=============
"""
def V_Init ():

	global crosshair, cl_testparticles, cl_testentities, cl_testlights, cl_testblend, cl_stats

	cmd.Cmd_AddCommand ("gun_next", V_Gun_Next_f)
	cmd.Cmd_AddCommand ("gun_prev", V_Gun_Prev_f)
	cmd.Cmd_AddCommand ("gun_model", V_Gun_Model_f)

	cmd.Cmd_AddCommand ("viewpos", V_Viewpos_f);
	
	crosshair = cvar.Cvar_Get ("crosshair", "0", q_shared.CVAR_ARCHIVE)

	cl_testblend = cvar.Cvar_Get ("cl_testblend", "0", 0)
	cl_testparticles = cvar.Cvar_Get ("cl_testparticles", "0", 0)
	cl_testentities = cvar.Cvar_Get ("cl_testentities", "0", 0)
	cl_testlights = cvar.Cvar_Get ("cl_testlights", "0", 0)

	cl_stats = cvar.Cvar_Get ("cl_stats", "0", 0)

