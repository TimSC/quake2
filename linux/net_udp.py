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
import time
from qcommon import qcommon, common
"""
// net_wins.c

#include "../qcommon/qcommon.h"

#include <unistd.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/param.h>
#include <sys/ioctl.h>
#include <sys/uio.h>
#include <errno.h>

#ifdef NeXT
#include <libc.h>
#endif
"""
net_local_adr = qcommon.netadr_t()
"""
#define	LOOPBACK	0x7f000001
"""
MAX_LOOPBACK	= 4
"""
typedef struct
{
	byte	data[MAX_MSGLEN];
	int		datalen;
} loopmsg_t;
"""
class loopback_t(object):

	def __init__(self):

		self.msgs = [] # loopmsg_t[MAX_LOOPBACK];
		self.get, self.send = 0, 0 #int

loopbacks = [loopback_t(), loopback_t()]
"""
int			ip_sockets[2];
int			ipx_sockets[2];

int NET_Socket (char *net_interface, int port);
char *NET_ErrorString (void);

//=============================================================================

void NetadrToSockadr (netadr_t *a, struct sockaddr_in *s)
{
	memset (s, 0, sizeof(*s));

	if (a->type == NA_BROADCAST)
	{
		s->sin_family = AF_INET;

		s->sin_port = a->port;
		*(int *)&s->sin_addr = -1;
	}
	else if (a->type == NA_IP)
	{
		s->sin_family = AF_INET;

		*(int *)&s->sin_addr = *(int *)&a->ip;
		s->sin_port = a->port;
	}
}

void SockadrToNetadr (struct sockaddr_in *s, netadr_t *a)
{
	*(int *)&a->ip = *(int *)&s->sin_addr;
	a->port = s->sin_port;
	a->type = NA_IP;
}

"""
def NET_CompareAdr (a, b): #netadr_t, netadr_t (returns qboolean)

	if a.ip == b.ip and a.port == b.port:
		return True
	return False

"""
===================
NET_CompareBaseAdr

Compares without the port
===================
"""
def NET_CompareBaseAdr (a, b): # netadr_t, netadr_t (returns qboolean)

	if a.type != b.type:
		return False

	if a.type == qcommon.netadrtype_t.NA_LOOPBACK:
		return True

	if a.type == qcommon.netadrtype_t.NA_IP:
	
		if a.ip[0] == b.ip[0] and a.ip[1] == b.ip[1] and a.ip[2] == b.ip[2] and a.ip[3] == b.ip[3]:
			return True
		return False
	
	if a.type == qcommon.netadrtype_t.NA_IPX:
	
		if a.ipx == b.ipx:
			return True
		return False
	

def NET_AdrToString (a): #netadr_t (returns char	*)

	if a.ip is None or len(a.ip) < 4:
		return "0.0.0.0:{}".format(a.port)

	return "{:d}.{:d}.{:d}.{:d}:{}".format(a.ip[0], a.ip[1], a.ip[2], a.ip[3], a.port)


"""
char	*NET_BaseAdrToString (netadr_t a)
{
	static	char	s[64];
	
	Com_sprintf (s, sizeof(s), "%i.%i.%i.%i", a.ip[0], a.ip[1], a.ip[2], a.ip[3]);

	return s;
}

/*
=============
NET_StringToAdr

localhost
idnewt
idnewt:28000
192.246.40.70
192.246.40.70:28000
=============
*/
qboolean	NET_StringToSockaddr (char *s, struct sockaddr *sadr)
{
	struct hostent	*h;
	char	*colon;
	char	copy[128];
	
	memset (sadr, 0, sizeof(*sadr));
	((struct sockaddr_in *)sadr)->sin_family = AF_INET;
	
	((struct sockaddr_in *)sadr)->sin_port = 0;

	strcpy (copy, s);
	// strip off a trailing :port if present
	for (colon = copy ; *colon ; colon++)
		if (*colon == ':')
		{
			*colon = 0;
			((struct sockaddr_in *)sadr)->sin_port = htons((short)atoi(colon+1));	
		}
	
	if (copy[0] >= '0' && copy[0] <= '9')
	{
		*(int *)&((struct sockaddr_in *)sadr)->sin_addr = inet_addr(copy);
	}
	else
	{
		if (! (h = gethostbyname(copy)) )
			return 0;
		*(int *)&((struct sockaddr_in *)sadr)->sin_addr = *(int *)h->h_addr_list[0];
	}
	
	return true;
}

/*
=============
NET_StringToAdr

localhost
idnewt
idnewt:28000
192.246.40.70
192.246.40.70:28000
=============
"""
def NET_StringToAdr (s): #char * (returns netadr_t *)

	#struct sockaddr_in sadr;
	
	if s == "localhost":
	
		a = qcommon.netadr_t()
		a.type = qcommon.netadrtype_t.NA_LOOPBACK
		return a
	
	return None

	#if (!NET_StringToSockaddr (s, (struct sockaddr *)&sadr))
	#	return False;
	
	#SockadrToNetadr (&sadr, a)

	#return a



def NET_IsLocalAddress (adr): #netadr_t (returns qboolean)

	return NET_CompareAdr (adr, net_local_adr)

"""
/*
=============================================================================

LOOPBACK BUFFERS FOR LOCAL PLAYER

=============================================================================
"""

def NET_GetLoopPacket (sock): #netsrc_t (returns qboolean, netadr_t *, sizebuf_t *)

	loop = loopbacks[sock.value]

	if len(loop.msgs) == 0:
		return False, None, None

	net_message = qcommon.sizebuf_t()
	common.SZ_Init (net_message, qcommon.MAX_MSGLEN)
	net_message.data = loop.msgs.pop(0)
	net_message.cursize = len(net_message.data)

	return True, net_local_adr, net_message


def NET_SendLoopPacket (sock, data: bytes, to): #netsrc_t, void *, netadr_t

	assert isinstance(data, bytes) or isinstance(data, bytearray)
	loop = loopbacks[sock.value^1]

	if len(loop.msgs) >= MAX_LOOPBACK:
		loop.msgs.pop(0)

	loop.msgs.append(data)

"""
//=============================================================================
"""
def NET_GetPacket (sock): #netsrc_t (returns qboolean, netadr_t *, sizebuf_t *)

	#int 	ret;
	#struct sockaddr_in	from;
	#int		fromlen;
	#int		net_socket;
	#int		protocol;
	#int		err;

	rx, net_from, net_message = NET_GetLoopPacket (sock)
	assert net_message is None or isinstance(net_message, qcommon.sizebuf_t)
	if rx:
		return True, net_from, net_message
	"""
	for (protocol = 0 ; protocol < 2 ; protocol++)
	{
		if (protocol == 0)
			net_socket = ip_sockets[sock];
		else
			net_socket = ipx_sockets[sock];

		if (!net_socket)
			continue;

		fromlen = sizeof(from);
		ret = recvfrom (net_socket, net_message->data, net_message->maxsize
			, 0, (struct sockaddr *)&from, &fromlen);

		SockadrToNetadr (&from, net_from);

		if (ret == -1)
		{
			err = errno;

			if (err == EWOULDBLOCK || err == ECONNREFUSED)
				continue;
			Com_Printf ("NET_GetPacket: %s from %s\n", NET_ErrorString(),
						NET_AdrToString(*net_from));
			continue;
		}

		if (ret == net_message->maxsize)
		{
			Com_Printf ("Oversize packet from %s\n", NET_AdrToString (*net_from));
			continue;
		}

		net_message->cursize = ret;
		return True, net_from, net_message
	}
"""
	return False, None, None

"""
//=============================================================================
"""
def NET_SendPacket (sock, data, to): #netsrc_t, void *, netadr_t

	#int		ret;
	#struct sockaddr_in	addr;
	#int		net_socket;

	if to.type == qcommon.netadrtype_t.NA_LOOPBACK:
	
		NET_SendLoopPacket (sock, data, to)
		return

	raise NotImplementedError()

	"""
	if (to.type == NA_BROADCAST)
	{
		net_socket = ip_sockets[sock];
		if (!net_socket)
			return;
	}
	else if (to.type == NA_IP)
	{
		net_socket = ip_sockets[sock];
		if (!net_socket)
			return;
	}
	else if (to.type == NA_IPX)
	{
		net_socket = ipx_sockets[sock];
		if (!net_socket)
			return;
	}
	else if (to.type == NA_BROADCAST_IPX)
	{
		net_socket = ipx_sockets[sock];
		if (!net_socket)
			return;
	}
	else
		Com_Error (ERR_FATAL, "NET_SendPacket: bad address type");

	NetadrToSockadr (&to, &addr);

	ret = sendto (net_socket, data, length, 0, (struct sockaddr *)&addr, sizeof(addr) );
	if (ret == -1)
	{
		Com_Printf ("NET_SendPacket ERROR: %s to %s\n", NET_ErrorString(),
				NET_AdrToString (to));
	}
}


//=============================================================================




/*
====================
NET_OpenIP
====================
*/
void NET_OpenIP (void)
{
	cvar_t	*port, *ip;

	port = Cvar_Get ("port", va("%i", PORT_SERVER), CVAR_NOSET);
	ip = Cvar_Get ("ip", "localhost", CVAR_NOSET);

	if (!ip_sockets[NS_SERVER])
		ip_sockets[NS_SERVER] = NET_Socket (ip->string, port->value);
	if (!ip_sockets[NS_CLIENT])
		ip_sockets[NS_CLIENT] = NET_Socket (ip->string, PORT_ANY);
}

/*
====================
NET_OpenIPX
====================
*/
void NET_OpenIPX (void)
{
}


/*
====================
NET_Config

A single player game will only use the loopback code
====================
"""
def NET_Config (multiplayer): #qboolean

	if not multiplayer:
		# shut down any existing sockets
		pass
		"""
		for (i=0 ; i<2 ; i++)
		{
			if (ip_sockets[i])
			{
				close (ip_sockets[i]);
				ip_sockets[i] = 0;
			}
			if (ipx_sockets[i])
			{
				close (ipx_sockets[i]);
				ipx_sockets[i] = 0;
			}
		}
		"""
	
	else:
		
		# open sockets
		pass
		"""
		NET_OpenIP ();
		NET_OpenIPX ();
		"""

"""
//===================================================================


/*
====================
NET_Init
====================
"""
def NET_Init ():

	pass


"""
====================
NET_Socket
====================
*/
int NET_Socket (char *net_interface, int port)
{
	int newsocket;
	struct sockaddr_in address;
	qboolean _true = true;
	int	i = 1;

	if ((newsocket = socket (PF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
	{
		Com_Printf ("ERROR: UDP_OpenSocket: socket: %s", NET_ErrorString());
		return 0;
	}

	// make it non-blocking
	if (ioctl (newsocket, FIONBIO, &_true) == -1)
	{
		Com_Printf ("ERROR: UDP_OpenSocket: ioctl FIONBIO:%s\n", NET_ErrorString());
		return 0;
	}

	// make it broadcast capable
	if (setsockopt(newsocket, SOL_SOCKET, SO_BROADCAST, (char *)&i, sizeof(i)) == -1)
	{
		Com_Printf ("ERROR: UDP_OpenSocket: setsockopt SO_BROADCAST:%s\n", NET_ErrorString());
		return 0;
	}

	if (!net_interface || !net_interface[0] || !stricmp(net_interface, "localhost"))
		address.sin_addr.s_addr = INADDR_ANY;
	else
		NET_StringToSockaddr (net_interface, (struct sockaddr *)&address);

	if (port == PORT_ANY)
		address.sin_port = 0;
	else
		address.sin_port = htons((short)port);

	address.sin_family = AF_INET;

	if( bind (newsocket, (void *)&address, sizeof(address)) == -1)
	{
		Com_Printf ("ERROR: UDP_OpenSocket: bind: %s\n", NET_ErrorString());
		close (newsocket);
		return 0;
	}

	return newsocket;
}


/*
====================
NET_Shutdown
====================
*/
void	NET_Shutdown (void)
{
	NET_Config (false);	// close sockets
}


/*
====================
NET_ErrorString
====================
*/
char *NET_ErrorString (void)
{
	int		code;

	code = errno;
	return strerror (code);
}

// sleeps msec or until net socket is ready
"""
def NET_Sleep(msec: int):

	time.sleep(0)
	"""
    struct timeval timeout;
	fd_set	fdset;
	extern cvar_t *dedicated;
	extern qboolean stdin_active;

	if (!ip_sockets[NS_SERVER] || (dedicated && !dedicated->value))
		return; // we're not a server, just run full speed

	FD_ZERO(&fdset);
	if (stdin_active)
		FD_SET(0, &fdset); // stdin is processed too
	FD_SET(ip_sockets[NS_SERVER], &fdset); // network socket
	timeout.tv_sec = msec/1000;
	timeout.tv_usec = (msec%1000)*1000;
	select(ip_sockets[NS_SERVER]+1, &fdset, NULL, NULL, &timeout);
}
"""
