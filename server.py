"""
This is a simplified example of a multiplayer networking system using:
- ``pygame``    (for graphics)
- ``socket``    (for connections)
- ``threading`` (for handling socket operations without blocking main loop)
- ``json``      (for serializing data to be suitable for cross-socket transport)

I used User Datagram Protocol (UDP) for socket type, but you may notice that the server
behaves similar to a TCP server. Instead of listening for connections via ``sock.accept()``,
a separate 'intro' socket listens for any incoming data and immediately stores new clients as
they connect. From there on, handling the clients goes about the same with the exception
of not having to packet data for transfer. UDP covers this aspect as far as I know.

Here is what the client does:
- Pygame window is opened/configured
- Basic player is drawn using an image and a rect
- Hitting Spacebar enables multiplayer system (rather than enabling it on startup)

What enabling multiplayer does:
- Creates a UDP socket
- Sends initial data to server to trigger client-handling
- Receives a unique ID to assign to current player
- Starts network thread that handles connection with server

Store any data you want to send to the server in ``queued_data``. ``queued_data`` gets reset to ``None``
after send. The nice thing about this system is that you can send ANY kind of ``dict`` data without
the server getting errors.

For example: Every so often, the client will send a 'ping' to the server to keep the connection alive.
The 'ping' looks like this: ``{"ping":True}``. The server acknowledges this information, but it doesn't
affect player data (or any other data being sent across). Another example: A client that quits will send
``{"quit":True}`` to notify the server that the connection is over, and the server behaves correspondingly.

There are other little details that are worth inspecting, like how other players get displayed to the screen
or how player data is formatted.

Player data from server: ``{int:{'ID':int,'name':str,'rect':[int,int,int,int],'color':int,'flip':bool}}``

Player data from client: ``{'ID':int,'name':str,'rect':[int,int,int,int],'color':int,'flip':bool}``


Have fun experimenting or adapting this code into your projects!

Code by Stormwrecker.
Credit is not necessary but is appreciated :)
"""


# necessary modules
import socket
import threading
import json

# main socket for handling clients
my_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_sock.bind(("localhost", 8888))
my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

# main socket will timeout after 10 seconds
my_sock.settimeout(10)

# initial listener socket for 'accepting' clients (no timeout)
intro_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
intro_sock.bind(("localhost", 8889))
intro_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

# client-related values
clients = {}            # (IP, PORT): initial player value
players = {}            # player ID: current player value
client_count = 0        # count of unique active clients
MAX_CLIENTS = 3         # listener socket will handle up to this many clients


# main networking thread per client
def handle_client(addr, ID):
    global players, client_count

    # set up initial values
    current_ID = ID
    players[current_ID] = clients[addr]
    data = None

    # main loop
    while True:

        # send all active players (close connection if unable to)
        try:
            my_sock.sendto(json.dumps(players, sort_keys=True).encode(), addr)
        except:
            break

        # receive and 'translate' data from client
        data = None
        try:
            data, _ = my_sock.recvfrom(2048)
            data = json.loads(data.decode())
        except:
            # couldn't receive data; do nothing
            pass

        # interpret data from client
        if type(data) == dict:

            # player data
            if "name" in data:
                players[data["ID"]] = data

            # quit signal
            if "quit" in data:
                break

    # disconnect player
    print("Disconnected", players.get(current_ID)['name'])
    client_count -= 1
    clients.pop(addr)
    players.pop(current_ID)


# run listener socket and receive new clients
print("Waiting for clients...")
while client_count != MAX_CLIENTS:

    # receive data from any incoming connections
    try:
        data, addr = intro_sock.recvfrom(2048)
        print("Got a new client!", client_count + 1, "clients so far...")
    except:
        break

    # handle new unique clients
    if addr not in clients:
        # add initial data to 'clients' dict
        clients[addr] = json.loads(data.decode())
        # send a unique ID to client
        intro_sock.sendto(json.dumps({"assigned_ID": client_count}).encode(), addr)
        # start client-network thread
        threading.Thread(target=handle_client, args=[addr, client_count]).start()
        # increment client count
        client_count += 1


# shut down listener socket
print("\nDone accepting clients")
intro_sock.close()

# waste time in order to keep main socket alive
while client_count != 0:
    pass

# shut down main socket
print("\nShutdown")
my_sock.close()
