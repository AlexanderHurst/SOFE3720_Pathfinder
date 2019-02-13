from graph import build_graph
import tkinter as tk
from gui import PlanWin
import data_parser
import xml.etree.ElementTree as ET

elev_data, num_hgt_dim = data_parser.to_numpy("data/N43W079.hgt")

nodes, ways = build_graph(
    elev_data, ET.parse('data/map'), num_hgt_dim)


# elevs = build_elevs("../data/N43W079.hgt")
# nodes, ways, coastnodes = build_graph(elevs)

master = tk.Tk()
thewin = PlanWin(master, nodes, ways, elev_data, num_hgt_dim)
tk.mainloop()
