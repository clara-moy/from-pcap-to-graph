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
from modified_netgraph import NewInteractiveGraph
import numpy as np
import pandas as pd
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

# Initialize variables
list_nodes = []
ntwk_prefix = {}
subnetworks = {0: []}
mac = {}
ipv4 = {}
ipv6 = {}
port = {}
service = {}
node_color = {}
n_pkts = {}
mapping = {}
igmp = []

router = 0
mac[router] = []
router_proto = []
router_ip = []

print("Finding router...")

for packet in data["paquets"]:
    if packet["port_src"] == 80 or packet["port_src"] == 443:
        src = packet["src"]
        if src not in mac[router]:
            mac[router].append(src)
            index = mac[router].index(src)
            router_proto.append([])
            router_ip.append([])
        index = mac[router].index(src)
        proto = packet["proto"]
        ip = packet["ip_src"]
        if proto not in router_proto[index]:
            router_proto[index].append(proto)
        if ip not in router_ip[index]:
            router_ip[index].append(ip)

i = 0
while len(mac[router]) != 1 and i != 10:
    print(mac[router])
    i += 1
    for potential_router in mac[router]:
        try:
            index = mac[router].index(potential_router)
            for ip in router_ip[index]:
                try:
                    for other_ip in router_ip[index]:
                        if (
                            ip is not None
                            and ip != "0.0.0.0"
                            and other_ip is not None
                            and other_ip != "0.0.0.0"
                        ):
                            if ip[:3] != other_ip[:3]:
                                mac[router] = [potential_router]
                                router_ip = []
                                break
                except IndexError:
                    break
        except ValueError:
            break


if len(mac[router]) != 1:
    print("failed to find router")
else:
    list_nodes.append(mac[router][0])


print("Creating graph...")


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
scale = 1
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

fig, ax = plt.subplots()

table = {}
for index in range(len(list_nodes)):
    if index not in mac.keys():
        mac[index] = None
    if type(ipv4[index]) == list:
        ip_adress = ""
        for ip in ipv4[index]:
            if ip != None:
                ip_adress += ip + ", "
        table.update(
            {
                index: pd.DataFrame(
                    {"MAC adress": [mac[index]], "IP adress": ip_adress},
                    index=[""],
                )
            }
        )
    else:
        table.update(
            {
                index: pd.DataFrame(
                    {"MAC adress": [mac[index]], "IP adress": str(ipv4[index])},
                    index=[""],
                )
            }
        )

fig = NewInteractiveGraph(
    graph,
    # annotations=annotations,
    node_layout=layout,
    node_color=node_color,
    edge_width=0.4,
    edge_color="black",
    tables=table,
)

scale = 1.1
zp = ZoomPan()
figZoom = zp.zoom_factory(ax, base_scale=scale)
figPan = zp.pan_factory(ax)

fig.mouseover_highlight_mapping = mapping

end = time()
print("Done in", end - start, "s")
plt.show()
