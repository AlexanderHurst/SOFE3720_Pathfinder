import constants
import math
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

    def make_path(self, par, g):
        nodes = []
        ways = []
        curr = g
        nodes.append(curr)
        while par[curr] is not None:
            prev, way = par[curr]
            ways.append(way.name)
            nodes.append(prev)
            curr = prev
        nodes.reverse()
        ways.reverse()
        return nodes, ways
