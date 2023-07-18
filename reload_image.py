"""
Reloads data from main.py and plots them (allows to not recalculate data)

Usage:
=====
    python3 reload_image.py file_name

    file_name: name of the file where data from main.py were saved
"""

import pickle
import matplotlib.pyplot as plt
import sys
from modified_netgraph import NewInteractiveGraph
from zoom import ZoomPan
import numpy as np

np.seterr(divide="ignore", invalid="ignore")

with open(sys.argv[1], "rb") as file:
    data = pickle.load(file)

fig, ax = plt.subplots()

fig = NewInteractiveGraph(
    data["graph"],
    node_layout=data["layout"],
    node_color=data["node_color"],
    edge_width=data["edge_width"],
    edge_color=data["edge_color"],
    tables=data["table"],
    mapping=data["mapping"],
    annotations=data["annotations"],
)

scale = 1.1
zp = ZoomPan()
figZoom = zp.zoom_factory(ax, base_scale=scale)
figPan = zp.pan_factory(ax)

plt.show()
