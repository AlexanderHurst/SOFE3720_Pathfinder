import math

# bounds of the window, in lat/long
LEFTLON = -78.9162
RIGHTLON = -78.8250
TOPLAT = 43.9711
BOTLAT = 43.8853
WIDTH = RIGHTLON-LEFTLON
HEIGHT = TOPLAT-BOTLAT
# ratio of one degree of longitude to one degree of latitude
LONRATIO = math.cos(TOPLAT*3.1415/180)
WINWID = 800
WINHGT = (int)((WINWID/LONRATIO)*HEIGHT/WIDTH)
TOXPIX = WINWID/WIDTH
TOYPIX = WINHGT/HEIGHT
# width,height of elevation array
EPIX = 3601
# approximate number of meters per degree of latitude
MPERLAT = 111000
MPERLON = MPERLAT*LONRATIO
