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
from client import menu as menumod
from linux import vid_so, q_shlinux
"""
#include <string.h>
#include <ctype.h>

#include "client.h"
#include "qmenu.h"

static void	 Action_DoEnter( menuaction_s *a );
static void	 Action_Draw( menuaction_s *a );
static void  Menu_DrawStatusBar( const char *string );
static void	 Menulist_DoEnter( menulist_s *l );
static void	 MenuList_Draw( menulist_s *l );
static void	 Separator_Draw( menuseparator_s *s );
static void	 Slider_DoSlide( menuslider_s *s, int dir );
static void	 Slider_Draw( menuslider_s *s );
static void	 SpinControl_DoEnter( menulist_s *s );
static void	 SpinControl_Draw( menulist_s *s );
static void	 SpinControl_DoSlide( menulist_s *s, int dir );
"""
RCOLUMN_OFFSET  = 16
LCOLUMN_OFFSET  = -16
"""
extern refexport_t re;
extern viddef_t viddef;
"""
def VID_WIDTH(): return vid_so.viddef.width
def VID_HEIGHT(): return vid_so.viddef.height

def Draw_Char(x, y, num): 
	return vid_so.re.DrawChar(x, y, num)
def Draw_Fill(x, y, w, h, c):
	return vid_so.re.DrawFill(x, y, w, h, c)

def Action_DoEnter( a ): #menuaction_s *

	if a.callback is not None:
		a.callback( a )

def Action_Draw( a ): #menuaction_s *

	if a.flags & menumod.QMF_LEFT_JUSTIFY:
	
		if a.flags & menumod.QMF_GRAYED:
			Menu_DrawStringDark( a.x + a.parent.x + LCOLUMN_OFFSET, a.y + a.parent.y, a.name )
		else:
			Menu_DrawString( a.x + a.parent.x + LCOLUMN_OFFSET, a.y + a.parent.y, a.name )
	
	else:
	
		if a.flags & menumod.QMF_GRAYED:
			Menu_DrawStringR2LDark( a.x + a.parent.x + LCOLUMN_OFFSET, a.y + a.parent.y, a.name )
		else:
			Menu_DrawStringR2L( a.x + a.parent.x + LCOLUMN_OFFSET, a.y + a.parent.y, a.name )
	
	if a.ownerdraw is not None:
		a.ownerdraw( a )

"""
qboolean Field_DoEnter( menufield_s *f )
{
	if ( f.callback )
	{
		f.callback( f );
		return true;
	}
	return false;
}

void Field_Draw( menufield_s *f )
{
	int i;
	char tempbuffer[128]="";

	if ( f.name )
		Menu_DrawStringR2LDark( f.x + f.parent.x + LCOLUMN_OFFSET, f.y + f.parent.y, f.name );

	strncpy( tempbuffer, f->buffer + f->visible_offset, f->visible_length );

	Draw_Char( f.x + f.parent.x + 16, f.y + f.parent.y - 4, 18 );
	Draw_Char( f.x + f.parent.x + 16, f.y + f.parent.y + 4, 24 );

	Draw_Char( f.x + f.parent.x + 24 + f->visible_length * 8, f.y + f.parent.y - 4, 20 );
	Draw_Char( f.x + f.parent.x + 24 + f->visible_length * 8, f.y + f.parent.y + 4, 26 );

	for ( i = 0; i < f->visible_length; i++ )
	{
		Draw_Char( f.x + f.parent.x + 24 + i * 8, f.y + f.parent.y - 4, 19 );
		Draw_Char( f.x + f.parent.x + 24 + i * 8, f.y + f.parent.y + 4, 25 );
	}

	Menu_DrawString( f.x + f.parent.x + 24, f.y + f.parent.y, tempbuffer );

	if ( Menu_ItemAtCursor( f.parent ) == f )
	{
		int offset;

		if ( f->visible_offset )
			offset = f->visible_length;
		else
			offset = f->cursor;

		if ( ( ( int ) ( q_shlinux.Sys_Milliseconds() / 250 ) ) & 1 )
		{
			Draw_Char( f.x + f.parent.x + ( offset + 2 ) * 8 + 8,
					   f.y + f.parent.y,
					   11 );
		}
		else
		{
			Draw_Char( f.x + f.parent.x + ( offset + 2 ) * 8 + 8,
					   f.y + f.parent.y,
					   ' ' );
		}
	}
}
"""
def Field_Key( f,  key ): #menufield_s *, int (returns qboolean)

	return False
	"""
	extern int keydown[];

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

	if ( key > 127 )
	{
		switch ( key )
		{
		case K_DEL:
		default:
			return false;
		}
	}

	/*
	** support pasting from the clipboard
	*/
	if ( ( toupper( key ) == 'V' && keydown[K_CTRL] ) ||
		 ( ( ( key == K_INS ) || ( key == K_KP_INS ) ) && keydown[K_SHIFT] ) )
	{
		char *cbd;
		
		if ( ( cbd = Sys_GetClipboardData() ) != 0 )
		{
			strtok( cbd, "\n\r\b" );

			strncpy( f->buffer, cbd, f->length - 1 );
			f->cursor = strlen( f->buffer );
			f->visible_offset = f->cursor - f->visible_length;
			if ( f->visible_offset < 0 )
				f->visible_offset = 0;

			free( cbd );
		}
		return true;
	}

	switch ( key )
	{
	case K_KP_LEFTARROW:
	case K_LEFTARROW:
	case K_BACKSPACE:
		if ( f->cursor > 0 )
		{
			memmove( &f->buffer[f->cursor-1], &f->buffer[f->cursor], strlen( &f->buffer[f->cursor] ) + 1 );
			f->cursor--;

			if ( f->visible_offset )
			{
				f->visible_offset--;
			}
		}
		break;

	case K_KP_DEL:
	case K_DEL:
		memmove( &f->buffer[f->cursor], &f->buffer[f->cursor+1], strlen( &f->buffer[f->cursor+1] ) + 1 );
		break;

	case K_KP_ENTER:
	case K_ENTER:
	case K_ESCAPE:
	case K_TAB:
		return false;

	case K_SPACE:
	default:
		if ( !isdigit( key ) && ( f.flags & QMF_NUMBERSONLY ) )
			return false;

		if ( f->cursor < f->length )
		{
			f->buffer[f->cursor++] = key;
			f->buffer[f->cursor] = 0;

			if ( f->cursor > f->visible_length )
			{
				f->visible_offset++;
			}
		}
	}

	return true;
}
"""
def Menu_AddItem( menu, item ): #menuframework_s *, void *

	if len(menu.items) == 0:
		menu.nslots = 0

	if len(menu.items) < menumod.MAXMENUITEMS:
	
		menu.items.append(item)
		item.parent = menu
		menu.nitems += 1
	
	menu.nslots = Menu_TallySlots( menu )

"""
/*
** Menu_AdjustCursor
**
** This function takes the given menu, the direction, and attempts
** to adjust the menu's cursor so that it's at the next available
** slot.
*/
"""
def Menu_AdjustCursor( m,  direc ): #menuframework_s *, int


	#menucommon_s *citem;

	#
	# see if it's in a valid spot
	#
	if m.cursor >= 0 and m.cursor < len(m.items):
	
		citem = Menu_ItemAtCursor( m )
		if citem is not None:
		
			if citem.type != menumod.MTYPE_SEPARATOR:
				return
		
	

	#
	# it's not in a valid spot, so crawl in the direction indicated until we
	# find a valid spot
	#
	if direc == 1:
	
		while 1:
		
			citem = Menu_ItemAtCursor( m )
			if citem is not None:
				if citem.type != menumod.MTYPE_SEPARATOR:
					break
			m.cursor += direc
			if m.cursor >= len(m.items):
				m.cursor = 0
		
	
	else:
	
		while 1:
		
			citem = Menu_ItemAtCursor( m )
			if citem is not None:
				if citem.type != menumod.MTYPE_SEPARATOR:
					break
			m.cursor += direc
			if m.cursor < 0:
				m.cursor = len(m.items) - 1
		

def Menu_Center( menu ): #menuframework_s *

	height = menu.items[-1].y
	height += 10

	menu.y = ( VID_HEIGHT() - height ) // 2

def Menu_Draw( menu ): #menuframework_s *
	
	#int i;
	#menucommon_s *item;

	#
	# draw contents
	#
	for item in menu.items:
	
		if item.type == menumod.MTYPE_FIELD:
			Field_Draw( item )

		elif item.type == menumod.MTYPE_SLIDER:
			Slider_Draw( item )

		elif item.type == menumod.MTYPE_LIST:
			MenuList_Draw( item )

		elif item.type == menumod.MTYPE_SPINCONTROL:
			SpinControl_Draw( item )

		elif item.type == menumod.MTYPE_ACTION:
			Action_Draw( item )

		elif item.type == menumod.MTYPE_SEPARATOR:
			Separator_Draw( item )

	

	item = Menu_ItemAtCursor( menu )

	if item is not None and item.cursordraw is not None:
	
		item.cursordraw( item )
	
	elif menu.cursordraw is not None:
	
		menu.cursordraw( menu )
	
	
	elif item is not None and item.type != menumod.MTYPE_FIELD:
	
		if item.flags & menumod.QMF_LEFT_JUSTIFY:
		
			Draw_Char( menu.x + item.x - 24 + item.cursor_offset, menu.y + item.y, 12 + ( int ( q_shlinux.Sys_Milliseconds()//250 ) & 1 ) )
		
		else:
		
			Draw_Char( menu.x + item.cursor_offset, menu.y + item.y, 12 + ( int ( q_shlinux.Sys_Milliseconds()//250 ) & 1 ) )
		
	
	
	if item is not None:
	
		if item.statusbarfunc is not None:
			item.statusbarfunc( item )
		elif item.statusbar is not None:
			Menu_DrawStatusBar( item.statusbar )
		else:
			Menu_DrawStatusBar( menu.statusbar )

	else:
	
		Menu_DrawStatusBar( menu.statusbar )
	


def Menu_DrawStatusBar( string ): #const char *
	
	pass
	"""
	if ( string )
	{
		int l = strlen( string );
		int maxrow = VID_HEIGHT() / 8;
		int maxcol = VID_WIDTH() / 8;
		int col = maxcol / 2 - l / 2;

		Draw_Fill( 0, VID_HEIGHT()-8, VID_WIDTH(), 8, 4 );
		Menu_DrawString( col*8, VID_HEIGHT() - 8, string );
	}
	else
	{
		Draw_Fill( 0, VID_HEIGHT()-8, VID_WIDTH(), 8, 0 );
	}
}
"""
def Menu_DrawString( x, y, string ): #int, int, const char *

	for i, ch in enumerate(string):

		Draw_Char( ( x + i*8 ), y, ord(ch) )
	

def Menu_DrawStringDark( x, y, string ): #int, int, const char *

	for i, ch in enumerate(string):
	
		Draw_Char( ( x + i*8 ), y, ord(ch) + 128 )
	
def Menu_DrawStringR2L( x, y, string ): #int, int, const char *

	for i, ch in enumerate(string):
	
		Draw_Char( ( x - i*8 ), y, ord(string[-i-1]) )

def Menu_DrawStringR2LDark( x, y, string ): #int, int, const char *

	for i, ch in enumerate(string):
	
		Draw_Char( ( x - i*8 ), y, ord(string[-i-1])+128 )
	
def Menu_ItemAtCursor( m ): #menuframework_s * (returns void *)

	if m.cursor < 0 or m.cursor >= len(m.items):
		return None

	return m.items[m.cursor]


def Menu_SelectItem( s ): #menuframework_s * (returns qboolean)

	item = Menu_ItemAtCursor( s )

	if item is not None:
		
		if item.type == menumod.MTYPE_FIELD:
			return Field_DoEnter( item )
		elif item.type == menumod.MTYPE_ACTION:
			Action_DoEnter( item )
			return True
		elif item.type == menumod.MTYPE_LIST:
			## Menulist_DoEnter( item )
			return False
		elif item.type == menumod.MTYPE_SPINCONTROL:
			## SpinControl_DoEnter( item )
			return False
		
	return False


def Menu_SetStatusBar( m, string ): #menuframework_s *, const char *

	m.statusbar = string


def Menu_SlideItem( s, direc ): # menuframework_s *, int

	item = Menu_ItemAtCursor( s )

	if item is not None:
	
		if item.type == menumod.MTYPE_SLIDER:
			Slider_DoSlide( item, direc )

		elif item.type == menumod.MTYPE_SPINCONTROL:
			SpinControl_DoSlide( item, direc )

def Menu_TallySlots( menu ): #menuframework_s * (returns int)

	total = 0 #int

	for item in menu.items:
	
		if item.type == menumod.MTYPE_LIST:
			total += len(item.itemnames)		
		else:
			total += 1
		
	return total

"""
void Menulist_DoEnter( menulist_s *l )
{
	int start;

	start = l.y / 10 + 1;

	l->curvalue = l.parent->cursor - start;

	if ( l.callback )
		l.callback( l );
}
"""
def MenuList_Draw( l ): #menulist_s *
	pass
	"""
	const char **n;
	int y = 0;

	Menu_DrawStringR2LDark( l.x + l.parent.x + LCOLUMN_OFFSET, l.y + l.parent.y, l.name );

	n = l->itemnames;

  	Draw_Fill( l.x - 112 + l.parent.x, l.parent.y + l.y + l->curvalue*10 + 10, 128, 10, 16 );
	while ( *n )
	{
		Menu_DrawStringR2LDark( l.x + l.parent.x + LCOLUMN_OFFSET, l.y + l.parent.y + y + 10, *n );

		n++;
		y += 10;
	}
}
"""
def Separator_Draw( s ): #menuseparator_s *

	if s.name:
		Menu_DrawStringR2LDark( s.x + s.parent.x, s.y + s.parent.y, s.name )


def Slider_DoSlide( s, direc ): # menuslider_s *, int

	s.curvalue += direc

	if s.curvalue > s.maxvalue:
		s.curvalue = s.maxvalue
	elif s.curvalue < s.minvalue:
		s.curvalue = s.minvalue

	if s.callback is not None:
		s.callback( s )


SLIDER_RANGE = 10

def Slider_Draw( s ): #menuslider_s *

	#int	i;

	Menu_DrawStringR2LDark( s.x + s.parent.x + LCOLUMN_OFFSET,
		                s.y + s.parent.y, 
						s.name )

	s.range = ( s.curvalue - s.minvalue ) / ( s.maxvalue - s.minvalue )

	if s.range < 0.0:
		s.range = 0.0
	if s.range > 1.0:
		s.range = 1.0
	Draw_Char( s.x + s.parent.x + RCOLUMN_OFFSET, s.y + s.parent.y, 128)
	for i in range(SLIDER_RANGE):
		Draw_Char( RCOLUMN_OFFSET + s.x + i*8 + s.parent.x + 8, s.y + s.parent.y, 129)
	Draw_Char( RCOLUMN_OFFSET + s.x + i*8 + s.parent.x + 8, s.y + s.parent.y, 130)
	Draw_Char( int ( 8 + RCOLUMN_OFFSET + s.parent.x + s.x + (SLIDER_RANGE-1)*8 * s.range ), s.y + s.parent.y, 131)

"""
void SpinControl_DoEnter( menulist_s *s )
{
	s->curvalue++;
	if ( s->itemnames[s->curvalue] == 0 )
		s->curvalue = 0;

	if ( s.callback )
		s.callback( s );
}
"""
def SpinControl_DoSlide( s, direc ): #menulist_s *, int

	s.curvalue += direc

	if s.curvalue < 0:
		s.curvalue = 0
	elif s.curvalue >= len(s.itemnames):
		s.curvalue-=1

	if s.callback is not None:
		s.callback( s )

def SpinControl_Draw( s ): #menulist_s *

	if len(s.name) > 0:
	
		Menu_DrawStringR2LDark( s.x + s.parent.x + LCOLUMN_OFFSET, 
							s.y + s.parent.y, 
							s.name )
	
	if len(s.itemnames) == 0:
		return

	lineSplit = s.itemnames[s.curvalue].split('\n')
	if len(lineSplit) == 1:
		Menu_DrawString( RCOLUMN_OFFSET + s.x + s.parent.x, s.y + s.parent.y, lineSplit[0] )
	
	else:
		Menu_DrawString( RCOLUMN_OFFSET + s.x + s.parent.x, s.y + s.parent.y, lineSplit[0] )
		Menu_DrawString( RCOLUMN_OFFSET + s.x + s.parent.x, s.y + s.parent.y + 10, lineSplit[1] )
	
