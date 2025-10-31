# Pygame UDP Multiplayer Framework

This is a simplified example of a multiplayer networking system using:
- `pygame`    (for graphics)
- `socket`    (for connections)
- `threading` (for handling socket operations without blocking main loop)
- `json`      (for serializing data to be suitable for cross-socket transport)

I used User Datagram Protocol (UDP) for socket type, but you may notice that the server
behaves similar to a TCP server. Instead of listening for connections via `sock.accept()`,
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

Store any data you want to send to the server in `queued_data`. `queued_data` gets reset to `None`
after send. The nice thing about this system is that you can send ANY kind of `dict` data without
the server getting errors.

For example: Every so often, the client will send a 'ping' to the server to keep the connection alive.
The 'ping' looks like this: `{"ping":True}`. The server acknowledges this information, but it doesn't
affect player data (or any other data being sent across). Another example: A client that quits will send
`{"quit":True}` to notify the server that the connection is over, and the server behaves correspondingly.

There are other little details that are worth inspecting, like how other players get displayed to the screen
or how player data is formatted.

Player data from server: `{int:{'ID':int,'name':str,'rect':[int,int,int,int],'color':int,'flip':bool}}`

Player data from client: `{'ID':int,'name':str,'rect':[int,int,int,int],'color':int,'flip':bool}`


Have fun experimenting or adapting this code into your projects!

Credit is not necessary but is appreciated :)
