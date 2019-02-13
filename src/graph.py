import constants
import math
import struct
import xml.etree.ElementTree as ET
from queue import PriorityQueue


class Node():
    ''' Location Node '''
    __slots__ = ('id', 'pos', 'ways', 'elev', 'waystr')

    def __init__(self, id, pos, elev=0):
        self.id = id
        self.pos = pos
        self.ways = []
        self.elev = elev
        self.waystr = None

    def __str__(self):
        if self.waystr is None:
            self.waystr = self.get_waystr()
        return str(self.pos) + ": " + self.waystr

    def get_waystr(self):
        if self.waystr is None:
            self.waystr = ""
            wayset = set()
            for w in self.ways:
                wayset.add(w.way.name)
            for w in wayset:
                self.waystr += w + " "
        return self.waystr

    def get_str(self):
        return (str(self.id) + "\n" + str(self.pos) + "\n" + str(self.elev))

    def node_dist(self, n2):
        ''' Distance between nodes self and n2, in meters. '''
        dx = (n2.pos[0]-self.pos[0]) * constants.MPERLON
        dy = (n2.pos[1]-self.pos[1]) * constants.MPERLAT
        return math.sqrt(dx*dx+dy*dy)  # in meters

    def add_way(self, edge):
        self.ways.append(edge)


class Edge():
    ''' Graph (map) edge. Includes cost computation.'''
    __slots__ = ('way', 'dest', 'cost')

    def __init__(self, way, src, dest):
        self.way = way
        self.dest = dest
        self.cost = src.node_dist(self.dest)
        if self.dest.elev > src.elev:
            self.cost += (self.dest.elev-src.elev)*2
            if self.way.t == 'steps':
                self.cost *= 1.5


class Way():
    ''' A way is an entire street, for drawing, not searching. '''
    __slots__ = ('name', 't', 'nodes')
    # nodes here for ease of drawing only

    def __init__(self, name, t):
        self.name = name
        self.t = t
        self.nodes = []

    def set_nodes(self, nodes):
        self.nodes = nodes

    def __str__(self):
        return self.name + " " + self.t


class Planner():
    __slots__ = ('nodes', 'ways')

    def __init__(self, nodes, ways):
        self.nodes = nodes
        self.ways = ways

    def plan(self, start, goal):
        '''
        Standard A* search
        '''
        parents = {}
        costs = {}
        q = PriorityQueue()
        q.put(start)
        parents[start] = None
        costs[start] = 0
        while not q.empty():
            cnode = q.get()
            if cnode == goal:
                print("Path found, time will be",
                      costs[goal]*60/5000)  # 5 km/hr on flat
                return self.make_path(parents, goal)
            for edge in cnode.ways:
                newcost = costs[cnode] + edge.cost
                if edge.dest not in parents or newcost < costs[edge.dest]:
                    parents[edge.dest] = (cnode, edge.way)
                    costs[edge.dest] = newcost
                    q.put(edge.dest)

    def make_path(self, par, new):
        nodes = []
        ways = []
        curr = new
        nodes.append(curr)
        while par[curr] is not None:
            prev, way = par[curr]
            ways.append(way.name)
            nodes.append(prev)
            curr = prev
        nodes.reverse()
        ways.reverse()
        return nodes, ways

# TODO: add data range for elevation
#       automatically detect and adjust for north / south, east / west coordinates
#       add suport for crossing equator, prime meridian


def build_graph(elevs, street_data, num_hgt_dim):
    ''' Build the search graph from the OpenStreetMap XML. '''

    root = street_data.getroot()

    nodes = dict()
    ways = dict()

    for item in root:

        if item.tag == 'node':
            coords = [float(item.get('lat')), float(item.get('lon'))]

            # row is 0 for bottom of hgt data, max (usually 1201 or 3601) for top
            erow = (int)(abs((coords[0]-constants.HGT_BOT)) * num_hgt_dim)
            # col is 0 for far left of hgt data, max (usually 1201 or 3601) for top
            ecol = (int)(abs(1 - (coords[1]-constants.HGT_LEFT)) * num_hgt_dim)

            try:
                el = elevs[erow, ecol]

            except IndexError:
                str = "Point is too far: "
                if coords[0] >= constants.HGT_BOT + 1:
                    str += "North, "
                if coords[0] <= constants.HGT_BOT:
                    str += "South, "
                if coords[1] >= constants.HGT_LEFT + 1:
                    str += "East, "
                if coords[1] <= constants.HGT_LEFT:
                    str += "West, "
                str = str[:-2]
                print(str, coords)
                el = 0
            nodes[(item.get('id'))] = Node(
                (item.get('id')), coords, el)

        elif item.tag == 'way':
            usable = False
            oneway = False
            name = 'unnamed way'
            # sets the usability, name and whether the way is one way
            for elem in item:
                if elem.tag == 'tag' and elem.get('k') == 'highway':
                    usable = True
                    waytype = elem.get('v')
                if elem.tag == 'tag' and elem.get('k') == 'name':
                    name = elem.get('v')
                if elem.tag == 'tag' and elem.get('k') == 'oneway':
                    if elem.get('v') == 'yes':
                        oneway = True
            # if the way is usable add it to the ways
            if usable:
                wayid = (item.get('id'))
                ways[wayid] = Way(name, waytype)
                nlist = []
                # add all of the ref nodes to the node list
                for elem in item:
                    if elem.tag == 'nd':
                        nlist.append((elem.get('ref')))
                # starting with the first node
                thisn = nlist[0]
                for n in range(len(nlist)-1):
                    nextn = nlist[n+1]
                    # add the way to get to the next referenced node
                    nodes[thisn].add_way(
                        Edge(ways[wayid], nodes[thisn], nodes[nextn]))
                    # move to the next node
                    thisn = nextn
                # if the road is not one way do the same thing in reverse
                if not oneway:
                    thisn = nlist[-1]
                    for n in range(len(nlist)-2, -1, -1):
                        nextn = nlist[n]
                        nodes[thisn].add_way(
                            Edge(ways[wayid], nodes[thisn], nodes[nextn]))
                        thisn = nextn
                # save the node list in the way
                ways[wayid].set_nodes(nlist)
    return (nodes, ways)
