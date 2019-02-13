import math

# bounds of the window, in lat/long
LEFTLON = -78.9250
RIGHTLON = -78.7900
TOPLAT = 43.9500
BOTLAT = 43.8450
WIDTH = RIGHTLON-LEFTLON
HEIGHT = TOPLAT-BOTLAT
HGT_BOT = math.floor(BOTLAT)
HGT_LEFT = math.floor(LEFTLON)
# ratio of one degree of longitude to one degree of latitude
LONRATIO = math.cos(TOPLAT*3.1415/180)
WINWID = 800
WINHGT = (int)((WINWID/LONRATIO)*HEIGHT/WIDTH)
TOXPIX = WINWID/WIDTH
TOYPIX = WINHGT/HEIGHT
# approximate number of meters per degree of latitude
MPERLAT = 111000
MPERLON = MPERLAT*LONRATIO
