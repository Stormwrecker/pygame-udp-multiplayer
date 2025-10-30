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
import pygame
import socket
import threading
import json

# not-so-necessary modules
import time
import random

# init pygame
pygame.init()

# generated a randomized 5-letter name for our client
letters = "abcdefghijklmnopqrstuvwxyz"
name = ""
for i in range(5):
    name += letters[random.randint(0, len(letters) - 1)]

# screen setup
screen_width = 500
screen_height = 500
screen = pygame.display.set_mode((screen_width, screen_height))

# misc pygame setup
caption = f"Player: {name} | Multiplayer: Disabled"
pygame.display.set_caption(caption)
display = pygame.Surface((250, 250))  # this is the Surface to blit to, not screen
clock = pygame.time.Clock()

# constants
FPS = 60
PING_INTERVAL = 180
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
ORANGE = (233, 128, 60)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARK_BLUE = (28, 89, 152)

# other players
all_players = {}

# player-related values
my_pos = [10, 10]
speed = 3
images = [pygame.image.load("images/slimeBlue.png").convert(),
          pygame.image.load("images/slimePink.png").convert(),
          pygame.image.load("images/slimeGreen.png").convert()]
for i, v in enumerate(images):
    v.set_colorkey(BLACK)
    v = pygame.transform.scale_by(v, .5)
    images[i] = v
image_color = random.randint(0, 2)
image = images[image_color]
flip = False
player = pygame.Rect(*my_pos, 10, 10)

# multiplayer-related values
enable_multiplayer = False           # do NOT edit this value (cannot be reset either)
ADDR_PAIR = ("localhost", 8888)      # this is the address of the main server socket
PRE_ADDR_PAIR = ("localhost", 8889)  # this is the address of the listener server socket
queued_data = []                     # setting this to a non-null value will be sent to server immediately and reset to None
ping_timer = 0                       # increments to PING_INTERVAL (edit PING_INTERVAL not ping_timer)
temp_players = {}                    # server's version of all the connected players
my_ID = None                         # player ID assigned by server
update_player = False                # setting this to True will update the server immediately


# main networking function
def network(sock):
    global run, temp_players, queued_data

    # main loop
    while run:

        # handle data
        data = None
        try:
            # receive and 'translate' data from server
            data, _ = sock.recvfrom(2048)
            data = json.loads(data.decode())
        except:
            # couldn't receive data; do nothing
            pass

        # plug data into temp_players (to be handled outside thread)
        if type(data) == dict:
            temp_players = data

        # cap networking at 2x the current framerate
        time.sleep(1/(FPS*2))

        # send data from our data queue
        if len(queued_data):
            sock.sendto(json.dumps(queued_data[0]).encode(), ADDR_PAIR)
            queued_data.pop(0)

    # send quit signal and close socket
    print("closed")
    my_sock.sendto(json.dumps({"quit": True}).encode(), ADDR_PAIR)
    sock.close()


# main loop
run = True
while run:
    # fill display to keep from smearing
    display.fill(DARK_BLUE)

    # handle basic player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        my_pos[0] -= speed
        flip = False
        update_player = True
    if keys[pygame.K_RIGHT]:
        my_pos[0] += speed
        flip = True
        update_player = True
    if keys[pygame.K_UP]:
        my_pos[1] -= speed
        update_player = True
    if keys[pygame.K_DOWN]:
        my_pos[1] += speed
        update_player = True
    player.topleft = my_pos

    # update server with player data
    if update_player:
        ping_timer = 0
        queued_data.append({"ID":my_ID, "name":name, "rect":[player.x, player.y, player.width, player.height], "color":image_color, "flip":flip})
        update_player = False

    # set up other players' values
    for k, v in temp_players.items():
        if v['name'] != name:
            all_players[k] = v

    # draw other players if applicable
    for k, player_info in all_players.items():
        if type(player_info) == dict and k in temp_players.keys():
            if player_info['name'] != name:
                display.blit(pygame.transform.flip(images[player_info['color']], player_info["flip"], False), player_info['rect'])

    # draw our current player
    display.blit(pygame.transform.flip(image, flip, False), player)

    # ping server every PING_INTERVAL frames
    if ping_timer < PING_INTERVAL:
        ping_timer += 1
    else:
        if len(queued_data) == 0:
            queued_data.append({"ping":True})
        ping_timer = 0

    # update display
    screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
    pygame.display.flip()

    # event handling
    all_events = pygame.event.get()
    for event in all_events:
        # quit
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]):
            run = False
            break

        # key events
        if event.type == pygame.KEYDOWN:
            # enable multiplayer (cannot be disabled)
            if event.key == pygame.K_SPACE:
                if not enable_multiplayer:
                    try:
                        # create main socket
                        my_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
                        # instant timeout
                        my_sock.settimeout(0)
                        # send initial data to trigger server
                        init_player_data = {"ID":my_ID, "name":name, "rect":[player.x, player.y, player.width, player.height], "color":image_color, "flip":flip}
                        my_sock.sendto(json.dumps(init_player_data).encode(), PRE_ADDR_PAIR)
                        # receive the unique ID
                        my_sock.setblocking(True)
                        data, _ = my_sock.recvfrom(2048)
                        my_ID = json.loads(data.decode())["assigned_ID"]
                        my_sock.setblocking(False)
                        # start network thread
                        net_thread = threading.Thread(target=network, args=[my_sock,], daemon=False)
                        net_thread.start()
                        # set caption title
                        caption = f"Player: {name} | Multiplayer: Enabled"
                        enable_multiplayer = True
                    except Exception as e:
                        # catch error
                        print(type(e), e)
                        # set caption title
                        caption = f"Player: {name} | Multiplayer: Doesn't Work"
                    # set caption
                    pygame.display.set_caption(caption)
            # change player's color
            if event.key == pygame.K_RETURN:
                image_color += 1
                image_color %= len(images)
                image = images[image_color]
                update_player = True

    # tick clock
    clock.tick(FPS)

# quit pygame
pygame.quit()
