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

cvar.c -- dynamic variable tracking

#include "qcommon.h"
"""
from qcommon import cmd, common
from game import q_shared

cvar_vars = []

"""
============
Cvar_InfoValidate
============
"""
def Cvar_InfoValidate (s):

	if s.find("\\") != -1:
		return False;
	if s.find("\"") != -1:
		return False;
	if s.find(";") != -1:
		return False;
	return True;

"""
============
Cvar_FindVar
============
"""
def Cvar_FindVar (var_name): #char *

	for var in cvar_vars:
		if var_name == var.name:
			return var;

	return None;

"""
============
Cvar_VariableValue
============
"""
def Cvar_VariableValue (var_name): #char *

	var = Cvar_FindVar (var_name)
	if var is None:
		return 0.0
	return float (var.string)

"""
============
Cvar_VariableString
============
"""
def Cvar_VariableString (var_name): #char *

	var = Cvar_FindVar (var_name)
	if var is None:
		return ""
	return var.string

"""
============
Cvar_CompleteVariable
============
*/
char *Cvar_CompleteVariable (char *partial)
{
	cvar_t		*cvar;
	int			len;
	
	len = strlen(partial);
	
	if (!len)
		return NULL;
		
	// check exact match
	for (cvar=cvar_vars ; cvar ; cvar=cvar.next)
		if (!strcmp (partial,cvar.name))
			return cvar.name;

	// check partial match
	for (cvar=cvar_vars ; cvar ; cvar=cvar.next)
		if (!strncmp (partial,cvar.name, len))
			return cvar.name;

	return NULL;
}

"""
"""
============
Cvar_Get

If the variable already exists, the value will not be set
The flags will be or'ed in if the variable exists.
============
"""
def Cvar_Get (var_name, var_value, flags):  #char *, char *, int (returns cvar_t *)

	if flags & (q_shared.CVAR_USERINFO | q_shared.CVAR_SERVERINFO):
	
		if not Cvar_InfoValidate (var_name):
		
			common.Com_Printf("invalid info cvar name\n")
			return None

	var = Cvar_FindVar (var_name)
	if var is not None:
	
		var.flags |= flags
		return var
	
	if var_value is None:
		return None

	if flags & (q_shared.CVAR_USERINFO | q_shared.CVAR_SERVERINFO):
	
		if not Cvar_InfoValidate (var_value):
		
			common.Com_Printf("invalid info cvar value\n")
			return None
		
	var = q_shared.cvar_t()
	var.name = var_name
	var.string = var_value
	var.modified = True
	try:
		var.value = float(var.string)
	except ValueError:
		var.value = None
	var.flags = flags

	cvar_vars.insert(0, var)

	return var

"""
============
Cvar_Set2
============
"""
def Cvar_Set2 (var_name, value, force): #char *, char *, qboolean (returns cvar_t *)

	var = Cvar_FindVar (var_name)

	if var is None:
		# create it
		return Cvar_Get (var_name, value, 0);
	

	if var.flags & (q_shared.CVAR_USERINFO | q_shared.CVAR_SERVERINFO):
	
		if not Cvar_InfoValidate (value):
		
			common.Com_Printf("invalid info cvar value\n")
			return var
		
	
	if not force:
	
		if var.flags & q_shared.CVAR_NOSET:
		
			common.Com_Printf ("{} is write protected.\n".format(var_name))
			return var
		
		if var.flags & q_shared.CVAR_LATCH:
		
			if var.latched_string:
				if value == var.latched_string:
					return var
			else:
				if value == var.string:
					return var
			

			if Com_ServerState():
			
				common.Com_Printf ("{} will be changed for next game.\n".format(var_name))
				var.latched_string = value
			
			else:
			
				var.string = value
				try:
					var.value = float(var.string)
				except ValueError:
					var.value = None
				if var.name == "game":
				
					FS_SetGamedir (var.string);
					FS_ExecAutoexec ();
				
			
			return var
		
	
	else:
		if var.latched_string:
			var.latched_string = None
		
	if value == var.string:
		return var		# not changed

	var.modified = True

	if var.flags & q_shared.CVAR_USERINFO:
		userinfo_modified = True	# transmit at next oportunity
	
	var.string = value
	try:
		var.value = float(var.string)
	except ValueError:
		var.value = None

	return var

"""
============
Cvar_ForceSet
============
"""
def Cvar_ForceSet (var_name, value):

	return Cvar_Set2 (var_name, value, True)

"""
============
Cvar_Set
============
"""
def Cvar_Set (var_name, value): #char *, char * (returns cvar_t *)

	return Cvar_Set2 (var_name, value, False)

"""
============
Cvar_FullSet
============
*/
cvar_t *Cvar_FullSet (char *var_name, char *value, int flags)
{
	cvar_t	*var;
	
	var = Cvar_FindVar (var_name);
	if (!var)
	{	// create it
		return Cvar_Get (var_name, value, flags);
	}

	var.modified = true;

	if (var.flags & q_shared.CVAR_USERINFO)
		userinfo_modified = true;	// transmit at next oportunity
	
	Z_Free (var.string);	// free the old value string
	
	var.string = CopyString(value);
	var.value = atof (var.string);
	var.flags = flags;

	return var;
}

/*
============
Cvar_SetValue
============
"""
def Cvar_SetValue (var_name, value): #char *, float

	#char	val[32];

	#if (value == (int)value)
	#	Com_sprintf (val, sizeof(val), "%i",(int)value);
	#else
	#	Com_sprintf (val, sizeof(val), "%f",value);
	Cvar_Set (var_name, str(value))


"""
============
Cvar_GetLatchedVars

Any variables with latched values will now be updated
============
*/
void Cvar_GetLatchedVars (void)
{
	cvar_t	*var;

	for (var = cvar_vars ; var ; var = var.next)
	{
		if (!var.latched_string)
			continue;
		Z_Free (var.string);
		var.string = var.latched_string;
		var.latched_string = NULL;
		var.value = atof(var.string);
		if (!strcmp(var.name, "game"))
		{
			FS_SetGamedir (var.string);
			FS_ExecAutoexec ();
		}
	}
}

"""
"""
============
Cvar_Command

Handles variable inspection and changing from the console
============
"""
def Cvar_Command ():

	# check variables
	v = Cvar_FindVar (cmd.Cmd_Argv(0))
	if v is None:
		return False
		
	# perform a variable print or set
	if cmd.Cmd_Argc() == 1:
	
		common.Com_Printf ("\"{}\" is \"{}\"\n".format(v.name, v.string))
		return True
	
	Cvar_Set (v.name, cmd.Cmd_Argv(1))
	return True

"""
============
Cvar_Set_f

Allows setting and defining of arbitrary cvars from console
============
"""
def Cvar_Set_f ():

	c = cmd.Cmd_Argc()
	if c != 3 and c != 4:
	
		common.Com_Printf ("usage: set <variable> <value> [u / s]\n")
		return
	
	if c == 4:
	
		flags = 0
		if cmd.Cmd_Argv(3) == "u":
			flags = CVAR_USERINFO;
		elif cmd.Cmd_Argv(3) == "s":
			flags = CVAR_SERVERINFO;
		else:		
			common.Com_Printf ("flags can only be 'u' or 's'\n")
			return

		Cvar_FullSet (cmd.Cmd_Argv(1), cmd.Cmd_Argv(2), flags)

	else:
		Cvar_Set (cmd.Cmd_Argv(1), cmd.Cmd_Argv(2))

"""
============
Cvar_WriteVariables

Appends lines containing "set variable value" for all variables
with the archive flag set to true.
============
*/
void Cvar_WriteVariables (char *path)
{
	cvar_t	*var;
	char	buffer[1024];
	FILE	*f;

	f = fopen (path, "a");
	for (var = cvar_vars ; var ; var = var.next)
	{
		if (var.flags & CVAR_ARCHIVE)
		{
			Com_sprintf (buffer, sizeof(buffer), "set %s \"%s\"\n", var.name, var.string);
			fprintf (f, "%s", buffer);
		}
	}
	fclose (f);
}

"""
"""
============
Cvar_List_f

============
"""

def Cvar_List_f ():

	i = 0;
	for var in cvar_vars:

		if var.flags & q_shared.CVAR_ARCHIVE:
			common.Com_Printf ("*")
		else:
			common.Com_Printf (" ")
		if var.flags & q_shared.CVAR_USERINFO:
			common.Com_Printf ("U")
		else:
			common.Com_Printf (" ")
		if var.flags & q_shared.CVAR_SERVERINFO:
			common.Com_Printf ("S")
		else:
			common.Com_Printf (" ")
		if var.flags & q_shared.CVAR_NOSET:
			common.Com_Printf ("-")
		elif var.flags & q_shared.CVAR_LATCH:
			common.Com_Printf ("L")
		else:
			common.Com_Printf (" ")
		common.Com_Printf (" {} \"{}\"\n".format(var.name, var.string))

	common.Com_Printf ("{} cvars\n".format(len(cvar_vars)))

"""

qboolean userinfo_modified;


char	*Cvar_BitInfo (int bit)
{
	static char	info[MAX_INFO_STRING];
	cvar_t	*var;

	info[0] = 0;

	for (var = cvar_vars ; var ; var = var.next)
	{
		if (var.flags & bit)
			Info_SetValueForKey (info, var.name, var.string);
	}
	return info;
}

// returns an info string containing all the CVAR_USERINFO cvars
char	*Cvar_Userinfo (void)
{
	return Cvar_BitInfo (CVAR_USERINFO);
}

// returns an info string containing all the CVAR_SERVERINFO cvars
char	*Cvar_Serverinfo (void)
{
	return Cvar_BitInfo (CVAR_SERVERINFO);
}

"""
"""
============
Cvar_Init

Reads in all archived cvars
============
"""
def Cvar_Init():

	cmd.Cmd_AddCommand ("set", Cvar_Set_f)
	cmd.Cmd_AddCommand ("cvarlist", Cvar_List_f)


