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
from qcommon import cvar, common, files
from game import q_shared
"""
// cmd.c -- Quake script command processing module

#include "qcommon.h"

void Cmd_ForwardToServer (void);
"""
MAX_ALIAS_NAME = 32

class cmdalias_t(object):

	def __init__(self):
		name = None #char	[MAX_ALIAS_NAME]
		value = None #char	*value

cmd_alias = [] #cmdalias_t	*

cmd_wait = None
ALIAS_LOOP_COUNT = 16
alias_count = None		# for detecting runaway loops

"""
//=============================================================================

============
Cmd_Wait_f

Causes execution of the remainder of the command buffer to be delayed until
next frame.  This allows commands like:
bind g "impulse 5 ; +attack ; wait ; -attack ; impulse 2"
============
"""
def Cmd_Wait_f ():
	
	global cmd_wait
	cmd_wait = True

"""
=============================================================================

						COMMAND BUFFER

=============================================================================
"""
cmd_text_maxsize=8192
cmd_text_buf="" #byte[8192]
defer_text_buf="" #byte[8192];
"""
============
Cbuf_Init
============
"""
def Cbuf_Init ():
	global cmd_text_buf, cmd_text_maxsize

	cmd_text_buf=""
	##SZ_Init (&cmd_text, cmd_text_buf, sizeof(cmd_text_buf));

"""
============
Cbuf_AddText

Adds command text at the end of the buffer
============
"""
def Cbuf_AddText (text): #char *
	global cmd_text_buf, cmd_text_maxsize

	l = len (text)

	if len(cmd_text_buf) + l >= cmd_text_maxsize:
	
		common.Com_Printf ("Cbuf_AddText: overflow\n")
		return
	
	cmd_text_buf += text
	##SZ_Write (&cmd_text, text, strlen (text));

"""
============
Cbuf_InsertText

Adds command text immediately after the current command
Adds a \n to the text
FIXME: actually change the command buffer to do less copying
============
"""
def Cbuf_InsertText (text): #char *

	global cmd_text_buf
	#char	*temp;
	#int		templen;

	# copy off any commands still remaining in the exec buffer
	temp = cmd_text_buf
	cmd_text_buf = ""
	
	# add the entire text of the file
	Cbuf_AddText (text);
	
	# add the copied off data
	cmd_text_buf += temp

"""
============
Cbuf_CopyToDefer
============
*/
void Cbuf_CopyToDefer (void)
{
	memcpy(defer_text_buf, cmd_text_buf, cmd_text.cursize);
	defer_text_buf[cmd_text.cursize] = 0;
	cmd_text.cursize = 0;
}

/*
============
Cbuf_InsertFromDefer
============
*/
void Cbuf_InsertFromDefer (void)
{
	Cbuf_InsertText (defer_text_buf);
	defer_text_buf[0] = 0;
}


"""
"""
============
Cbuf_ExecuteText
============
"""
def Cbuf_ExecuteText (exec_when, text): #int, char *
	pass
"""
	switch (exec_when):
	
	case EXEC_NOW:
		Cmd_ExecuteString (text);
		break;
	case EXEC_INSERT:
		Cbuf_InsertText (text);
		break;
	case EXEC_APPEND:
		Cbuf_AddText (text);
		break;
	default:
		Com_Error (ERR_FATAL, "Cbuf_ExecuteText: bad exec_when");
	
"""

"""
============
Cbuf_Execute
============
"""

def Cbuf_Execute ():

	global cmd_text_buf, alias_count, cmd_wait
	alias_count = 0;		# don't allow infinite alias loops

	while len(cmd_text_buf) > 0:
	
		# find a \n or ; line break
		quotes = 0;
		for i in range(len(cmd_text_buf)):
		
			if cmd_text_buf[i] == '"':
				quotes+=1
			if not (quotes&1) and cmd_text_buf[i] == ';':
				break	# don't break if inside a quoted string
			if cmd_text_buf[i] == '\n':
				break
		
		line = cmd_text_buf[:i]

		# delete the text from the command buffer and move remaining commands down
		# this is necessary because commands (exec, alias) can insert data at the
		# beginning of the text buffer

		cmd_text_buf = cmd_text_buf[i+1:]

		# execute the command line
		Cmd_ExecuteString (line)
		
		if cmd_wait:
		
			# skip out while text still remains in buffer, leaving it
			# for next frame
			cmd_wait = False
			break


"""
===============
Cbuf_AddEarlyCommands

Adds command line parameters as script statements
Commands lead with a +, and continue until another +

Set commands are added early, so they are guaranteed to be set before
the client and server initialize for the first time.

Other commands are added late, after all initialization is complete.
===============
"""
def Cbuf_AddEarlyCommands (clear):

	i = 0
	while i < common.COM_Argc():
	
		s = common.COM_Argv(i)

		if s != "+set":
			i += 1
			continue
		Cbuf_AddText ("set {} {}\n".format(common.COM_Argv(i+1), common.COM_Argv(i+2)))
		if clear:
		
			common.COM_ClearArgv(i);
			common.COM_ClearArgv(i+1);
			common.COM_ClearArgv(i+2);
		
		i += 3

"""
=================
Cbuf_AddLateCommands

Adds command line parameters as script statements
Commands lead with a + and continue until another + or -
quake +vid_ref gl +map amlev1

Returns true if any late commands were added, which
will keep the demoloop from immediately starting
=================
"""
def Cbuf_AddLateCommands (): #(returns qboolean)

	"""
	int		i, j;
	int		s;
	char	*text, *build, c;
	int		argc;
	qboolean	ret; """

	# build the combined string to parse from
	argc = common.COM_Argc()	
	if argc == 0:
		return False
		
	text = []
	for i in range(argc):

		text.append(common.COM_Argv(i))
		if i != argc-1:
			text.append(" ")

	text = "".join(text)
	text += " " #Extra space at end of string simplifies code in next stage
	if len(text) == 0:
		return False
	
	# pull out the commands
	build = []
	i = 0
	while i<len(text)-1:
	
		if text[i] == '+':
		
			i+=1

			j=i
			while j<len(text) and (text[j] != '+') and (text[j] != '-'): 
				j+=1
			
			build.append("{}\n".format(text[i:j]))

			i = j-1
		
		i += 1
	build = "".join(build)	

	ret = len(build) > 0
	if ret:
		Cbuf_AddText (build)
	
	return ret;

"""
==============================================================================

						SCRIPT COMMANDS

==============================================================================




===============
Cmd_Exec_f
===============
"""
def Cmd_Exec_f ():

	#char	*f, *f2;
	#int		len;

	if Cmd_Argc () != 2:
	
		common.Com_Printf ("exec <filename> : execute a script file\n")
		return
	
	length, data = files.FS_LoadFile (Cmd_Argv(1));
	if data is None:
	
		common.Com_Printf ("couldn't exec {}\n".format(Cmd_Argv(1)))
		return
	
	data = data.decode("ascii")

	common.Com_Printf ("execing {}\n".format(Cmd_Argv(1)))
	
	# the file doesn't have a trailing 0, so we need to copy it off

	Cbuf_InsertText (data);

"""
===============
Cmd_Echo_f

Just prints the rest of the line to the console
===============
"""
def Cmd_Echo_f ():
	
	for i in range(1, Cmd_Argc()):
		common.Com_Printf ("{} ".format(Cmd_Argv(i)));
	common.Com_Printf ("\n");

"""
===============
Cmd_Alias_f

Creates a new command that executes a command string (possibly ; seperated)
===============
"""
def Cmd_Alias_f ():


	"""
	cmdalias_t	*a;
	char		cmd[1024];
	int			i, c;
	char		*s;
	"""

	if Cmd_Argc() == 1:
	
		common.Com_Printf ("Current alias commands:\n")
		for a in cmd_alias:
			common.Com_Printf ("{} : {}\n".format(a.name, a.value))
		return
	
	
	s = Cmd_Argv(1)
	if len(s) >= MAX_ALIAS_NAME:
	
		common.Com_Printf ("Alias name is too long\n")
		return
	
	# if the alias already exists, reuse it
	alias = None
	for a in cmd_alias:
	
		if s == a.name:
			alias = a
			break;

	if alias is None:
	
		alias = cmdalias_t()
		cmd_alias.append(alias)
	
	alias.name = s

	# copy the rest of the command line
	cmd = []		# start out with a null string
	c = Cmd_Argc()
	for i in range(2, Cmd_Argc()):
	
		cmd.append(Cmd_Argv(i))
		if i != (c - 1):
			cmd.append(" ")
	
	cmd.append("\n")
	
	alias.value = "".join(cmd)

"""
=============================================================================

					COMMAND EXECUTION

=============================================================================
"""
class cmd_function_t(object):
	def __init__(self, nameIn=None, functionIn=None):

		name = nameIn #char *
		function = functionIn #xcommand_t

cmd_argv = [] #char *[MAX_STRING_TOKENS]
cmd_null_string = "" # char *
cmd_args = "" #char[MAX_STRING_CHARS]


cmd_functions = []		# possible commands to execute, cmd_function_t	*

"""
============
Cmd_Argc
============
"""
def Cmd_Argc():
	return len(cmd_argv)

"""
============
Cmd_Argv
============
"""
def Cmd_Argv(arg): #int

	if arg >= len(cmd_argv):
		return cmd_null_string
	return cmd_argv[arg]

"""
============
Cmd_Args

Returns a single string containing argv(1) to argv(argc()-1)
============
"""
def Cmd_Args():

	return cmd_args


"""
======================
Cmd_MacroExpandString
======================
*/
char *Cmd_MacroExpandString (char *text)
{
	int		i, j, count, len;
	qboolean	inquote;
	char	*scan;
	static	char	expanded[MAX_STRING_CHARS];
	char	temporary[MAX_STRING_CHARS];
	char	*token, *start;

	inquote = false;
	scan = text;

	len = strlen (scan);
	if (len >= MAX_STRING_CHARS)
	{
		common.Com_Printf ("Line exceeded %i chars, discarded.\n", MAX_STRING_CHARS);
		return NULL;
	}

	count = 0;

	for (i=0 ; i<len ; i++)
	{
		if (scan[i] == '"')
			inquote ^= 1;
		if (inquote)
			continue;	// don't expand inside quotes
		if (scan[i] != '$')
			continue;
		// scan out the complete macro
		start = scan+i+1;
		token = COM_Parse (&start);
		if (!start)
			continue;
	
		token = Cvar_VariableString (token);

		j = strlen(token);
		len += j;
		if (len >= MAX_STRING_CHARS)
		{
			common.Com_Printf ("Expanded line exceeded %i chars, discarded.\n", MAX_STRING_CHARS);
			return NULL;
		}

		strncpy (temporary, scan, i);
		strcpy (temporary+i, token);
		strcpy (temporary+i+j, start);

		strcpy (expanded, temporary);
		scan = expanded;
		i--;

		if (++count == 100)
		{
			common.Com_Printf ("Macro expansion loop, discarded.\n");
			return NULL;
		}
	}

	if (inquote)
	{
		common.Com_Printf ("Line has unmatched quote, discarded.\n");
		return NULL;
	}

	return scan;
}

"""
"""
============
Cmd_TokenizeString

Parses the given string into command line tokens.
$Cvars will be expanded unless they are in a quoted token
============
"""
def Cmd_TokenizeString (text, macroExpand): #char *, qboolean

	global cmd_argv, cmd_args

	# clear the args from the last string
	cmd_argv = []
	cmd_args = "";
	cursor = 0

	# macro expand the text
	#if (macroExpand)
	#	text = Cmd_MacroExpandString (text);
	if text is None or len(text) == 0:
		return;

	while 1:
		# skip whitespace up to a /n
		while cursor < len(text) and text[cursor].strip() == '' and text[cursor] != '\n':
			cursor += 1
		
		if cursor >= len(text):
			return;

		if text[cursor] == '\n':
			# a newline seperates commands in the buffer
			cursor += 1
			break
		
		if cursor >= len(text):
			return;

		# set cmd_args to everything after the first arg
		if len(cmd_argv) == 1:

			# strip off any trailing whitespace
			cmd_args = text[:cursor].strip()
					
		com_token, cursor = q_shared.COM_Parse (text, cursor)

		if cursor > len(text):
			return;

		if len(cmd_argv) < q_shared.MAX_STRING_TOKENS:	
			cmd_argv.append(com_token)

		if cursor >= len(text):
			return;
		
"""
============
Cmd_AddCommand
============
"""
def Cmd_AddCommand(cmd_name, function): #char *, xcommand_t

	# fail if the command is a variable name
	if len(cvar.Cvar_VariableString(cmd_name)) > 0:

		common.Com_Printf ("Cmd_AddCommand: {} already defined as a var\n".format(cmd_name))
		return;
	
	# fail if the command already exists
	for cmd in cmd_functions:
	
		if cmd_name == cmd.name:

			common.Com_Printf ("Cmd_AddCommand: {} already defined\n".format(cmd_name));
			return;

	cmd = cmd_function_t()
	cmd.name = cmd_name
	cmd.function = function
	cmd_functions.insert(0, cmd)


"""
============
Cmd_RemoveCommand
============
"""
def Cmd_RemoveCommand (cmd_name): #char *

	#cmd_function_t	*cmd, **back;
	found = None
	for cmd in cmd_functions:
	
		if cmd_name == cmd.name:
			found = cmd
			break
		
	if found is not None:
		cmd_functions.remove(cmd)
	else:	
		common.Com_Printf ("Cmd_RemoveCommand: %s not added\n", cmd_name);

"""
============
Cmd_Exists
============
"""
def Cmd_Exists (cmd_name): #char * (returns qboolean)

	#cmd_function_t	*cmd;

	for cmd in cmd_functions:
	
		if cmd_name == cmd.name:
			return True
	
	return False


"""
============
Cmd_CompleteCommand
============
*/
char *Cmd_CompleteCommand (char *partial)
{
	cmd_function_t	*cmd;
	int				len;
	cmdalias_t		*a;
	
	len = strlen(partial);
	
	if (!len)
		return NULL;
		
// check for exact match
	for (cmd=cmd_functions ; cmd ; cmd=cmd->next)
		if (!strcmp (partial,cmd->name))
			return cmd->name;
	for (a=cmd_alias ; a ; a=a->next)
		if (!strcmp (partial, a->name))
			return a->name;

// check for partial match
	for (cmd=cmd_functions ; cmd ; cmd=cmd->next)
		if (!strncmp (partial,cmd->name, len))
			return cmd->name;
	for (a=cmd_alias ; a ; a=a->next)
		if (!strncmp (partial, a->name, len))
			return a->name;

	return NULL;
}


"""
"""
============
Cmd_ExecuteString

A complete command line has been parsed, so try to execute it
FIXME: lookupnoadd the token to speed search?
============
"""
def Cmd_ExecuteString (text): #char *
	
	"""
	cmd_function_t	*cmd;
	cmdalias_t		*a;
	"""
	global cmd_argv, alias_count

	Cmd_TokenizeString (text, True)
	#common.Com_Printf ("{}\n".format(cmd_argv))

	# execute the command line
	if Cmd_Argc() == 0:
		return		# no tokens

	# check functions
	for cmd in cmd_functions:
	
		if not q_shared.Q_strcasecmp(cmd_argv[0], cmd.name):
		
			if cmd.function is None:
				# forward to server command
				Cmd_ExecuteString ("cmd %s".format(text))
			else:
				cmd.function()
			return
		
	
	# check alias
	for a in cmd_alias:
	
		if not q_shared.Q_strcasecmp (cmd_argv[0], a.name):
		
			alias_count += 1
			if alias_count == ALIAS_LOOP_COUNT:
			
				common.Com_Printf ("ALIAS_LOOP_COUNT\n")
				return
			
			Cbuf_InsertText (a.value)
			return

	# check cvars
	if cvar.Cvar_Command ():
		return

	# send it as a server command if we are connected
	#Cmd_ForwardToServer ();

"""
============
Cmd_List_f
============
"""
def Cmd_List_f ():
	
	i = 0;
	for cmd in cmd_functions:
		common.Com_Printf ("{}\n".format(cmd.name))
	common.Com_Printf ("{} commands\n".format(len(cmd_functions)))

"""
============
Cmd_Init
============
"""
def Cmd_Init ():

	# register our commands
	Cmd_AddCommand ("cmdlist",Cmd_List_f);
	Cmd_AddCommand ("exec",Cmd_Exec_f);
	Cmd_AddCommand ("echo",Cmd_Echo_f);
	Cmd_AddCommand ("alias",Cmd_Alias_f);
	Cmd_AddCommand ("wait", Cmd_Wait_f);

