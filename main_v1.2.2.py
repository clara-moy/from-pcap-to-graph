"""Takes a .json file with log data and plots a graph representing the topology of the network
Usage:
=====
    python3 main_v1.py file_name.json

    file_name: name of the file (with the relative path) from which we want data
"""

__authors__ = "Clara Moy"
__contact__ = "c.m0y@yahoo.com"
__copyright__ = "MIT"
__date__ = "2023-06-26"

import math
import sys
from time import time

from functions import *
import json
import matplotlib.pyplot as plt
from netgraph._main import InteractiveGraph
import numpy as np

# from pyvis.network import Network
from zoom import ZoomPan

np.seterr(divide="ignore", invalid="ignore")

print("Extracting data...")
file_name = sys.argv[1]
start = time()
with open(file_name) as file:
    data = json.load(file)
with open("numbers/ip-protocol-numbers.json") as file:
    ip_protocols_db = json.load(file)
with open("numbers/ethertypes.json") as file:
    ethertypes = json.load(file)

print("Creating graph...")

# Initialize variables
list_nodes = []
ntwk_prefix = {}
subnetworks = {0: []}
mac = {}
ipv4 = {i: [] for i in range(len(data["paquets"]))}
ipv6 = {i: [] for i in range(len(data["paquets"]))}
port = {i: [] for i in range(len(data["paquets"]))}
service = {i: [] for i in range(len(data["paquets"]))}
node_color = {i: "magenta" for i in range(len(data["paquets"]))}
n_pkts = {}
mapping = {}
igmp = []

router = 0
mac[router] = []

for packet in data["paquets"]:
    if packet["port_src"] == 80 or packet["port_src"] == 443:
        if packet["src"] not in mac[router]:
            mac[router].append(packet["src"])
#     if packet["proto"] == 2:
#         igmp.append([packet["ip_src"], packet["ip_dst"]])

# print(igmp)

i = 0
while len(mac[router]) != 1 and i != 10:
    print(mac[router])
    i += 1
    for packet in data["paquets"]:
        if packet["src"] in mac[router]:
            if packet["proto"] == 89 or packet["ip_src"] == "224.0.0.9":
                print(packet["ip_src"])
                router = [packet["src"]]
                break
            elif packet["proto"] == 1:
                mac[router].remove(packet["src"])

if len(mac[router]) != 1:
    print("failed to find router")
else:
    list_nodes.append(mac[router][0])

# Create local network
graph = nx.Graph()
for packet in data["paquets"]:
    try:
        ethertype = ethertypes[str(packet["type"])]
    except (KeyError, TypeError):
        ethertype = "unknown"
    if (
        packet["ip_src"] is not None
        and packet["ip_dst"] is not None
        and packet["ip_src"][:4] != "ff02"
        and packet["ip_dst"][:4] != "ff02"
        and packet["ip_src"][:3] not in [str(i) for i in range(224, 240)]
        and packet["ip_dst"][:3] not in [str(i) for i in range(224, 240)]
        and packet["src"] != "ff:ff:ff:ff:ff:ff"
        and packet["dst"] != "ff:ff:ff:ff:ff:ff"
    ):
        src_index, dist_src_index, src_ntwk_index, port_src = data_processing(
            packet,
            "src",
            list_nodes,
            mac,
            ethertype,
            ipv6,
            ipv4,
            port,
            ntwk_prefix,
            subnetworks,
        )
        dst_index, dist_dst_index, dst_ntwk_index, port_dst = data_processing(
            packet,
            "dst",
            list_nodes,
            mac,
            ethertype,
            ipv6,
            ipv4,
            port,
            ntwk_prefix,
            subnetworks,
        )
        update_mapping(
            src_index, dist_src_index, mapping, dst_index, graph, src_ntwk_index
        )
        update_mapping(
            dst_index, dist_dst_index, mapping, src_index, graph, dst_ntwk_index
        )

ipv4[router] = None
ipv6[router] = None
port[router] = None
service[router] = None

print("Adjusting layout...")

node_color = {}

for node in graph:
    if node in subnetworks.keys():
        node_color[node] = "green"
    elif node in subnetworks[0]:
        node_color[node] = "cyan"
    else:
        node_color[node] = "orange"

layout = {}

i = 0
scale = 0.6
n_subnetworks = len(subnetworks)
dim = round(math.sqrt(n_subnetworks))
for subnetwork in subnetworks.keys():
    if subnetwork == 0:
        add = dim * scale / 2.5
    else:
        add = 0
    column = round((i - 1) // dim)
    layout[subnetwork] = (column * scale, i % dim * scale + add)
    angles = np.linspace(0, 1, len(subnetworks[subnetwork]) + 1)[:-1] * 2 * np.pi
    for j in range(len(subnetworks[subnetwork])):
        angle = angles[j]
        layout[subnetworks[subnetwork][j]] = (
            (math.sin(angle) / 3 + column) * scale,
            (math.cos(angle) / 3 + i % dim) * scale + add,
        )
    i += 1

annotations = {}

for i in range(len(list_nodes)):
    if i in mac.keys():
        annotations[i] = "MAC : " + str(mac[i]) + "\nIP : "
    else:
        annotations[i] = "MAC : None\nIP : "
    if ipv4[i] != None:
        for ip in ipv4[i]:
            annotations[i] += ip

# nt = Network("500px", "1000px")
# node_color_2 = [node_color[i] for i in node_color.keys()]
# nt.add_nodes(list(graph.nodes), color=node_color_2)
# nt.add_edges(graph.edges)
# nt.show("hoho.html")

fig, ax = plt.subplots()

fig = InteractiveGraph(
    graph,
    annotations=annotations,
    # node_labels=True,
    node_layout=layout,
    node_color=node_color,
    edge_width=0.4,
    edge_color="black",
)

scale = 1.1
zp = ZoomPan()
figZoom = zp.zoom_factory(ax, base_scale=scale)
figPan = zp.pan_factory(ax)

fig.mouseover_highlight_mapping = mapping

end = time()
print("Done in", end - start, "s")
plt.show()
