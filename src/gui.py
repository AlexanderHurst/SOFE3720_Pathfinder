import constants
import tkinter as tk
from graph import Planner
import time


class PlanWin(tk.Frame):
    '''
    All the GUI pieces to draw the streets, allow places to be selected,
    and then draw the resulting path.
    '''

    __slots__ = ('node_at_xy', 'nodes', 'ways', 'elevs', 'nodelab', 'elab',
                 'planner', 'lastnode', 'startnode', 'goalnode')

    def lat_lon_to_pix(self, latlon):
        # convert lat lon location to pixel coordinates
        # lon - furthest left location (most negative) * conversion
        x = (latlon[1]-constants.LEFTLON)*(constants.TOXPIX)
        # top (highest) - lat * conversion
        y = (constants.TOPLAT-latlon[0])*(constants.TOYPIX)
        return x, y

    def pix_to_elev(self, x, y):
        # debug statements
        # print(constants.TOPLAT, " - ", y, " / ", constants.TOYPIX,
        #       " = ", constants.TOPLAT-(y/constants.TOYPIX))
        # print(x, " / ", constants.TOXPIX, " + ", constants.LEFTLON,
        #       " = ", (x/constants.TOXPIX)+constants.LEFTLON)

        # top position (highest) - y converted to approx degrees
        # x converted to approx degrees + furthest left location (smallest)
        return self.lat_lon_to_elev(((constants.TOPLAT-(y/constants.TOYPIX)), ((x/constants.TOXPIX)+constants.LEFTLON)))

    def lat_lon_to_elev(self, latlon):
        # 0 for furthest south position in hgt data dim for furthest north
        # lat - bottom position gives relative position * dim to get array spot in hgt data
        row = (int)((latlon[0] - constants.HGT_BOT) * self.dim)
        # 0 for furthest west position in hgt data dim for furthest east
        # lat - far left position gives relative position * dim to get array spot in hgt data
        col = (int)(((latlon[1] - constants.HGT_LEFT)) * self.dim)
        return self.elevs[row, col]

    def maphover(self, mouse):
        # informs user of elevation
        self.elab.configure(text=str(self.pix_to_elev(mouse.x, mouse.y)))

        # scans area around mouse, starting at mouse for a point (who wants to be pixel perfect)
        for (dx, dy) in constants.ACCURACY_TOLERANCE:
            # check each position, stop if node found
            ckpos = (mouse.x+dx, mouse.y+dy)
            # if there is a node
            if ckpos in self.node_at_xy:
                # update the last node
                self.lastnode = self.node_at_xy[ckpos]
                # get the pixel location of the node
                last_node_pos = self.lat_lon_to_pix(
                    self.nodes[self.lastnode].pos)
                # update the last dot
                self.canvas.coords(
                    'lastdot', (last_node_pos[0]-2, last_node_pos[1]-2, last_node_pos[0]+2, last_node_pos[1]+2))
                # update the location string information with the node and way
                nstr = str(self.lastnode)
                nstr += " "
                nstr += str(self.nodes[self.node_at_xy[ckpos]].get_waystr())
                self.nodelab.configure(text=nstr)
                return

    def mapclick(self, mouse):
        ''' Canvas click handler:
        First click sets path start, second sets path goal
        '''
        # print where the user clicked,aand what the last node was
        print("Clicked on "+str(mouse.x)+"," +
              str(mouse.y)+" last node "+str(self.lastnode))

        # if there was no last node do nothing
        if self.lastnode is None:
            return
        # if there is no start node
        if self.startnode is None:
            # set the start node to the last node and colour the location
            self.startnode = self.nodes[self.lastnode]
            self.snpix = self.lat_lon_to_pix(self.startnode.pos)
            self.canvas.coords(
                'startdot', (self.snpix[0]-2, self.snpix[1]-2, self.snpix[0]+2, self.snpix[1]+2))
        # if there is a start node but no goal node
        elif self.goalnode is None:
            # set the goal node and colour the location
            self.goalnode = self.nodes[self.lastnode]
            self.snpix = self.lat_lon_to_pix(self.goalnode.pos)
            self.canvas.coords(
                'goaldot', (self.snpix[0]-2, self.snpix[1]-2, self.snpix[0]+2, self.snpix[1]+2))

    def clear(self):
        ''' Clear button callback. '''
        # wipe everything
        self.lastnode = None
        self.goalnode = None
        self.startnode = None
        self.canvas.coords('startdot', (0, 0, 0, 0))
        self.canvas.coords('goaldot', (0, 0, 0, 0))
        self.canvas.coords('path', (0, 0, 0, 0))

    def plan_path(self):
        ''' Path button callback, plans and then draws path.'''
        if self.startnode is None or self.goalnode is None:
            print("Sorry, not enough info.")
            return
        print("Planning! Starting Timer")
        start_time = time.time()
        nodes, ways = self.planner.plan(self.startnode, self.goalnode)
        print("Time taken to plan:", time.time() - start_time)
        print("From", self.startnode.id, "to", self.goalnode.id)
        lastway = ""
        # iterate through the ways printing each one
        for wayname in ways:
            # avoid printing the same way multiple times in a row
            if wayname != lastway:
                print(wayname)
                lastway = wayname
        coords = []
        # add each node to the list to be plotted on the gui
        for node in nodes:
            npos = self.lat_lon_to_pix(node.pos)
            coords.append(npos[0])
            coords.append(npos[1])
            # print node.id
        self.canvas.coords('path', coords)

    def __init__(self, master, nodes, ways, elevs, dim):
        # stores each location on the screen asociated with a node
        self.node_at_xy = {}
        # stores all of the nodes
        self.nodes = nodes
        # stores all of the ways
        self.ways = ways
        # stores the elevation array
        self.elevs = elevs
        # planner nodes
        self.startnode = None
        self.goalnode = None
        # planner object
        self.planner = Planner(nodes, ways)
        # the number of rows and columns in the elevation array
        self.dim = dim
        # the window
        thewin = tk.Frame(master)
        w = tk.Canvas(thewin, width=constants.WINWID, height=constants.WINHGT)

        # hover and clicking function bindings
        w.bind("<Button-1>", self.mapclick)
        w.bind("<Motion>", self.maphover)

        for waynum in self.ways:
            # for every way get the nodes
            nlist = self.ways[waynum].nodes
            # get the pixel location for the first node
            thispix = self.lat_lon_to_pix(self.nodes[nlist[0]].pos)

            # if the first node has more than 2 ways
            if len(self.nodes[nlist[0]].ways) > 2:
                # add it to the location to node mapping
                self.node_at_xy[((int)(thispix[0]),
                                 (int)(thispix[1]))] = nlist[0]
            # for each of the rest of the nodes
            for n in range(1, len(nlist)):
                # get the next pixel location
                nextpix = self.lat_lon_to_pix(self.nodes[nlist[n]].pos)
                # add it to the location to node mapping
                self.node_at_xy[((int)(nextpix[0]),
                                 (int)(nextpix[1]))] = nlist[n]
                # draw a line between the two nodes
                w.create_line(thispix[0], thispix[1], nextpix[0], nextpix[1])
                thispix = nextpix

        # path line
        w.create_line(0, 0, 0, 0, fill='orange', width=3, tag='path')
        # starting dot
        w.create_oval(0, 0, 0, 0, outline='green',
                      fill='green', tag='startdot')
        # goal dot
        w.create_oval(0, 0, 0, 0, outline='red', fill='red', tag='goaldot')
        # last dot
        w.create_oval(0, 0, 0, 0, outline='blue', fill='blue', tag='lastdot')
        w.pack(fill=tk.BOTH)

        # store the window canvas
        self.canvas = w

        # clean on button press
        cb = tk.Button(thewin, text="Clear", command=self.clear)
        cb.pack(side=tk.RIGHT, pady=5)

        # plan path on plan press
        sb = tk.Button(thewin, text="Plan!", command=self.plan_path)
        sb.pack(side=tk.RIGHT, pady=5)

        # information for user
        nodelablab = tk.Label(thewin, text="Node:")
        nodelablab.pack(side=tk.LEFT, padx=5)

        self.nodelab = tk.Label(thewin, text="None")
        self.nodelab.pack(side=tk.LEFT, padx=5)

        elablab = tk.Label(thewin, text="Elev:")
        elablab.pack(side=tk.LEFT, padx=5)

        self.elab = tk.Label(thewin, text="0")
        self.elab.pack(side=tk.LEFT, padx=5)

        thewin.pack()
