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
                self.waystr += w.encode("utf-8") + " "
        return self.waystr

    def node_dist(self, n2):
        ''' Distance between nodes self and n2, in meters. '''
        dx = (n2.pos[0]-self.pos[0]) * constants.MPERLON
        dy = (n2.pos[1]-self.pos[1]) * constants.MPERLAT
        return math.sqrt(dx*dx+dy*dy)  # in meters


class Edge():
    ''' Graph (map) edge. Includes cost computation.'''
    __slots__ = ('way', 'dest', 'cost')

    def __init__(self, way, src, dest):
        self.way = way
        self.dest = dest
        self.cost = src.node_dist(self.dest)
        if self.dest.elev > src.elev:
            self.cost += (self.dest.elev-src.elev)*2
            if self.way.type == 'steps':
                self.cost *= 1.5


class Way():
    ''' A way is an entire street, for drawing, not searching. '''
    __slots__ = ('name', 't', 'nodes')
    # nodes here for ease of drawing only

    def __init__(self, name, t):
        self.name = name
        self.t = t
        self.nodes = []


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


def build_elevs(efilename):
    ''' read in elevations from a file. '''
    efile = open(efilename)
    estr = efile.read()
    elevs = []
    for spot in range(0, len(estr), 2):
        elevs.append(struct.unpack('>h', estr[spot:spot+2])[0])
    return elevs


def build_graph(elevs):
    ''' Build the search graph from the OpenStreetMap XML. '''
    tree = ET.parse('dbv.osm')
    root = tree.getroot()

    nodes = dict()
    ways = dict()
    coastnodes = []
    for item in root:
        if item.tag == 'node':
            coords = ((float)(item.get('lat')), (float)(item.get('lon')))
            # row is 0 for 43N, 1201 (EPIX) for 42N
            erow = (int)((43 - coords[0]) * constants.EPIX)
            # col is 0 for 18 E, 1201 for 19 E
            ecol = (int)((coords[1]-18) * constants.EPIX)
            try:
                el = elevs[erow*constants.EPIX+ecol]
            except IndexError:
                el = 0
            nodes[(item.get('id'))] = Node(
                (item.get('id')), coords, el)
        elif item.tag == 'way':
            if item.get('id') == '157161112':  # main coastline way ID
                for thing in item:
                    if thing.tag == 'nd':
                        coastnodes.append((thing.get('ref')))
                continue
            useme = False
            oneway = False
            myname = 'unnamed way'
            for thing in item:
                if thing.tag == 'tag' and thing.get('k') == 'highway':
                    useme = True
                    mytype = thing.get('v')
                if thing.tag == 'tag' and thing.get('k') == 'name':
                    myname = thing.get('v')
                if thing.tag == 'tag' and thing.get('k') == 'oneway':
                    if thing.get('v') == 'yes':
                        oneway = True
            if useme:
                wayid = (item.get('id'))
                ways[wayid] = Way(myname, mytype)
                nlist = []
                for thing in item:
                    if thing.tag == 'nd':
                        nlist.append((thing.get('ref')))
                thisn = nlist[0]
                for n in range(len(nlist)-1):
                    nextn = nlist[n+1]
                    nodes[thisn].ways.append(
                        Edge(ways[wayid], nodes[thisn], nodes[nextn]))
                    thisn = nextn
                if not oneway:
                    thisn = nlist[-1]
                    for n in range(len(nlist)-2, -1, -1):
                        nextn = nlist[n]
                        nodes[thisn].ways.append(
                            Edge(ways[wayid], nodes[thisn], nodes[nextn]))
                        thisn = nextn
                ways[wayid].nodes = nlist
    print(len(coastnodes))
    print(coastnodes[0])
    print(nodes[coastnodes[0]])
    return nodes, ways, coastnodes
