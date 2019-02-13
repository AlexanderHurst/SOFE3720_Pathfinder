import constants
import tkinter as tk
from graph import Planner


class PlanWin(tk.Frame):
    '''
    All the GUI pieces to draw the streets, allow places to be selected,
    and then draw the resulting path.
    '''

    __slots__ = ('whatis', 'nodes', 'ways', 'elevs', 'nodelab', 'elab',
                 'planner', 'lastnode', 'startnode', 'goalnode')

    def lat_lon_to_pix(self, latlon):
        x = (latlon[1]-constants.LEFTLON)*(constants.TOXPIX)
        y = (constants.TOPLAT-latlon[0])*(constants.TOYPIX)
        return x, y

    def pix_to_elev(self, x, y):
        return self.lat_lon_to_elev(((constants.TOPLAT-(y/constants.TOYPIX)), ((x/constants.TOXPIX)+constants.LEFTLON)))

    def lat_lon_to_elev(self, latlon):
        # row is 0 for 43N, 1201 (EPIX) for 42N
        row = (int)((constants.HGT_BOT - latlon[0]) * self.dim)
        # col is 0 for 18 E, 1201 for 19 E
        col = (int)((latlon[1]-constants.HGT_LEFT) * self.dim)
        print(row, col)
        return self.elevs[row, col]

    def maphover(self, event):
        self.elab.configure(text=str(self.pix_to_elev(event.x, event.y)))
        for (dx, dy) in [(0, 0), (-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            ckpos = (event.x+dx, event.y+dy)
            if ckpos in self.whatis:
                self.lastnode = self.whatis[ckpos]
                lnpos = self.lat_lon_to_pix(self.nodes[self.lastnode].pos)
                self.canvas.coords(
                    'lastdot', (lnpos[0]-2, lnpos[1]-2, lnpos[0]+2, lnpos[1]+2))
                nstr = str(self.lastnode)
                nstr += " "
                nstr += str(self.nodes[self.whatis[ckpos]].get_waystr())
                self.nodelab.configure(text=nstr)
                return

    def mapclick(self, event):
        ''' Canvas click handler:
        First click sets path start, second sets path goal 
        '''
        print("Clicked on "+str(event.x)+"," +
              str(event.y)+" last node "+str(self.lastnode))
        if self.lastnode is None:
            return
        if self.startnode is None:
            self.startnode = self.nodes[self.lastnode]
            self.snpix = self.lat_lon_to_pix(self.startnode.pos)
            self.canvas.coords(
                'startdot', (self.snpix[0]-2, self.snpix[1]-2, self.snpix[0]+2, self.snpix[1]+2))
        elif self.goalnode is None:
            self.goalnode = self.nodes[self.lastnode]
            self.snpix = self.lat_lon_to_pix(self.goalnode.pos)
            self.canvas.coords(
                'goaldot', (self.snpix[0]-2, self.snpix[1]-2, self.snpix[0]+2, self.snpix[1]+2))

    def clear(self):
        ''' Clear button callback. '''
        self.lastnode = None
        self.goalnode = None
        self.startnode = None
        self.canvas.coords('startdot', (0, 0, 0, 0))
        self.canvas.coords('goaldot', (0, 0, 0, 0))
        self.canvas.coords('path', (0, 0, 0, 0))

    def plan_path(self):
        ''' Path button callback, plans and then draws path.'''
        print("Planning!")
        if self.startnode is None or self.goalnode is None:
            print("Sorry, not enough info.")
            return
        print("From", self.startnode.id, "to", self.goalnode.id)
        nodes, ways = self.planner.plan(self.startnode, self.goalnode)
        lastway = ""
        for wayname in ways:
            if wayname != lastway:
                print(wayname)
                lastway = wayname
        coords = []
        for node in nodes:
            npos = self.lat_lon_to_pix(node.pos)
            coords.append(npos[0])
            coords.append(npos[1])
            # print node.id
        self.canvas.coords('path', *coords)

    def __init__(self, master, nodes, ways, elevs, dim):
        self.whatis = {}
        self.nodes = nodes
        self.ways = ways
        self.elevs = elevs
        self.startnode = None
        self.goalnode = None
        self.planner = Planner(nodes, ways)
        self.dim = dim
        thewin = tk.Frame(master)
        # , cursor="crosshair")
        w = tk.Canvas(thewin, width=constants.WINWID, height=constants.WINHGT)
        w.bind("<Button-1>", self.mapclick)
        w.bind("<Motion>", self.maphover)
        for waynum in self.ways:
            nlist = self.ways[waynum].nodes
            thispix = self.lat_lon_to_pix(self.nodes[nlist[0]].pos)
            if len(self.nodes[nlist[0]].ways) > 2:
                self.whatis[((int)(thispix[0]), (int)(thispix[1]))] = nlist[0]
            for n in range(len(nlist)-1):
                nextpix = self.lat_lon_to_pix(self.nodes[nlist[n+1]].pos)
                self.whatis[((int)(nextpix[0]), (int)
                             (nextpix[1]))] = nlist[n+1]
                w.create_line(thispix[0], thispix[1], nextpix[0], nextpix[1])
                thispix = nextpix

        # other visible things are hiding for now...
        w.create_line(0, 0, 0, 0, fill='orange', width=3, tag='path')

        w.create_oval(0, 0, 0, 0, outline='green',
                      fill='green', tag='startdot')
        w.create_oval(0, 0, 0, 0, outline='red', fill='red', tag='goaldot')
        w.create_oval(0, 0, 0, 0, outline='blue', fill='blue', tag='lastdot')
        w.pack(fill=tk.BOTH)
        self.canvas = w

        cb = tk.Button(thewin, text="Clear", command=self.clear)
        cb.pack(side=tk.RIGHT, pady=5)

        sb = tk.Button(thewin, text="Plan!", command=self.plan_path)
        sb.pack(side=tk.RIGHT, pady=5)

        nodelablab = tk.Label(thewin, text="Node:")
        nodelablab.pack(side=tk.LEFT, padx=5)

        self.nodelab = tk.Label(thewin, text="None")
        self.nodelab.pack(side=tk.LEFT, padx=5)

        elablab = tk.Label(thewin, text="Elev:")
        elablab.pack(side=tk.LEFT, padx=5)

        self.elab = tk.Label(thewin, text="0")
        self.elab.pack(side=tk.LEFT, padx=5)

        thewin.pack()
