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
from linux import vid_so
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

	if a.generic.callback is not None:
		a.generic.callback( a )

def Action_Draw( a ): #menuaction_s *

	if a.generic.flags & menumod.QMF_LEFT_JUSTIFY:
	
		if a.generic.flags & menumod.QMF_GRAYED:
			Menu_DrawStringDark( a.generic.x + a.generic.parent.x + LCOLUMN_OFFSET, a.generic.y + a.generic.parent.y, a.generic.name )
		else:
			Menu_DrawString( a.generic.x + a.generic.parent.x + LCOLUMN_OFFSET, a.generic.y + a.generic.parent.y, a.generic.name )
	
	else:
	
		if a.generic.flags & menumod.QMF_GRAYED:
			Menu_DrawStringR2LDark( a.generic.x + a.generic.parent.x + LCOLUMN_OFFSET, a.generic.y + a.generic.parent.y, a.generic.name )
		else:
			Menu_DrawStringR2L( a.generic.x + a.generic.parent.x + LCOLUMN_OFFSET, a.generic.y + a.generic.parent.y, a.generic.name )
	
	if a.generic.ownerdraw is not None:
		a.generic.ownerdraw( a )

"""
qboolean Field_DoEnter( menufield_s *f )
{
	if ( f.generic.callback )
	{
		f.generic.callback( f );
		return true;
	}
	return false;
}

void Field_Draw( menufield_s *f )
{
	int i;
	char tempbuffer[128]="";

	if ( f.generic.name )
		Menu_DrawStringR2LDark( f.generic.x + f.generic.parent.x + LCOLUMN_OFFSET, f.generic.y + f.generic.parent.y, f.generic.name );

	strncpy( tempbuffer, f->buffer + f->visible_offset, f->visible_length );

	Draw_Char( f.generic.x + f.generic.parent.x + 16, f.generic.y + f.generic.parent.y - 4, 18 );
	Draw_Char( f.generic.x + f.generic.parent.x + 16, f.generic.y + f.generic.parent.y + 4, 24 );

	Draw_Char( f.generic.x + f.generic.parent.x + 24 + f->visible_length * 8, f.generic.y + f.generic.parent.y - 4, 20 );
	Draw_Char( f.generic.x + f.generic.parent.x + 24 + f->visible_length * 8, f.generic.y + f.generic.parent.y + 4, 26 );

	for ( i = 0; i < f->visible_length; i++ )
	{
		Draw_Char( f.generic.x + f.generic.parent.x + 24 + i * 8, f.generic.y + f.generic.parent.y - 4, 19 );
		Draw_Char( f.generic.x + f.generic.parent.x + 24 + i * 8, f.generic.y + f.generic.parent.y + 4, 25 );
	}

	Menu_DrawString( f.generic.x + f.generic.parent.x + 24, f.generic.y + f.generic.parent.y, tempbuffer );

	if ( Menu_ItemAtCursor( f.generic.parent ) == f )
	{
		int offset;

		if ( f->visible_offset )
			offset = f->visible_length;
		else
			offset = f->cursor;

		if ( ( ( int ) ( Sys_Milliseconds() / 250 ) ) & 1 )
		{
			Draw_Char( f.generic.x + f.generic.parent.x + ( offset + 2 ) * 8 + 8,
					   f.generic.y + f.generic.parent.y,
					   11 );
		}
		else
		{
			Draw_Char( f.generic.x + f.generic.parent.x + ( offset + 2 ) * 8 + 8,
					   f.generic.y + f.generic.parent.y,
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
		if ( !isdigit( key ) && ( f.generic.flags & QMF_NUMBERSONLY ) )
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
		item.generic.parent = menu
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
		
			if citem.generic.type != menumod.MTYPE_SEPARATOR:
				return
		
	

	#
	# it's not in a valid spot, so crawl in the direction indicated until we
	# find a valid spot
	#
	if direc == 1:
	
		while 1:
		
			citem = Menu_ItemAtCursor( m )
			if citem is not None:
				if citem.generic.type != menumod.MTYPE_SEPARATOR:
					break
			m.cursor += direc
			if m.cursor >= len(m.items):
				m.cursor = 0
		
	
	else:
	
		while 1:
		
			citem = Menu_ItemAtCursor( m )
			if citem is not None:
				if citem.generic.type != menumod.MTYPE_SEPARATOR:
					break
			m.cursor += direc
			if m.cursor < 0:
				m.cursor = len(m.items) - 1
		

def Menu_Center( menu ): #menuframework_s *

	height = menu.items[-1].generic.y
	height += 10

	menu.y = ( VID_HEIGHT() - height ) // 2

def Menu_Draw( menu ): #menuframework_s *
	
	#int i;
	#menucommon_s *item;

	#
	# draw contents
	#
	for item in menu.items:
	
		if item.generic.type == menumod.MTYPE_FIELD:
			Field_Draw( item )

		elif item.generic.type == menumod.MTYPE_SLIDER:
			Slider_Draw( item )

		elif item.generic.type == menumod.MTYPE_LIST:
			MenuList_Draw( item )

		elif item.generic.type == menumod.MTYPE_SPINCONTROL:
			SpinControl_Draw( item )

		elif item.generic.type == menumod.MTYPE_ACTION:
			Action_Draw( item )

		elif item.generic.type == menumod.menumod.MTYPE_SEPARATOR:
			Separator_Draw( item )

	
	"""
	item = Menu_ItemAtCursor( menu );

	if ( item && item->cursordraw )
	{
		item->cursordraw( item );
	}
	else if ( menu->cursordraw )
	{
		menu->cursordraw( menu );
	}
	else if ( item && item->type != menumod.MTYPE_FIELD )
	{
		if ( item->flags & menumod.QMF_LEFT_JUSTIFY )
		{
			Draw_Char( menu.x + item.x - 24 + item->cursor_offset, menu.y + item.y, 12 + ( ( int ) ( Sys_Milliseconds()/250 ) & 1 ) );
		}
		else
		{
			Draw_Char( menu.x + item->cursor_offset, menu.y + item.y, 12 + ( ( int ) ( Sys_Milliseconds()/250 ) & 1 ) );
		}
	}

	if ( item )
	{
		if ( item->statusbarfunc )
			item->statusbarfunc( ( void * ) item );
		else if ( item->statusbar )
			Menu_DrawStatusBar( item->statusbar );
		else
			Menu_DrawStatusBar( menu->statusbar );

	}
	else
	{
		Menu_DrawStatusBar( menu->statusbar );
	}


void Menu_DrawStatusBar( const char *string )
{
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

	#unsigned i;

	for i, ch in enumerate(string):

		Draw_Char( ( x + i*8 ), y, ord(ch) )
	
"""
void Menu_DrawStringDark( int x, int y, const char *string )
{
	unsigned i;

	for ( i = 0; i < strlen( string ); i++ )
	{
		Draw_Char( ( x + i*8 ), y, string[i] + 128 );
	}
}

void Menu_DrawStringR2L( int x, int y, const char *string )
{
	unsigned i;

	for ( i = 0; i < strlen( string ); i++ )
	{
		Draw_Char( ( x - i*8 ), y, string[strlen(string)-i-1] );
	}
}

void Menu_DrawStringR2LDark( int x, int y, const char *string )
{
	unsigned i;

	for ( i = 0; i < strlen( string ); i++ )
	{
		Draw_Char( ( x - i*8 ), y, string[strlen(string)-i-1]+128 );
	}
}
"""
def Menu_ItemAtCursor( m ): #menuframework_s * (returns void *)

	if m.cursor < 0 or m.cursor >= len(m.items):
		return None

	return m.items[m.cursor]


def Menu_SelectItem( s ): #menuframework_s * (returns qboolean)

	item = Menu_ItemAtCursor( s )

	if item is not None:
		
		if item.generic.type == menumod.MTYPE_FIELD:
			return Field_DoEnter( item )
		elif item.generic.type == menumod.MTYPE_ACTION:
			Action_DoEnter( item )
			return True
		elif item.generic.type == menumod.MTYPE_LIST:
			## Menulist_DoEnter( item )
			return False
		elif item.generic.type == menumod.MTYPE_SPINCONTROL:
			## SpinControl_DoEnter( item )
			return False
		
	return False
"""

void Menu_SetStatusBar( menuframework_s *m, const char *string )
{
	m->statusbar = string;
}

void Menu_SlideItem( menuframework_s *s, int dir )
{
	menucommon_s *item = ( menucommon_s * ) Menu_ItemAtCursor( s );

	if ( item )
	{
		switch ( item->type )
		{
		case MTYPE_SLIDER:
			Slider_DoSlide( ( menuslider_s * ) item, dir );
			break;
		case MTYPE_SPINCONTROL:
			SpinControl_DoSlide( ( menulist_s * ) item, dir );
			break;
		}
	}
}
"""
def Menu_TallySlots( menu ): #menuframework_s * (returns int)

	total = 0 #int

	for item in menu.items:
	
		if item.generic.type == menumod.MTYPE_LIST:
			total += len(item.itemnames)		
		else:
			total += 1
		
	return total

"""
void Menulist_DoEnter( menulist_s *l )
{
	int start;

	start = l.generic.y / 10 + 1;

	l->curvalue = l.generic.parent->cursor - start;

	if ( l.generic.callback )
		l.generic.callback( l );
}

void MenuList_Draw( menulist_s *l )
{
	const char **n;
	int y = 0;

	Menu_DrawStringR2LDark( l.generic.x + l.generic.parent.x + LCOLUMN_OFFSET, l.generic.y + l.generic.parent.y, l.generic.name );

	n = l->itemnames;

  	Draw_Fill( l.generic.x - 112 + l.generic.parent.x, l.generic.parent.y + l.generic.y + l->curvalue*10 + 10, 128, 10, 16 );
	while ( *n )
	{
		Menu_DrawStringR2LDark( l.generic.x + l.generic.parent.x + LCOLUMN_OFFSET, l.generic.y + l.generic.parent.y + y + 10, *n );

		n++;
		y += 10;
	}
}

void Separator_Draw( menuseparator_s *s )
{
	if ( s.generic.name )
		Menu_DrawStringR2LDark( s.generic.x + s.generic.parent.x, s.generic.y + s.generic.parent.y, s.generic.name );
}

void Slider_DoSlide( menuslider_s *s, int dir )
{
	s->curvalue += dir;

	if ( s->curvalue > s->maxvalue )
		s->curvalue = s->maxvalue;
	else if ( s->curvalue < s->minvalue )
		s->curvalue = s->minvalue;

	if ( s.generic.callback )
		s.generic.callback( s );
}

#define SLIDER_RANGE 10

void Slider_Draw( menuslider_s *s )
{
	int	i;

	Menu_DrawStringR2LDark( s.generic.x + s.generic.parent.x + LCOLUMN_OFFSET,
		                s.generic.y + s.generic.parent.y, 
						s.generic.name );

	s->range = ( s->curvalue - s->minvalue ) / ( float ) ( s->maxvalue - s->minvalue );

	if ( s->range < 0)
		s->range = 0;
	if ( s->range > 1)
		s->range = 1;
	Draw_Char( s.generic.x + s.generic.parent.x + RCOLUMN_OFFSET, s.generic.y + s.generic.parent.y, 128);
	for ( i = 0; i < SLIDER_RANGE; i++ )
		Draw_Char( RCOLUMN_OFFSET + s.generic.x + i*8 + s.generic.parent.x + 8, s.generic.y + s.generic.parent.y, 129);
	Draw_Char( RCOLUMN_OFFSET + s.generic.x + i*8 + s.generic.parent.x + 8, s.generic.y + s.generic.parent.y, 130);
	Draw_Char( ( int ) ( 8 + RCOLUMN_OFFSET + s.generic.parent.x + s.generic.x + (SLIDER_RANGE-1)*8 * s->range ), s.generic.y + s.generic.parent.y, 131);
}

void SpinControl_DoEnter( menulist_s *s )
{
	s->curvalue++;
	if ( s->itemnames[s->curvalue] == 0 )
		s->curvalue = 0;

	if ( s.generic.callback )
		s.generic.callback( s );
}

void SpinControl_DoSlide( menulist_s *s, int dir )
{
	s->curvalue += dir;

	if ( s->curvalue < 0 )
		s->curvalue = 0;
	else if ( s->itemnames[s->curvalue] == 0 )
		s->curvalue--;

	if ( s.generic.callback )
		s.generic.callback( s );
}

void SpinControl_Draw( menulist_s *s )
{
	char buffer[100];

	if ( s.generic.name )
	{
		Menu_DrawStringR2LDark( s.generic.x + s.generic.parent.x + LCOLUMN_OFFSET, 
							s.generic.y + s.generic.parent.y, 
							s.generic.name );
	}
	if ( !strchr( s->itemnames[s->curvalue], '\n' ) )
	{
		Menu_DrawString( RCOLUMN_OFFSET + s.generic.x + s.generic.parent.x, s.generic.y + s.generic.parent.y, s->itemnames[s->curvalue] );
	}
	else
	{
		strcpy( buffer, s->itemnames[s->curvalue] );
		*strchr( buffer, '\n' ) = 0;
		Menu_DrawString( RCOLUMN_OFFSET + s.generic.x + s.generic.parent.x, s.generic.y + s.generic.parent.y, buffer );
		strcpy( buffer, strchr( s->itemnames[s->curvalue], '\n' ) + 1 );
		Menu_DrawString( RCOLUMN_OFFSET + s.generic.x + s.generic.parent.x, s.generic.y + s.generic.parent.y + 10, buffer );
	}
}
"""
