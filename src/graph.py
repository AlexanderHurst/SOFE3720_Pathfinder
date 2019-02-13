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

    # creates a string with all the ways connected to the node
    def get_waystr(self):
        if self.waystr is None:
            self.waystr = ""
            wayset = set()
            for w in self.ways:
                wayset.add(w.way.name)
            for w in wayset:
                self.waystr += w + " "
        return self.waystr

    # quick string representation without the list of ways
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

        # if uphill add uphill penalty
        if self.dest.elev > src.elev:
            self.cost += (self.dest.elev-src.elev)*1.25


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
        cost, cost_est = {}, {}
        parents[start] = None
        # remember the cost to get to the node
        cost[start] = 0
        # use heuristic to assign a cost estimate
        # in this case, euclidean distance (elevation not included)
        cost_est[start] = start.node_dist(goal)

        # priority queue, holds the node sorted by
        # the cost to the node + estimated cost to the finish
        q = PriorityQueue()
        q.put((cost_est, start))

        while not q.empty():
            # get the lowest element in the queue by cost_est
            cur_node = q.get()
            if cur_node[1] == goal:
                print("Path found, time will be",
                      round(cost[goal]*60/5000), " minutes")  # 5 km/hr on flat
                # make the path
                return self.make_path(parents, goal)
            for edge in cur_node[1].ways:
                # new est cost is the current cost to get to the current node
                # + cost to get to the edge dest
                # + heuristic cost to get to goal from the edge dest
                new_est_cost = cost[cur_node[1]] + \
                    edge.cost + edge.dest.node_dist(goal)
                if edge.dest not in parents or new_est_cost < cost_est[edge.dest]:
                    # keep track of the path
                    parents[edge.dest] = (cur_node[1], edge.way)
                    # update the est cost
                    cost_est[edge.dest] = new_est_cost
                    # set the cost to edge dest
                    cost[edge.dest] = cost[cur_node[1]] + edge.cost
                    # put the edge dest in the queue
                    q.put((new_est_cost, edge.dest))

    def make_path(self, path, goal):
        nodes = []
        ways = []
        curr = goal
        nodes.append(goal)
        while path[curr] is not None:
            # get the previous node and path
            prev, way = path[curr]
            # add these to their own lists
            ways.append(way.name)
            nodes.append(prev)
            # move to the next, previous node
            curr = prev
        # reverse lists to put goal last, start first
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
            erow = (int)(
                (1 - ((constants.HGT_BOT + 1) - coords[0])) * num_hgt_dim)
            # col is 0 for far left of hgt data, max (usually 1201 or 3601) for top
            ecol = (int)((coords[1]-constants.HGT_LEFT) * num_hgt_dim)
            try:
                el = elevs[erow, ecol]

            except IndexError:
                # str = "Point is too far: "
                # if coords[0] >= constants.HGT_BOT + 1:
                #     str += "North, "
                # if coords[0] <= constants.HGT_BOT:
                #     str += "South, "
                # if coords[1] >= constants.HGT_LEFT + 1:
                #     str += "East, "
                # if coords[1] <= constants.HGT_LEFT:
                #     str += "West, "
                # str = str[:-2]
                # print(str, coords)
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
