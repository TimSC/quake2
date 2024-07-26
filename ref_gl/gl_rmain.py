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
import math
import struct
import copy
import OpenGL.GL as GL
import OpenGL.GLU as GLU
import numpy as np
from OpenGL.GL import glGetString
from enum import Enum
from client import ref
from linux import gl_glx, qgl_linux
from game import q_shared
from qcommon import cvar, cmd, files, qcommon
from ref_gl import gl_draw, gl_image, gl_rmisc, gl_model, gl_warp, gl_rsurf

REF_VERSION = "GL 0.01"

# up / down
PITCH	= 0

# left / right
YAW		= 1

# fall over
ROLL	= 2

class rserr_t(Enum):

	rserr_ok = 0

	rserr_invalid_fullscreen = 1
	rserr_invalid_mode = 2

	rserr_unknown = 3

class glconfig_t(object):

	def __init__(self):

		self.renderer = None #int
		self.renderer_string = None #const char *
		self.vendor_string = None #const char *
		self.version_string = None #const char *
		self.extensions_string = None #const char *

		self.allow_cds = True #qboolean

class glstate_t(object):
	def __init__(self):

		self.inverse_intensity = None #float
		self.fullscreen = None #qboolean

		self.prev_mode = None #int

		self.d_16to8table = None #unsigned char *

		self.lightmap_textures = None #int

		self.currenttextures = [None, None] #int[2]
		self.currenttmu = 0 #int

		self.camera_separation = None #float
		self.stereo_enabled = None #qboolean

		self.originalRedGammaTable = [] #unsigned char [256]
		self.originalGreenGammaTable = [] #unsigned char [256]
		self.originalBlueGammaTable = [] #unsigned char [256]

class viddef_t(object):
	def __init__(self):
		self.width, self.height = 800, 600 # coordinates from main game

vid = viddef_t()

ri = ref.refimport_t()
"""
int GL_TEXTURE0, GL_TEXTURE1;
"""
r_worldmodel = None #model_t *

gldepthmin, gldepthmax = 0.0, 0.0 #float

gl_config = glconfig_t()

gl_state = glstate_t()

r_notexture = None # image_t *, use for bad textures
r_particletexture = None # image_t *, little dot for particles

currententity = None # entity_t *

currentmodel = None # model_t *
"""
cplane_t	frustum[4];

int			r_visframecount;	// bumped when going to a new PVS
int			r_framecount;		// used for dlight push checking

int			c_brush_polys, c_alias_polys;

float		v_blend[4];			// final blending color

void GL_Strings_f( void );
"""
#
# view origin
#
vup = np.zeros((3,), dtype=np.float32)
vpn = np.zeros((3,), dtype=np.float32)
vright = np.zeros((3,), dtype=np.float32)
r_origin = np.zeros((3,), dtype=np.float32)

r_world_matrix = np.zeros((16,), dtype=np.float32)
r_base_world_matrix = np.zeros((16,), dtype=np.float32)

#
# screen size info
#
r_newrefdef = ref.refdef_t()

r_viewcluster, r_viewcluster2, r_oldviewcluster, r_oldviewcluster2 = None, None, None, None #int

r_norefresh = None #cvar_t *
r_drawentities = None #cvar_t *
r_drawworld = None #cvar_t *
r_speeds = None #cvar_t *
r_fullbright = None #cvar_t *
r_novis = None #cvar_t *
r_nocull = None #cvar_t *
r_lerpmodels = None #cvar_t *
r_lefthand = None #cvar_t *

r_lightlevel = None #cvar_t *, FIXME: This is a HACK to get the client's light level

gl_nosubimage = None #cvar_t *
gl_allow_software = None #cvar_t *

gl_vertex_arrays = None #cvar_t *

gl_particle_min_size = None #cvar_t *
gl_particle_max_size = None #cvar_t *
gl_particle_size = None #cvar_t *
gl_particle_att_a = None #cvar_t *
gl_particle_att_b = None #cvar_t *
gl_particle_att_c = None #cvar_t *

gl_ext_swapinterval = None #cvar_t *
gl_ext_palettedtexture = None #cvar_t *
gl_ext_multitexture = None #cvar_t *
gl_ext_pointparameters = None #cvar_t *
gl_ext_compiled_vertex_array = None #cvar_t *

gl_log = None #cvar_t *
gl_bitdepth = None #cvar_t *
gl_drawbuffer = None #cvar_t *
gl_driver = None #cvar_t *
gl_lightmap = None #cvar_t *
gl_shadows = None #cvar_t *
gl_mode = None #cvar_t *
gl_dynamic = None #cvar_t *
gl_monolightmap = None #cvar_t *
gl_modulate = None #cvar_t *
gl_nobind = None #cvar_t *
gl_round_down = None #cvar_t *
gl_picmip = None #cvar_t *
gl_skymip = None #cvar_t *
gl_showtris = None #cvar_t *
gl_ztrick = None #cvar_t *
gl_finish = None #cvar_t *
gl_clear = None #cvar_t *
gl_cull = None #cvar_t *
gl_polyblend = None #cvar_t *
gl_flashblend = None #cvar_t *
gl_playermip = None #cvar_t *

gl_saturatelighting = None #cvar_t *
gl_swapinterval = None #cvar_t *
gl_texturemode = None #cvar_t *
gl_texturealphamode = None #cvar_t *
gl_texturesolidmode = None #cvar_t *
gl_lockpvs = None #cvar_t *

gl_3dlabs_broken = None #cvar_t *

vid_fullscreen = None #cvar_t *
vid_gamma = None #cvar_t *
vid_ref = None #cvar_t *

"""
=================
R_CullBox

Returns true if the box is completely outside the frustom
=================
*/
qboolean R_CullBox (vec3_t mins, vec3_t maxs)
{
	int		i;

	if (r_nocull->value)
		return false;

	for (i=0 ; i<4 ; i++)
		if ( BOX_ON_PLANE_SIDE(mins, maxs, &frustum[i]) == 2)
			return true;
	return false;
}


void R_RotateForEntity (entity_t *e)
{
	qglTranslatef (e->origin[0],  e->origin[1],  e->origin[2]);

	qglRotatef (e->angles[1],  0, 0, 1);
	qglRotatef (-e->angles[0],  0, 1, 0);
	qglRotatef (-e->angles[2],  1, 0, 0);
}

/*
=============================================================

  SPRITE MODELS

=============================================================
*/


/*
=================
R_DrawSpriteModel

=================
*/
void R_DrawSpriteModel (entity_t *e)
{
	float alpha = 1.0F;
	vec3_t	point;
	dsprframe_t	*frame;
	float		*up, *right;
	dsprite_t		*psprite;

	// don't even bother culling, because it's just a single
	// polygon without a surface cache

	psprite = (dsprite_t *)currentmodel->extradata;

#if 0
	if (e->frame < 0 || e->frame >= psprite->numframes)
	{
		ri.Con_Printf (q_shared.PRINT_ALL, "no such sprite frame %i\n", e->frame);
		e->frame = 0;
	}
#endif
	e->frame %= psprite->numframes;

	frame = &psprite->frames[e->frame];

#if 0
	if (psprite->type == SPR_ORIENTED)
	{	// bullet marks on walls
	vec3_t		v_forward, v_right, v_up;

	AngleVectors (currententity->angles, v_forward, v_right, v_up);
		up = v_up;
		right = v_right;
	}
	else
#endif
	{	// normal sprite
		up = vup;
		right = vright;
	}

	if ( e->flags & RF_TRANSLUCENT )
		alpha = e->alpha;

	if ( alpha != 1.0F )
		qglEnable( GL_BLEND );

	qglColor4f( 1, 1, 1, alpha );

	GL_Bind(currentmodel->skins[e->frame]->texnum);

	GL_TexEnv( GL_MODULATE );

	if ( alpha == 1.0 )
		qglEnable (GL_ALPHA_TEST);
	else
		qglDisable( GL_ALPHA_TEST );

	qglBegin (GL_QUADS);

	qglTexCoord2f (0, 1);
	VectorMA (e->origin, -frame->origin_y, up, point);
	VectorMA (point, -frame->origin_x, right, point);
	qglVertex3fv (point);

	qglTexCoord2f (0, 0);
	VectorMA (e->origin, frame->height - frame->origin_y, up, point);
	VectorMA (point, -frame->origin_x, right, point);
	qglVertex3fv (point);

	qglTexCoord2f (1, 0);
	VectorMA (e->origin, frame->height - frame->origin_y, up, point);
	VectorMA (point, frame->width - frame->origin_x, right, point);
	qglVertex3fv (point);

	qglTexCoord2f (1, 1);
	VectorMA (e->origin, -frame->origin_y, up, point);
	VectorMA (point, frame->width - frame->origin_x, right, point);
	qglVertex3fv (point);
	
	qglEnd ();

	qglDisable (GL_ALPHA_TEST);
	GL_TexEnv( GL_REPLACE );

	if ( alpha != 1.0F )
		qglDisable( GL_BLEND );

	qglColor4f( 1, 1, 1, 1 );
}

//==================================================================================

/*
=============
R_DrawNullModel
=============
*/
void R_DrawNullModel (void)
{
	vec3_t	shadelight;
	int		i;

	if ( currententity->flags & RF_FULLBRIGHT )
		shadelight[0] = shadelight[1] = shadelight[2] = 1.0F;
	else
		R_LightPoint (currententity->origin, shadelight);

	qglPushMatrix ();
	R_RotateForEntity (currententity);

	qglDisable (GL_TEXTURE_2D);
	qglColor3fv (shadelight);

	qglBegin (GL_TRIANGLE_FAN);
	qglVertex3f (0, 0, -16);
	for (i=0 ; i<=4 ; i++)
		qglVertex3f (16*cos(i*M_PI/2), 16*sin(i*M_PI/2), 0);
	qglEnd ();

	qglBegin (GL_TRIANGLE_FAN);
	qglVertex3f (0, 0, 16);
	for (i=4 ; i>=0 ; i--)
		qglVertex3f (16*cos(i*M_PI/2), 16*sin(i*M_PI/2), 0);
	qglEnd ();

	qglColor3f (1,1,1);
	qglPopMatrix ();
	qglEnable (GL_TEXTURE_2D);
}

/*
=============
R_DrawEntitiesOnList
=============
*/
void R_DrawEntitiesOnList (void)
{
	int		i;

	if (!r_drawentities->value)
		return;

	// draw non-transparent first
	for (i=0 ; i<r_newrefdef.num_entities ; i++)
	{
		currententity = &r_newrefdef.entities[i];
		if (currententity->flags & RF_TRANSLUCENT)
			continue;	// solid

		if ( currententity->flags & RF_BEAM )
		{
			R_DrawBeam( currententity );
		}
		else
		{
			currentmodel = currententity->model;
			if (!currentmodel)
			{
				R_DrawNullModel ();
				continue;
			}
			switch (currentmodel->type)
			{
			case mod_alias:
				R_DrawAliasModel (currententity);
				break;
			case mod_brush:
				R_DrawBrushModel (currententity);
				break;
			case mod_sprite:
				R_DrawSpriteModel (currententity);
				break;
			default:
				ri.Sys_Error (ERR_DROP, "Bad modeltype");
				break;
			}
		}
	}

	// draw transparent entities
	// we could sort these if it ever becomes a problem...
	qglDepthMask (0);		// no z writes
	for (i=0 ; i<r_newrefdef.num_entities ; i++)
	{
		currententity = &r_newrefdef.entities[i];
		if (!(currententity->flags & RF_TRANSLUCENT))
			continue;	// solid

		if ( currententity->flags & RF_BEAM )
		{
			R_DrawBeam( currententity );
		}
		else
		{
			currentmodel = currententity->model;

			if (!currentmodel)
			{
				R_DrawNullModel ();
				continue;
			}
			switch (currentmodel->type)
			{
			case mod_alias:
				R_DrawAliasModel (currententity);
				break;
			case mod_brush:
				R_DrawBrushModel (currententity);
				break;
			case mod_sprite:
				R_DrawSpriteModel (currententity);
				break;
			default:
				ri.Sys_Error (ERR_DROP, "Bad modeltype");
				break;
			}
		}
	}
	qglDepthMask (1);		// back to writing

}

/*
** GL_DrawParticles
**
*/
void GL_DrawParticles( int num_particles, const particle_t particles[], const unsigned colortable[768] )
{
	const particle_t *p;
	int				i;
	vec3_t			up, right;
	float			scale;
	byte			color[4];

	GL_Bind(r_particletexture->texnum);
	qglDepthMask( GL_FALSE );		// no z buffering
	qglEnable( GL_BLEND );
	GL_TexEnv( GL_MODULATE );
	qglBegin( GL_TRIANGLES );

	VectorScale (vup, 1.5, up);
	VectorScale (vright, 1.5, right);

	for ( p = particles, i=0 ; i < num_particles ; i++,p++)
	{
		// hack a scale up to keep particles from disapearing
		scale = ( p->origin[0] - r_origin[0] ) * vpn[0] + 
				( p->origin[1] - r_origin[1] ) * vpn[1] +
				( p->origin[2] - r_origin[2] ) * vpn[2];

		if (scale < 20)
			scale = 1;
		else
			scale = 1 + scale * 0.004;

		*(int *)color = colortable[p->color];
		color[3] = p->alpha*255;

		qglColor4ubv( color );

		qglTexCoord2f( 0.0625, 0.0625 );
		qglVertex3fv( p->origin );

		qglTexCoord2f( 1.0625, 0.0625 );
		qglVertex3f( p->origin[0] + up[0]*scale, 
					 p->origin[1] + up[1]*scale, 
					 p->origin[2] + up[2]*scale);

		qglTexCoord2f( 0.0625, 1.0625 );
		qglVertex3f( p->origin[0] + right[0]*scale, 
					 p->origin[1] + right[1]*scale, 
					 p->origin[2] + right[2]*scale);
	}

	qglEnd ();
	qglDisable( GL_BLEND );
	qglColor4f( 1,1,1,1 );
	qglDepthMask( 1 );		// back to normal Z buffering
	GL_TexEnv( GL_REPLACE );
}

/*
===============
R_DrawParticles
===============
*/
void R_DrawParticles (void)
{
	if ( gl_ext_pointparameters->value && qglPointParameterfEXT )
	{
		int i;
		unsigned char color[4];
		const particle_t *p;

		qglDepthMask( GL_FALSE );
		qglEnable( GL_BLEND );
		qglDisable( GL_TEXTURE_2D );

		qglPointSize( gl_particle_size->value );

		qglBegin( GL_POINTS );
		for ( i = 0, p = r_newrefdef.particles; i < r_newrefdef.num_particles; i++, p++ )
		{
			*(int *)color = d_8to24table[p->color];
			color[3] = p->alpha*255;

			qglColor4ubv( color );

			qglVertex3fv( p->origin );
		}
		qglEnd();

		qglDisable( GL_BLEND );
		qglColor4f( 1.0F, 1.0F, 1.0F, 1.0F );
		qglDepthMask( GL_TRUE );
		qglEnable( GL_TEXTURE_2D );

	}
	else
	{
		GL_DrawParticles( r_newrefdef.num_particles, r_newrefdef.particles, d_8to24table );
	}
}

/*
============
R_PolyBlend
============
*/
void R_PolyBlend (void)
{
	if (!gl_polyblend->value)
		return;
	if (!v_blend[3])
		return;

	qglDisable (GL_ALPHA_TEST);
	qglEnable (GL_BLEND);
	qglDisable (GL_DEPTH_TEST);
	qglDisable (GL_TEXTURE_2D);

	qglLoadIdentity ();

	// FIXME: get rid of these
	qglRotatef (-90,  1, 0, 0);		// put Z going up
	qglRotatef (90,  0, 0, 1);		// put Z going up

	qglColor4fv (v_blend);

	qglBegin (GL_QUADS);

	qglVertex3f (10, 100, 100);
	qglVertex3f (10, -100, 100);
	qglVertex3f (10, -100, -100);
	qglVertex3f (10, 100, -100);
	qglEnd ();

	qglDisable (GL_BLEND);
	qglEnable (GL_TEXTURE_2D);
	qglEnable (GL_ALPHA_TEST);

	qglColor4f(1,1,1,1);
}

//=======================================================================

int SignbitsForPlane (cplane_t *out)
{
	int	bits, j;

	// for fast box on planeside test

	bits = 0;
	for (j=0 ; j<3 ; j++)
	{
		if (out->normal[j] < 0)
			bits |= 1<<j;
	}
	return bits;
}

"""
def R_SetFrustum ():

	pass
	"""
	int		i;

#if 0
	/*
	** this code is wrong, since it presume a 90 degree FOV both in the
	** horizontal and vertical plane
	*/
	// front side is visible
	VectorAdd (vpn, vright, frustum[0].normal);
	VectorSubtract (vpn, vright, frustum[1].normal);
	VectorAdd (vpn, vup, frustum[2].normal);
	VectorSubtract (vpn, vup, frustum[3].normal);

	// we theoretically don't need to normalize these vectors, but I do it
	// anyway so that debugging is a little easier
	VectorNormalize( frustum[0].normal );
	VectorNormalize( frustum[1].normal );
	VectorNormalize( frustum[2].normal );
	VectorNormalize( frustum[3].normal );
#else
	// rotate VPN right by FOV_X/2 degrees
	RotatePointAroundVector( frustum[0].normal, vup, vpn, -(90-r_newrefdef.fov_x / 2 ) );
	// rotate VPN left by FOV_X/2 degrees
	RotatePointAroundVector( frustum[1].normal, vup, vpn, 90-r_newrefdef.fov_x / 2 );
	// rotate VPN up by FOV_X/2 degrees
	RotatePointAroundVector( frustum[2].normal, vright, vpn, 90-r_newrefdef.fov_y / 2 );
	// rotate VPN down by FOV_X/2 degrees
	RotatePointAroundVector( frustum[3].normal, vright, vpn, -( 90 - r_newrefdef.fov_y / 2 ) );
#endif

	for (i=0 ; i<4 ; i++)
	{
		frustum[i].type = PLANE_ANYZ;
		frustum[i].dist = DotProduct (r_origin, frustum[i].normal);
		frustum[i].signbits = SignbitsForPlane (&frustum[i]);
	}
}

//=======================================================================

/*
===============
R_SetupFrame
===============
"""

def R_SetupFrame ():

	pass
	"""
{
	int i;
	mleaf_t	*leaf;

	r_framecount++;

// build the transformation matrix for the given view angles
	q_shared.VectorCopy (r_newrefdef.vieworg, r_origin);

	AngleVectors (r_newrefdef.viewangles, vpn, vright, vup);

// current viewcluster
	if ( !( r_newrefdef.rdflags & RDF_NOWORLDMODEL ) )
	{
		r_oldviewcluster = r_viewcluster;
		r_oldviewcluster2 = r_viewcluster2;
		leaf = Mod_PointInLeaf (r_origin, r_worldmodel);
		r_viewcluster = r_viewcluster2 = leaf->cluster;

		// check above and below so crossing solid water doesn't draw wrong
		if (!leaf->contents)
		{	// look down a bit
			vec3_t	temp;

			q_shared.VectorCopy (r_origin, temp);
			temp[2] -= 16;
			leaf = Mod_PointInLeaf (temp, r_worldmodel);
			if ( !(leaf->contents & CONTENTS_SOLID) &&
				(leaf->cluster != r_viewcluster2) )
				r_viewcluster2 = leaf->cluster;
		}
		else
		{	// look up a bit
			vec3_t	temp;

			q_shared.VectorCopy (r_origin, temp);
			temp[2] += 16;
			leaf = Mod_PointInLeaf (temp, r_worldmodel);
			if ( !(leaf->contents & CONTENTS_SOLID) &&
				(leaf->cluster != r_viewcluster2) )
				r_viewcluster2 = leaf->cluster;
		}
	}

	for (i=0 ; i<4 ; i++)
		v_blend[i] = r_newrefdef.blend[i];

	c_brush_polys = 0;
	c_alias_polys = 0;

	// clear out the portion of the screen that the NOWORLDMODEL defines
	if ( r_newrefdef.rdflags & RDF_NOWORLDMODEL )
	{
		qglEnable( GL_SCISSOR_TEST );
		qglClearColor( 0.3, 0.3, 0.3, 1 );
		qglScissor( r_newrefdef.x, vid.height - r_newrefdef.height - r_newrefdef.y, r_newrefdef.width, r_newrefdef.height );
		qglClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );
		qglClearColor( 1, 0, 0.5, 0.5 );
		qglDisable( GL_SCISSOR_TEST );
	}
}

"""
def MYgluPerspective( fovy, aspect, zNear, zFar ): # GLdouble, GLdouble, GLdouble, GLdouble

   # GLdouble xmin, xmax, ymin, ymax;

   ymax = zNear * math.tan( fovy * math.pi / 360.0 )
   ymin = -ymax

   xmin = ymin * aspect
   xmax = ymax * aspect

   xmin += -( 2 * gl_state.camera_separation ) / zNear
   xmax += -( 2 * gl_state.camera_separation ) / zNear

   GL.glFrustum( xmin, xmax, ymin, ymax, zNear, zFar )



"""
=============
R_SetupGL
=============
"""
def R_SetupGL ():

	"""
	float	screenaspect;
//	float	yfov;
	int		x, x2, y2, y, w, h;
	"""

	#
	# set up viewport
	#
	x = math.floor(r_newrefdef.x * vid.width // vid.width)
	x2 = math.ceil((r_newrefdef.x + r_newrefdef.width) * vid.width // vid.width)
	y = math.floor(vid.height - r_newrefdef.y * vid.height // vid.height)
	y2 = math.ceil(vid.height - (r_newrefdef.y + r_newrefdef.height) * vid.height // vid.height)

	w = x2 - x
	h = y - y2

	GL.glViewport (x, y2, w, h)

	#
	# set up projection matrix
	#
	screenaspect = float(r_newrefdef.width/r_newrefdef.height)
#	yfov = 2*atan((float)r_newrefdef.height/r_newrefdef.width)*180/M_PI;
	GL.glMatrixMode(GL.GL_PROJECTION)
	GL.glLoadIdentity ()
	MYgluPerspective (r_newrefdef.fov_y, screenaspect,  4,  4096)

	GL.glCullFace(GL.GL_FRONT)

	GL.glMatrixMode(GL.GL_MODELVIEW)
	GL.glLoadIdentity ()

	GL.glRotatef (-90,  1, 0, 0)		# put Z going up
	GL.glRotatef (90,  0, 0, 1)		# put Z going up
	GL.glRotatef (-r_newrefdef.viewangles[2],  1, 0, 0)
	GL.glRotatef (-r_newrefdef.viewangles[0],  0, 1, 0)
	GL.glRotatef (-r_newrefdef.viewangles[1],  0, 0, 1)
	GL.glTranslatef (-r_newrefdef.vieworg[0],  -r_newrefdef.vieworg[1],  -r_newrefdef.vieworg[2]);

#	if ( gl_state.camera_separation != 0 && gl_state.stereo_enabled )
#		qglTranslatef ( gl_state.camera_separation, 0, 0 );

	GL.glGetFloatv (GL.GL_MODELVIEW_MATRIX, r_world_matrix)

	#
	# set drawing parms
	#
	if gl_cull.value is not None:
		GL.glEnable(GL.GL_CULL_FACE)
	else:
		GL.glDisable(GL.GL_CULL_FACE)

	GL.glDisable(GL.GL_BLEND)
	GL.glDisable(GL.GL_ALPHA_TEST)
	GL.glEnable(GL.GL_DEPTH_TEST)


"""
=============
R_Clear
=============
"""
def R_Clear ():

	global gldepthmin, gldepthmax

	if gl_ztrick.value:
	
		#static int trickframe;

		if gl_clear.value:
			GL.glClear (GL.GL_COLOR_BUFFER_BIT)

		trickframe+=1
		if (trickframe & 1):
		
			gldepthmin = 0
			gldepthmax = 0.49999
			GL.glDepthFunc (GL.GL_LEQUAL)
		
		else:
		
			gldepthmin = 1
			gldepthmax = 0.5
			GL.glDepthFunc (GL.GL_GEQUAL)
		
	else:
	
		if gl_clear.value:
			GL.glClear (GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		else:
			GL.glClear (GL.GL_DEPTH_BUFFER_BIT)
		gldepthmin = 0
		gldepthmax = 1
		GL.glDepthFunc (GL.GL_LEQUAL)
	
	GL.glDepthRange (gldepthmin, gldepthmax)

"""

void R_Flash( void )
{
	R_PolyBlend ();
}

/*
================
R_RenderView

r_newrefdef must be set before the first call
================
"""
def R_RenderView (fd): #refdef_t *

	global r_norefresh, r_newrefdef

	if r_norefresh.value:
		return
	
	r_newrefdef = copy.deepcopy(fd)
	
	if r_worldmodel is None and not ( r_newrefdef.rdflags & q_shared.RDF_NOWORLDMODEL ):
		ri.Sys_Error (q_shared.ERR_DROP, "R_RenderView: NULL worldmodel")
	"""
	if (r_speeds->value)
	{
		c_brush_polys = 0;
		c_alias_polys = 0;
	}

	R_PushDlights ();

	if (gl_finish->value)
		qglFinish ();

	"""
	R_SetupFrame ()

	R_SetFrustum ()

	R_SetupGL ()
	"""

	R_MarkLeaves ();	// done here so we know if we're in water

	"""
	gl_rsurf.R_DrawWorld ()
	"""

	R_DrawEntitiesOnList ();

	R_RenderDlights ();

	R_DrawParticles ();

	R_DrawAlphaSurfaces ();

	R_Flash();

	if (r_speeds.value)
	{
		ri.Con_Printf (q_shared.PRINT_ALL, "%4i wpoly %4i epoly %i tex %i lmaps\n",
			c_brush_polys, 
			c_alias_polys, 
			c_visible_textures, 
			c_visible_lightmaps); 
	}
	"""




def	R_SetGL2D ():

	# set 2D virtual screen size
	GL.glViewport (0,0, vid.width, vid.height)
	GL.glMatrixMode(GL.GL_PROJECTION)
	GL.glLoadIdentity ()
	GL.glOrtho  (0, vid.width, vid.height, 0, -99999, 99999)
	GL.glMatrixMode(GL.GL_MODELVIEW)
	GL.glLoadIdentity ()
	GL.glDisable (GL.GL_DEPTH_TEST)
	GL.glDisable (GL.GL_CULL_FACE)
	GL.glDisable (GL.GL_BLEND)
	GL.glEnable (GL.GL_ALPHA_TEST)
	GL.glColor4f (1,1,1,1)


"""
static void GL_DrawColoredStereoLinePair( float r, float g, float b, float y )
{
	qglColor3f( r, g, b );
	qglVertex2f( 0, y );
	qglVertex2f( vid.width, y );
	qglColor3f( 0, 0, 0 );
	qglVertex2f( 0, y + 1 );
	qglVertex2f( vid.width, y + 1 );
}

static void GL_DrawStereoPattern( void )
{
	int i;

	if ( !( gl_config.renderer & GL_RENDERER_INTERGRAPH ) )
		return;

	if ( !gl_state.stereo_enabled )
		return;

	R_SetGL2D();

	qglDrawBuffer( GL_BACK_LEFT );

	for ( i = 0; i < 20; i++ )
	{
		qglBegin( GL_LINES );
			GL_DrawColoredStereoLinePair( 1, 0, 0, 0 );
			GL_DrawColoredStereoLinePair( 1, 0, 0, 2 );
			GL_DrawColoredStereoLinePair( 1, 0, 0, 4 );
			GL_DrawColoredStereoLinePair( 1, 0, 0, 6 );
			GL_DrawColoredStereoLinePair( 0, 1, 0, 8 );
			GL_DrawColoredStereoLinePair( 1, 1, 0, 10);
			GL_DrawColoredStereoLinePair( 1, 1, 0, 12);
			GL_DrawColoredStereoLinePair( 0, 1, 0, 14);
		qglEnd();
		
		GLimp_EndFrame();
	}
}


/*
====================
R_SetLightLevel

====================
"""
def R_SetLightLevel ():
	pass
	"""

	vec3_t		shadelight;

	if (r_newrefdef.rdflags & RDF_NOWORLDMODEL)
		return;

	// save off light value for server to look at (BIG HACK!)

	R_LightPoint (r_newrefdef.vieworg, shadelight);

	// pick the greatest component, which should be the same
	// as the mono value returned by software
	if (shadelight[0] > shadelight[1])
	{
		if (shadelight[0] > shadelight[2])
			r_lightlevel->value = 150*shadelight[0];
		else
			r_lightlevel->value = 150*shadelight[2];
	}
	else
	{
		if (shadelight[1] > shadelight[2])
			r_lightlevel->value = 150*shadelight[1];
		else
			r_lightlevel->value = 150*shadelight[2];
	}
	"""


"""
@@@@@@@@@@@@@@@@@@@@@
R_RenderFrame

@@@@@@@@@@@@@@@@@@@@@
"""
def R_RenderFrame (fd): #refdef_t *

	R_RenderView( fd )
	R_SetLightLevel ()
	R_SetGL2D ()




def R_Register():

	global r_norefresh, r_drawentities, r_drawworld, r_speeds, r_fullbright, r_novis, r_nocull, r_lerpmodels, r_lefthand, r_lightlevel, \
	gl_nosubimage, gl_allow_software, gl_vertex_arrays, \
	gl_particle_min_size, gl_particle_max_size, gl_particle_size, gl_particle_att_a, gl_particle_att_b, gl_particle_att_c, \
	gl_ext_swapinterval, gl_ext_palettedtexture, gl_ext_multitexture, gl_ext_pointparameters, gl_ext_compiled_vertex_array, \
	gl_log, gl_bitdepth, gl_drawbuffer, gl_driver, gl_lightmap, gl_shadows, gl_mode, gl_dynamic, gl_monolightmap, gl_modulate, gl_nobind, \
	gl_round_down, gl_picmip, gl_skymip, gl_showtris, gl_ztrick, gl_finish, gl_clear, gl_cull, gl_polyblend, gl_flashblend, gl_playermip, \
	gl_saturatelighting, gl_swapinterval, gl_texturemode, gl_texturealphamode, gl_texturesolidmode, gl_lockpvs, \
	gl_3dlabs_broken, vid_fullscreen, vid_gamma, vid_ref

	r_lefthand = ri.Cvar_Get( "hand", "0", q_shared.CVAR_USERINFO | q_shared.CVAR_ARCHIVE )
	r_norefresh = ri.Cvar_Get ("r_norefresh", "0", 0)
	r_fullbright = ri.Cvar_Get ("r_fullbright", "0", 0)
	r_drawentities = ri.Cvar_Get ("r_drawentities", "1", 0)
	r_drawworld = ri.Cvar_Get ("r_drawworld", "1", 0)
	r_novis = ri.Cvar_Get ("r_novis", "0", 0)
	r_nocull = ri.Cvar_Get ("r_nocull", "0", 0)
	r_lerpmodels = ri.Cvar_Get ("r_lerpmodels", "1", 0)
	r_speeds = ri.Cvar_Get ("r_speeds", "0", 0)

	r_lightlevel = ri.Cvar_Get ("r_lightlevel", "0", 0)

	gl_nosubimage = ri.Cvar_Get( "gl_nosubimage", "0", 0 )
	gl_allow_software = ri.Cvar_Get( "gl_allow_software", "0", 0 )

	gl_particle_min_size = ri.Cvar_Get( "gl_particle_min_size", "2", q_shared.CVAR_ARCHIVE )
	gl_particle_max_size = ri.Cvar_Get( "gl_particle_max_size", "40", q_shared.CVAR_ARCHIVE )
	gl_particle_size = ri.Cvar_Get( "gl_particle_size", "40", q_shared.CVAR_ARCHIVE )
	gl_particle_att_a = ri.Cvar_Get( "gl_particle_att_a", "0.01", q_shared.CVAR_ARCHIVE )
	gl_particle_att_b = ri.Cvar_Get( "gl_particle_att_b", "0.0", q_shared.CVAR_ARCHIVE )
	gl_particle_att_c = ri.Cvar_Get( "gl_particle_att_c", "0.01", q_shared.CVAR_ARCHIVE )

	gl_modulate = ri.Cvar_Get ("gl_modulate", "1", q_shared.CVAR_ARCHIVE )
	gl_log = ri.Cvar_Get( "gl_log", "0", 0 )
	gl_bitdepth = ri.Cvar_Get( "gl_bitdepth", "0", 0 )
	gl_mode = ri.Cvar_Get( "gl_mode", "3", q_shared.CVAR_ARCHIVE )
	gl_lightmap = ri.Cvar_Get ("gl_lightmap", "0", 0)
	gl_shadows = ri.Cvar_Get ("gl_shadows", "0", q_shared.CVAR_ARCHIVE )
	gl_dynamic = ri.Cvar_Get ("gl_dynamic", "1", 0)
	gl_nobind = ri.Cvar_Get ("gl_nobind", "0", 0)
	gl_round_down = ri.Cvar_Get ("gl_round_down", "1", 0)
	gl_picmip = ri.Cvar_Get ("gl_picmip", "0", 0)
	gl_skymip = ri.Cvar_Get ("gl_skymip", "0", 0)
	gl_showtris = ri.Cvar_Get ("gl_showtris", "0", 0)
	gl_ztrick = ri.Cvar_Get ("gl_ztrick", "0", 0)
	gl_finish = ri.Cvar_Get ("gl_finish", "0", q_shared.CVAR_ARCHIVE)
	gl_clear = ri.Cvar_Get ("gl_clear", "0", 0)
	gl_cull = ri.Cvar_Get ("gl_cull", "1", 0)
	gl_polyblend = ri.Cvar_Get ("gl_polyblend", "1", 0)
	gl_flashblend = ri.Cvar_Get ("gl_flashblend", "0", 0)
	gl_playermip = ri.Cvar_Get ("gl_playermip", "0", 0)
	gl_monolightmap = ri.Cvar_Get( "gl_monolightmap", "0", 0 )
	gl_driver = ri.Cvar_Get( "gl_driver", "opengl32", q_shared.CVAR_ARCHIVE )
	gl_texturemode = ri.Cvar_Get( "gl_texturemode", "GL_LINEAR_MIPMAP_NEAREST", q_shared.CVAR_ARCHIVE )
	gl_texturealphamode = ri.Cvar_Get( "gl_texturealphamode", "default", q_shared.CVAR_ARCHIVE )
	gl_texturesolidmode = ri.Cvar_Get( "gl_texturesolidmode", "default", q_shared.CVAR_ARCHIVE )
	gl_lockpvs = ri.Cvar_Get( "gl_lockpvs", "0", 0 )

	gl_vertex_arrays = ri.Cvar_Get( "gl_vertex_arrays", "0", q_shared.CVAR_ARCHIVE )

	gl_ext_swapinterval = ri.Cvar_Get( "gl_ext_swapinterval", "1", q_shared.CVAR_ARCHIVE )
	gl_ext_palettedtexture = ri.Cvar_Get( "gl_ext_palettedtexture", "1", q_shared.CVAR_ARCHIVE )
	gl_ext_multitexture = ri.Cvar_Get( "gl_ext_multitexture", "1", q_shared.CVAR_ARCHIVE )
	gl_ext_pointparameters = ri.Cvar_Get( "gl_ext_pointparameters", "1", q_shared.CVAR_ARCHIVE )
	gl_ext_compiled_vertex_array = ri.Cvar_Get( "gl_ext_compiled_vertex_array", "1", q_shared.CVAR_ARCHIVE )

	gl_drawbuffer = ri.Cvar_Get( "gl_drawbuffer", "GL_BACK", 0 )
	gl_swapinterval = ri.Cvar_Get( "gl_swapinterval", "1", q_shared.CVAR_ARCHIVE )

	gl_saturatelighting = ri.Cvar_Get( "gl_saturatelighting", "0", 0 )

	gl_3dlabs_broken = ri.Cvar_Get( "gl_3dlabs_broken", "1", q_shared.CVAR_ARCHIVE )

	vid_fullscreen = ri.Cvar_Get( "vid_fullscreen", "0", q_shared.CVAR_ARCHIVE )
	vid_gamma = ri.Cvar_Get( "vid_gamma", "1.0", q_shared.CVAR_ARCHIVE )
	vid_ref = ri.Cvar_Get( "vid_ref", "soft", q_shared.CVAR_ARCHIVE )

	ri.Cmd_AddCommand( "imagelist", gl_image.GL_ImageList_f )
	#ri.Cmd_AddCommand( "screenshot", GL_ScreenShot_f )
	#ri.Cmd_AddCommand( "modellist", Mod_Modellist_f )
	ri.Cmd_AddCommand( "gl_strings", gl_rmisc.GL_Strings_f )


"""
==================
R_SetMode
==================
"""
def R_SetMode (): # (returns qboolean)

	global vid, gl_mode, vid_fullscreen, gl_config, gl_state

	#rserr_t err;
	#qboolean fullscreen;

	if vid_fullscreen.modified and not gl_config.allow_cds:
	
		ri.Con_Printf( q_shared.PRINT_ALL, "R_SetMode() - CDS not allowed with this driver\n" )
		ri.Cvar_SetValue( "vid_fullscreen", not vid_fullscreen.value )
		vid_fullscreen.modified = False
	
	fullscreen = vid_fullscreen.value

	vid_fullscreen.modified = False
	gl_mode.modified = False

	err, vid.width, vid.height = gl_glx.GLimp_SetMode( vid.width, vid.height, gl_mode.value, fullscreen )
	if err == rserr_t.rserr_ok:
	
		gl_state.prev_mode = gl_mode.value
	
	else:
		if err == rserr_t.rserr_invalid_fullscreen:
		
			ri.Cvar_SetValue( "vid_fullscreen", 0)
			vid_fullscreen.modified = False
			ri.Con_Printf( q_shared.PRINT_ALL, "ref_gl::R_SetMode() - fullscreen unavailable in this mode\n" )
			err, vid.width, vid.height = gl_glx.GLimp_SetMode( vid.width, vid.height, gl_mode.value, False )
			if err == rserr_t.rserr_ok:
				return True
		
		elif err == rserr_t.rserr_invalid_mode:
		
			ri.Cvar_SetValue( "gl_mode", gl_state.prev_mode )
			gl_mode.modified = False
			ri.Con_Printf( q_shared.PRINT_ALL, "ref_gl::R_SetMode() - invalid mode\n" )
		
		# try setting it back to something safe
		err, vid.width, vid.height = GLimp_SetMode( vid.width, vid.height, gl_state.prev_mode, False )
		if err != rserr_t.rserr_ok:
		
			ri.Con_Printf( q_shared.PRINT_ALL, "ref_gl::R_SetMode() - could not revert to safe mode\n" )
			return False
		

	return True


"""
===============
R_Init
===============
"""
def R_Init( hinstance, hWnd ): #void *, void *

	global gl_state, gl_ext_pointparameters, gl_ext_palettedtexture, gl_ext_multitexture

	"""
	char renderer_buffer[1000];
	char vendor_buffer[1000];
	int		err;
	int		j;
	extern float r_turbsin[256];

	for ( j = 0; j < 256; j++ )
	{
		r_turbsin[j] *= 0.5;
	}
	"""
	ri.Con_Printf (q_shared.PRINT_ALL, "ref_gl version: {}\n".format(REF_VERSION))
	
	gl_image.Draw_GetPalette ()
	R_Register()
	"""
	# initialize our QGL dynamic bindings
	if ( !QGL_Init( gl_driver->string ) )
	{
		QGL_Shutdown();
		ri.Con_Printf (q_shared.PRINT_ALL, "ref_gl::R_Init() - could not load \"%s\"\n", gl_driver->string );
		return -1;
	}
	"""
	# initialize OS-specific parts of OpenGL
	if not gl_glx.GLimp_Init( hinstance, hWnd ) :
	
		QGL_Shutdown()
		return -1
	
	# set our "safe" modes
	gl_state.prev_mode = 3
	
	# create the window and set up the context
	if not R_SetMode ():
	
		QGL_Shutdown()
		ri.Con_Printf (q_shared.PRINT_ALL, "ref_gl::R_Init() - could not R_SetMode()\n" )
		return -1
	
	"""
	ri.Vid_MenuInit();
	"""
	#
	# get our various GL strings
	#
	gl_config.vendor_string = glGetString (GL.GL_VENDOR)
	ri.Con_Printf (q_shared.PRINT_ALL, "GL_VENDOR: {}\n".format(gl_config.vendor_string) )
	gl_config.renderer_string = glGetString (GL.GL_RENDERER)
	ri.Con_Printf (q_shared.PRINT_ALL, "GL_RENDERER: {}\n".format(gl_config.renderer_string) )
	gl_config.version_string = glGetString (GL.GL_VERSION)
	ri.Con_Printf (q_shared.PRINT_ALL, "GL_VERSION: {}\n".format(gl_config.version_string) )
	gl_config.extensions = set(glGetString (GL.GL_EXTENSIONS).decode('utf-8').split(" "))
	ri.Con_Printf (q_shared.PRINT_ALL, "GL_EXTENSIONS: {}\n".format(gl_config.extensions) )
	"""
	strcpy( renderer_buffer, gl_config.renderer_string );
	strlwr( renderer_buffer );

	strcpy( vendor_buffer, gl_config.vendor_string );
	strlwr( vendor_buffer );

	if ( strstr( renderer_buffer, "voodoo" ) )
	{
		if ( !strstr( renderer_buffer, "rush" ) )
			gl_config.renderer = GL_RENDERER_VOODOO;
		else
			gl_config.renderer = GL_RENDERER_VOODOO_RUSH;
	}
	else if ( strstr( vendor_buffer, "sgi" ) )
		gl_config.renderer = GL_RENDERER_SGI;
	else if ( strstr( renderer_buffer, "permedia" ) )
		gl_config.renderer = GL_RENDERER_PERMEDIA2;
	else if ( strstr( renderer_buffer, "glint" ) )
		gl_config.renderer = GL_RENDERER_GLINT_MX;
	else if ( strstr( renderer_buffer, "glzicd" ) )
		gl_config.renderer = GL_RENDERER_REALIZM;
	else if ( strstr( renderer_buffer, "gdi" ) )
		gl_config.renderer = GL_RENDERER_MCD;
	else if ( strstr( renderer_buffer, "pcx2" ) )
		gl_config.renderer = GL_RENDERER_PCX2;
	else if ( strstr( renderer_buffer, "verite" ) )
		gl_config.renderer = GL_RENDERER_RENDITION;
	else
		gl_config.renderer = GL_RENDERER_OTHER;

	if ( toupper( gl_monolightmap->string[1] ) != 'F' )
	{
		if ( gl_config.renderer == GL_RENDERER_PERMEDIA2 )
		{
			ri.Cvar_Set( "gl_monolightmap", "A" );
			ri.Con_Printf( q_shared.PRINT_ALL, "...using gl_monolightmap 'a'\n" );
		}
		else if ( gl_config.renderer & GL_RENDERER_POWERVR ) 
		{
			ri.Cvar_Set( "gl_monolightmap", "0" );
		}
		else
		{
			ri.Cvar_Set( "gl_monolightmap", "0" );
		}
	}

	// power vr can't have anything stay in the framebuffer, so
	// the screen needs to redraw the tiled background every frame
	if ( gl_config.renderer & GL_RENDERER_POWERVR ) 
	{
		ri.Cvar_Set( "scr_drawall", "1" );
	}
	else
	{
		ri.Cvar_Set( "scr_drawall", "0" );
	}

#ifdef __linux__
	ri.Cvar_SetValue( "gl_finish", 1 );
#endif

	// MCD has buffering issues
	if ( gl_config.renderer == GL_RENDERER_MCD )
	{
		ri.Cvar_SetValue( "gl_finish", 1 );
	}

	if ( gl_config.renderer & GL_RENDERER_3DLABS )
	{
		if ( gl_3dlabs_broken->value )
			gl_config.allow_cds = false;
		else
			gl_config.allow_cds = true;
	}
	else
	{
		gl_config.allow_cds = true;
	}

	"""
	if gl_config.allow_cds:
		ri.Con_Printf( q_shared.PRINT_ALL, "...allowing CDS\n" )
	else:
		ri.Con_Printf( q_shared.PRINT_ALL, "...disabling CDS\n" )
	
	#
	# grab extensions
	#
	if "GL_EXT_compiled_vertex_array" in gl_config.extensions or \
		 "GL_SGI_compiled_vertex_array" in gl_config.extensions:
	
		ri.Con_Printf( q_shared.PRINT_ALL, "...enabling GL_EXT_compiled_vertex_array\n" )
		qgl_linux.qglLockArraysEXT = True #( void * ) qwglGetProcAddress( "glLockArraysEXT" )
		qgl_linux.qglUnlockArraysEXT = True #( void * ) qwglGetProcAddress( "glUnlockArraysEXT" )
	
	else:
	
		ri.Con_Printf( q_shared.PRINT_ALL, "...GL_EXT_compiled_vertex_array not found\n" )
	
	"""
#ifdef _WIN32
	if ( strstr( gl_config.extensions_string, "WGL_EXT_swap_control" ) )
	{
		qwglSwapIntervalEXT = ( BOOL (WINAPI *)(int)) qwglGetProcAddress( "wglSwapIntervalEXT" );
		ri.Con_Printf( q_shared.PRINT_ALL, "...enabling WGL_EXT_swap_control\n" );
	}
	else
	{
		ri.Con_Printf( q_shared.PRINT_ALL, "...WGL_EXT_swap_control not found\n" );
	}
#endif
	"""
	if "GL_EXT_point_parameters" in gl_config.extensions:
	
		if gl_ext_pointparameters.value:
		
			qgl_linux.qglPointParameterfEXT = True #( void (APIENTRY *)( GLenum, GLfloat ) ) qwglGetProcAddress( "glPointParameterfEXT" )
			qgl_linux.qglPointParameterfvEXT = True #( void (APIENTRY *)( GLenum, const GLfloat * ) ) qwglGetProcAddress( "glPointParameterfvEXT" )
			ri.Con_Printf( q_shared.PRINT_ALL, "...using GL_EXT_point_parameters\n" )
		
		else:
		
			ri.Con_Printf( q_shared.PRINT_ALL, "...ignoring GL_EXT_point_parameters\n" )
		
	
	else:
	
		ri.Con_Printf( q_shared.PRINT_ALL, "...GL_EXT_point_parameters not found\n" );
	
	"""
#ifdef __linux__
	if ( strstr( gl_config.extensions_string, "3DFX_set_global_palette" ))
	{
		if ( gl_ext_palettedtexture->value )
		{
			ri.Con_Printf( q_shared.PRINT_ALL, "...using 3DFX_set_global_palette\n" );
			qgl3DfxSetPaletteEXT = ( void ( APIENTRY * ) (GLuint *) )qwglGetProcAddress( "gl3DfxSetPaletteEXT" );
			qgl_linux.qglColorTableEXT = Fake_glColorTableEXT;
		}
		else
		{
			ri.Con_Printf( q_shared.PRINT_ALL, "...ignoring 3DFX_set_global_palette\n" );
		}
	}
	else
	{
		ri.Con_Printf( q_shared.PRINT_ALL, "...3DFX_set_global_palette not found\n" );
	}
#endif
	"""
	if qgl_linux.qglColorTableEXT is None and \
		"GL_EXT_paletted_texture" in gl_config.extensions and \
		"GL_EXT_shared_texture_palette" in gl_config.extensions:
	
		if gl_ext_palettedtexture.value:
		
			ri.Con_Printf( q_shared.PRINT_ALL, "...using GL_EXT_shared_texture_palette\n" )
			qgl_linux.qglColorTableEXT = True #( void ( APIENTRY * ) ( int, int, int, int, int, const void * ) ) qwglGetProcAddress( "glColorTableEXT" )
		
		else:
		
			ri.Con_Printf( q_shared.PRINT_ALL, "...ignoring GL_EXT_shared_texture_palette\n" )
		
	
	else:
	
		ri.Con_Printf( q_shared.PRINT_ALL, "...GL_EXT_shared_texture_palette not found\n" )
	
	
	if "GL_ARB_multitexture" in gl_config.extensions:
	
		if gl_ext_multitexture.value:
		
			ri.Con_Printf( q_shared.PRINT_ALL, "...using GL_ARB_multitexture\n" );
			qgl_linux.qglMTexCoord2fSGIS = True #( void * ) qwglGetProcAddress( "glMultiTexCoord2fARB" );
			qgl_linux.qglActiveTextureARB = True #( void * ) qwglGetProcAddress( "glActiveTextureARB" );
			qgl_linux.qglClientActiveTextureARB = True #( void * ) qwglGetProcAddress( "glClientActiveTextureARB" );
			#GL_TEXTURE0 = GL_TEXTURE0_ARB;
			#GL_TEXTURE1 = GL_TEXTURE1_ARB;
		
		else:
		
			ri.Con_Printf( q_shared.PRINT_ALL, "...ignoring GL_ARB_multitexture\n" );
		
	
	else:
	
		ri.Con_Printf( q_shared.PRINT_ALL, "...GL_ARB_multitexture not found\n" )
	
	"""
	if ( strstr( gl_config.extensions_string, "GL_SGIS_multitexture" ) )
	{
		if ( qglActiveTextureARB )
		{
			ri.Con_Printf( q_shared.PRINT_ALL, "...GL_SGIS_multitexture deprecated in favor of ARB_multitexture\n" );
		}
		else if ( gl_ext_multitexture->value )
		{
			ri.Con_Printf( q_shared.PRINT_ALL, "...using GL_SGIS_multitexture\n" );
			qglMTexCoord2fSGIS = ( void * ) qwglGetProcAddress( "glMTexCoord2fSGIS" );
			qglSelectTextureSGIS = ( void * ) qwglGetProcAddress( "glSelectTextureSGIS" );
			GL_TEXTURE0 = GL_TEXTURE0_SGIS;
			GL_TEXTURE1 = GL_TEXTURE1_SGIS;
		}
		else
		{
			ri.Con_Printf( q_shared.PRINT_ALL, "...ignoring GL_SGIS_multitexture\n" );
		}
	}
	else
	{
		ri.Con_Printf( q_shared.PRINT_ALL, "...GL_SGIS_multitexture not found\n" );
	}
	"""
	gl_rmisc.GL_SetDefaultState()

	#
	# draw our stereo patterns
	#

	# commented out until H3D pays us the money they owe us
	## GL_DrawStereoPattern()

	gl_image.GL_InitImages ()
	gl_model.Mod_Init ()
	#R_InitParticleTexture ()
	gl_draw.Draw_InitLocal ()


	err = GL.glGetError()
	if err != GL.GL_NO_ERROR:
		ri.Con_Printf (q_shared.PRINT_ALL, "glGetError() = 0x{:x}\n".format(err))

	# q2 extra code to catch opengl errors
	GL.glDebugMessageCallback(GL.GLDEBUGPROC(onGlDebugMessage), None)


def onGlDebugMessage(*args, **kwargs):
    println('glGetError args = {0}, kwargs = {1}'.format(args, kwargs))


"""
===============
R_Shutdown
===============
"""
def R_Shutdown ():

	"""
	ri.Cmd_RemoveCommand ("modellist");
	ri.Cmd_RemoveCommand ("screenshot");
	ri.Cmd_RemoveCommand ("imagelist");
	ri.Cmd_RemoveCommand ("gl_strings");

	Mod_FreeAll ();

	GL_ShutdownImages ();
	"""
	#
	# shut down OS specific OpenGL stuff like contexts, etc.
	#
	gl_glx.GLimp_Shutdown();
	"""
	/*
	** shutdown our QGL subsystem
	*/
	QGL_Shutdown();
	"""

"""
@@@@@@@@@@@@@@@@@@@@@
R_BeginFrame
@@@@@@@@@@@@@@@@@@@@@
"""
def R_BeginFrame( camera_separation ): #float

	global gl_state, gl_texturemode, gl_texturealphamode, gl_texturesolidmode

	gl_state.camera_separation = camera_separation
	"""
	/*
	** change modes if necessary
	*/
	if ( gl_mode->modified || vid_fullscreen->modified )
	{	// FIXME: only restart if CDS is required
		cvar_t	*ref;

		ref = ri.Cvar_Get ("vid_ref", "gl", 0);
		ref->modified = true;
	}

	if ( gl_log->modified )
	{
		GLimp_EnableLogging( gl_log->value );
		gl_log->modified = false;
	}

	if ( gl_log->value )
	{
		GLimp_LogNewFrame();
	}

	/*
	** update 3Dfx gamma -- it is expected that a user will do a vid_restart
	** after tweaking this value
	*/
	if ( vid_gamma->modified )
	{
		vid_gamma->modified = false;

		if ( gl_config.renderer & ( GL_RENDERER_VOODOO ) )
		{
			char envbuffer[1024];
			float g;

			g = 2.00 * ( 0.8 - ( vid_gamma->value - 0.5 ) ) + 1.0F;
			Com_sprintf( envbuffer, sizeof(envbuffer), "SSTV2_GAMMA=%f", g );
			putenv( envbuffer );
			Com_sprintf( envbuffer, sizeof(envbuffer), "SST_GAMMA=%f", g );
			putenv( envbuffer );
		}
	}
	"""
	gl_glx.GLimp_BeginFrame( camera_separation )

	#
	# go into 2D mode
	#
	GL.glViewport (0,0, vid.width, vid.height)
	GL.glMatrixMode(GL.GL_PROJECTION)
	GL.glLoadIdentity ()
	GL.glOrtho  (0, vid.width, vid.height, 0, -99999, 99999)
	GL.glMatrixMode(GL.GL_MODELVIEW)
	GL.glLoadIdentity ()
	GL.glDisable (GL.GL_DEPTH_TEST)
	GL.glDisable (GL.GL_CULL_FACE)
	GL.glDisable (GL.GL_BLEND)
	GL.glEnable (GL.GL_ALPHA_TEST)
	GL.glColor4f (1,1,1,1)
	"""
	#
	# draw buffer stuff
	#
	if ( gl_drawbuffer->modified )
	{
		gl_drawbuffer->modified = false;

		if ( gl_state.camera_separation == 0 || !gl_state.stereo_enabled )
		{
			if ( Q_stricmp( gl_drawbuffer->string, "GL_FRONT" ) == 0 )
				qglDrawBuffer( GL_FRONT );
			else
				qglDrawBuffer( GL_BACK );
		}
	}
	"""
	#
	# texturemode stuff
	#
	if gl_texturemode.modified:
	
		gl_image.GL_TextureMode( gl_texturemode.string )
		gl_texturemode.modified = False
	

	if gl_texturealphamode.modified:
	
		gl_image.GL_TextureAlphaMode( gl_texturealphamode.string )
		gl_texturealphamode.modified = False
	

	if gl_texturesolidmode.modified:
	
		gl_image.GL_TextureSolidMode( gl_texturesolidmode.string )
		gl_texturesolidmode.modified = False

	
	#
	# swapinterval stuff
	#
	gl_rmisc.GL_UpdateSwapInterval()
	
	#
	# clear screen if desired
	#
	R_Clear ()


"""
=============
R_SetPalette
=============
*/
"""
r_rawpalette = [0]*256 #unsigned[256];

def R_SetPalette (palette): #const unsigned char *
	
	#int		i;
	global r_rawpalette

	#byte *rp = ( byte * ) r_rawpalette;

	if palette is not None:
	
		for i in range(256):
		
			c = [0, 0, 0, 0]
			c[0] = palette[i*3+0]
			c[1] = palette[i*3+1]
			c[2] = palette[i*3+2]
			c[3] = 0xff
			r_rawpalette[i] = struct.unpack("<L", struct.pack("<BBBB", *c))[0]
		
	else:
	
		for i in range(256):
		
			c = gl_image.d_8to24table[i]
			r_rawpalette[i] = struct.unpack("<L", struct.pack("<BBBB", c[0], c[1], c[2], 0xff))[0]
	
	gl_image.GL_SetTexturePalette( r_rawpalette )

	GL.glClearColor (0,0,0,0)
	GL.glClear (GL.GL_COLOR_BUFFER_BIT)
	GL.glClearColor (1,0, 0.5 , 0.5)


"""
** R_DrawBeam
*/
void R_DrawBeam( entity_t *e )
{
#define NUM_BEAM_SEGS 6

	int	i;
	float r, g, b;

	vec3_t perpvec;
	vec3_t direction, normalized_direction;
	vec3_t	start_points[NUM_BEAM_SEGS], end_points[NUM_BEAM_SEGS];
	vec3_t oldorigin, origin;

	oldorigin[0] = e->oldorigin[0];
	oldorigin[1] = e->oldorigin[1];
	oldorigin[2] = e->oldorigin[2];

	origin[0] = e->origin[0];
	origin[1] = e->origin[1];
	origin[2] = e->origin[2];

	normalized_direction[0] = direction[0] = oldorigin[0] - origin[0];
	normalized_direction[1] = direction[1] = oldorigin[1] - origin[1];
	normalized_direction[2] = direction[2] = oldorigin[2] - origin[2];

	if ( VectorNormalize( normalized_direction ) == 0 )
		return;

	PerpendicularVector( perpvec, normalized_direction );
	VectorScale( perpvec, e->frame / 2, perpvec );

	for ( i = 0; i < 6; i++ )
	{
		RotatePointAroundVector( start_points[i], normalized_direction, perpvec, (360.0/NUM_BEAM_SEGS)*i );
		VectorAdd( start_points[i], origin, start_points[i] );
		VectorAdd( start_points[i], direction, end_points[i] );
	}

	qglDisable( GL_TEXTURE_2D );
	qglEnable( GL_BLEND );
	qglDepthMask( GL_FALSE );

	r = ( d_8to24table[e->skinnum & 0xFF] ) & 0xFF;
	g = ( d_8to24table[e->skinnum & 0xFF] >> 8 ) & 0xFF;
	b = ( d_8to24table[e->skinnum & 0xFF] >> 16 ) & 0xFF;

	r *= 1/255.0F;
	g *= 1/255.0F;
	b *= 1/255.0F;

	qglColor4f( r, g, b, e->alpha );

	qglBegin( GL_TRIANGLE_STRIP );
	for ( i = 0; i < NUM_BEAM_SEGS; i++ )
	{
		qglVertex3fv( start_points[i] );
		qglVertex3fv( end_points[i] );
		qglVertex3fv( start_points[(i+1)%NUM_BEAM_SEGS] );
		qglVertex3fv( end_points[(i+1)%NUM_BEAM_SEGS] );
	}
	qglEnd();

	qglEnable( GL_TEXTURE_2D );
	qglDisable( GL_BLEND );
	qglDepthMask( GL_TRUE );
}

//===================================================================


void	R_BeginRegistration (char *map);
struct model_s	*R_RegisterModel (char *name);
struct image_s	*R_RegisterSkin (char *name);
void R_SetSky (char *name, float rotate, vec3_t axis);
void	R_EndRegistration (void);

void	R_RenderFrame (refdef_t *fd);

struct image_s	*Draw_FindPic (char *name);

void	Draw_Pic (int x, int y, char *name);
void	Draw_Char (int x, int y, int c);
void	Draw_TileClear (int x, int y, int w, int h, char *name);
void	Draw_Fill (int x, int y, int w, int h, int c);
void	Draw_FadeScreen (void);

/*
@@@@@@@@@@@@@@@@@@@@@
GetRefAPI

@@@@@@@@@@@@@@@@@@@@@
"""
def GetRefAPI ( rimp ): #refimport_t (returns refexport_t)

	global ri

	re = ref.refexport_t()

	ri = rimp

	re.api_version = ref.API_VERSION

	re.BeginRegistration = gl_model.R_BeginRegistration
	re.RegisterModel = gl_model.R_RegisterModel
	re.RegisterSkin = gl_image.R_RegisterSkin
	re.RegisterPic = gl_draw.Draw_FindPic
	re.SetSky = gl_warp.R_SetSky
	re.EndRegistration = gl_model.R_EndRegistration

	re.RenderFrame = R_RenderFrame
	
	re.DrawGetPicSize = gl_draw.Draw_GetPicSize
	re.DrawPic = gl_draw.Draw_Pic
	re.DrawStretchPic = gl_draw.Draw_StretchPic
	re.DrawChar = gl_draw.Draw_Char
	re.DrawTileClear = gl_draw.Draw_TileClear
	re.DrawFill = gl_draw.Draw_Fill
	re.DrawFadeScreen= gl_draw.Draw_FadeScreen

	re.DrawStretchRaw = gl_draw.Draw_StretchRaw

	re.Init = R_Init
	re.Shutdown = R_Shutdown

	re.CinematicSetPalette = R_SetPalette

	re.BeginFrame = R_BeginFrame
	re.EndFrame = gl_glx.GLimp_EndFrame

	re.AppActivate = gl_glx.GLimp_AppActivate
	
	q_shared.Swap_Init ()

	return re


"""
#ifndef REF_HARD_LINKED
// this is only here so the functions in q_shared.c and q_shwin.c can link
void Sys_Error (char *error, ...)
{
	va_list		argptr;
	char		text[1024];

	va_start (argptr, error);
	vsprintf (text, error, argptr);
	va_end (argptr);

	ri.Sys_Error (ERR_FATAL, "%s", text);
}

void Com_Printf (char *fmt, ...)
{
	va_list		argptr;
	char		text[1024];

	va_start (argptr, fmt);
	vsprintf (text, fmt, argptr);
	va_end (argptr);

	ri.Con_Printf (q_shared.PRINT_ALL, "%s", text);
}

#endif
"""
