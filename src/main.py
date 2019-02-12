from graph import build_elevs, build_graph
import tkinter as tk
from gui import PlanWin
elevs = build_elevs("N43W079.hgt")
nodes, ways, coastnodes = build_graph(elevs)

master = tk.Tk()
thewin = PlanWin(master, nodes, ways, coastnodes, elevs)
tk.mainloop()
