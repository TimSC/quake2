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
from game import q_shared
from client import cl_main
"""
// cl_newfx.c -- MORE entity effects parsing and management

#include "client.h"
"""


"""
======
vectoangles2 - this is duplicated in the game DLL, but I need it here.
======
"""
def vectoangles2 (value1, angles): #vec3_t, vec3_t
	pass
	"""
	float	forward;
	float	yaw, pitch;
	
	if (value1[1] == 0 && value1[0] == 0)
	{
		yaw = 0;
		if (value1[2] > 0)
			pitch = 90;
		else
			pitch = 270;
	}
	else
	{
	// PMM - fixed to correct for pitch of 0
		if (value1[0])
			yaw = (atan2(value1[1], value1[0]) * 180 / M_PI);
		else if (value1[1] > 0)
			yaw = 90;
		else
			yaw = 270;

		if (yaw < 0)
			yaw += 360;

		forward = sqrt (value1[0]*value1[0] + value1[1]*value1[1]);
		pitch = (atan2(value1[2], forward) * 180 / M_PI);
		if (pitch < 0)
			pitch += 360;
	}

	angles[PITCH] = -pitch;
	angles[YAW] = yaw;
	angles[ROLL] = 0;
	"""


def CL_Flashlight (ent, pos): #int, vec3_t
	pass
	"""
	cdlight_t	*dl;

	dl = CL_AllocDlight (ent);
	VectorCopy (pos,  dl->origin);
	dl->radius = 400;
	dl->minlight = 250;
	dl->die = cl.time + 100;
	dl->color[0] = 1;
	dl->color[1] = 1;
	dl->color[2] = 1;
	"""


"""
======
CL_ColorFlash - flash of light
======
"""
def CL_ColorFlash (pos, ent, intensity, r, g, b): #vec3_t, int, int, float, float, float
	pass
	"""
	cdlight_t	*dl;

	if((vidref_val == VIDREF_SOFT) && ((r < 0) || (g<0) || (b<0)))
	{
		intensity = -intensity;
		r = -r;
		g = -g;
		b = -b;
	}

	dl = CL_AllocDlight (ent);
	VectorCopy (pos,  dl->origin);
	dl->radius = intensity;
	dl->minlight = 250;
	dl->die = cl.time + 100;
	dl->color[0] = r;
	dl->color[1] = g;
	dl->color[2] = b;
	"""


"""
======
CL_DebugTrail
======
"""
def CL_DebugTrail (start, end): #vec3_t, vec3_t
	pass
	"""
	vec3_t		move;
	vec3_t		vec;
	float		len;
//	int			j;
	cparticle_t	*p;
	float		dec;
	vec3_t		right, up;
//	int			i;
//	float		d, c, s;
//	vec3_t		dir;

	VectorCopy (start, move);
	VectorSubtract (end, start, vec);
	len = VectorNormalize (vec);

	MakeNormalVectors (vec, right, up);

//	VectorScale(vec, RT2_SKIP, vec);

//	dec = 1.0;
//	dec = 0.75;
	dec = 3;
	VectorScale (vec, dec, vec);
	VectorCopy (start, move);

	while (len > 0)
	{
		len -= dec;

		if (!free_particles)
			return;
		p = free_particles;
		free_particles = p->next;
		p->next = active_particles;
		active_particles = p;

		p->time = cl.time;
		VectorClear (p->accel);
		VectorClear (p->vel);
		p->alpha = 1.0;
		p->alphavel = -0.1;
//		p->alphavel = 0;
		p->color = 0x74 + (rand()&7);
		VectorCopy (move, p->org);
/*
		for (j=0 ; j<3 ; j++)
		{
			p->org[j] = move[j] + crand()*2;
			p->vel[j] = crand()*3;
			p->accel[j] = 0;
		}
*/
		VectorAdd (move, vec, move);
	}
	"""


"""
===============
CL_SmokeTrail
===============
"""
def CL_SmokeTrail (start, end, colorStart, colorRun, spacing): #vec3_t, vec3_t, int, int, int
	pass
	"""
	vec3_t		move;
	vec3_t		vec;
	float		len;
	int			j;
	cparticle_t	*p;

	VectorCopy (start, move);
	VectorSubtract (end, start, vec);
	len = VectorNormalize (vec);

	VectorScale (vec, spacing, vec);

	// FIXME: this is a really silly way to have a loop
	while (len > 0)
	{
		len -= spacing;

		if (!free_particles)
			return;
		p = free_particles;
		free_particles = p->next;
		p->next = active_particles;
		active_particles = p;
		VectorClear (p->accel);
		
		p->time = cl.time;

		p->alpha = 1.0;
		p->alphavel = -1.0 / (1+frand()*0.5);
		p->color = colorStart + (rand() % colorRun);
		for (j=0 ; j<3 ; j++)
		{
			p->org[j] = move[j] + crand()*3;
			p->accel[j] = 0;
		}
		p->vel[2] = 20 + crand()*5;

		VectorAdd (move, vec, move);
	}
	"""


def CL_ForceWall (start, end, color): #vec3_t, vec3_t, int
	pass
	"""
	vec3_t		move;
	vec3_t		vec;
	float		len;
	int			j;
	cparticle_t	*p;

	VectorCopy (start, move);
	VectorSubtract (end, start, vec);
	len = VectorNormalize (vec);

	VectorScale (vec, 4, vec);

	// FIXME: this is a really silly way to have a loop
	while (len > 0)
	{
		len -= 4;

		if (!free_particles)
			return;
		
		if (frand() > 0.3)
		{
			p = free_particles;
			free_particles = p->next;
			p->next = active_particles;
			active_particles = p;
			VectorClear (p->accel);
			
			p->time = cl.time;

			p->alpha = 1.0;
			p->alphavel =  -1.0 / (3.0+frand()*0.5);
			p->color = color;
			for (j=0 ; j<3 ; j++)
			{
				p->org[j] = move[j] + crand()*3;
				p->accel[j] = 0;
			}
			p->vel[0] = 0;
			p->vel[1] = 0;
			p->vel[2] = -40 - (crand()*10);
		}

		VectorAdd (move, vec, move);
	}
	"""


def CL_FlameEffects (ent, origin): #centity_t *, vec3_t
	pass
	"""
	int			n, count;
	int			j;
	cparticle_t	*p;

	count = rand() & 0xF;

	for(n=0;n<count;n++)
	{
		if (!free_particles)
			return;
			
		p = free_particles;
		free_particles = p->next;
		p->next = active_particles;
		active_particles = p;
		
		VectorClear (p->accel);
		p->time = cl.time;

		p->alpha = 1.0;
		p->alphavel = -1.0 / (1+frand()*0.2);
		p->color = 226 + (rand() % 4);
		for (j=0 ; j<3 ; j++)
		{
			p->org[j] = origin[j] + crand()*5;
			p->vel[j] = crand()*5;
		}
		p->vel[2] = crand() * -10;
		p->accel[2] = -PARTICLE_GRAVITY;
	}

	count = rand() & 0x7;

	for(n=0;n<count;n++)
	{
		if (!free_particles)
			return;
		p = free_particles;
		free_particles = p->next;
		p->next = active_particles;
		active_particles = p;
		VectorClear (p->accel);
		
		p->time = cl.time;

		p->alpha = 1.0;
		p->alphavel = -1.0 / (1+frand()*0.5);
		p->color = 0 + (rand() % 4);
		for (j=0 ; j<3 ; j++)
		{
			p->org[j] = origin[j] + crand()*3;
		}
		p->vel[2] = 20 + crand()*5;
	}
	"""


"""
===============
CL_GenericParticleEffect
===============
"""
def CL_GenericParticleEffect (org, dir, color, count, numcolors, dirspread, alphavel):
	pass
	"""
	int			i, j;
	cparticle_t	*p;
	float		d;

	for (i=0 ; i<count ; i++)
	{
		if (!free_particles)
			return;
		p = free_particles;
		free_particles = p->next;
		p->next = active_particles;
		active_particles = p;

		p->time = cl.time;
		if (numcolors > 1)
			p->color = color + (rand() & numcolors);
		else
			p->color = color;

		d = rand() & dirspread;
		for (j=0 ; j<3 ; j++)
		{
			p->org[j] = org[j] + ((rand()&7)-4) + d*dir[j];
			p->vel[j] = crand()*20;
		}

		p->accel[0] = p->accel[1] = 0;
		p->accel[2] = -PARTICLE_GRAVITY;
//		VectorCopy (accel, p->accel);
		p->alpha = 1.0;

		p->alphavel = -1.0 / (0.5 + frand()*alphavel);
//		p->alphavel = alphavel;
	}
	"""


"""
===============
CL_BubbleTrail2 (lets you control the # of bubbles by setting the distance between the spawns)

===============
"""
def CL_BubbleTrail2 (start, end, dist): #vec3_t, vec3_t, int
	pass
	"""
	vec3_t		move;
	vec3_t		vec;
	float		len;
	int			i, j;
	cparticle_t	*p;
	float		dec;

	VectorCopy (start, move);
	VectorSubtract (end, start, vec);
	len = VectorNormalize (vec);

	dec = dist;
	VectorScale (vec, dec, vec);

	for (i=0 ; i<len ; i+=dec)
	{
		if (!free_particles)
			return;

		p = free_particles;
		free_particles = p->next;
		p->next = active_particles;
		active_particles = p;

		VectorClear (p->accel);
		p->time = cl.time;

		p->alpha = 1.0;
		p->alphavel = -1.0 / (1+frand()*0.1);
		p->color = 4 + (rand()&7);
		for (j=0 ; j<3 ; j++)
		{
			p->org[j] = move[j] + crand()*2;
			p->vel[j] = crand()*10;
		}
		p->org[2] -= 4;
//		p->vel[2] += 6;
		p->vel[2] += 20;

		VectorAdd (move, vec, move);
	}
	"""


def CL_Heatbeam (start, end): #vec3_t, vec3_t
	pass
	"""
// multiple heatbeam variants exist in the original source, controlled by defines.
"""
