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

from bokeh.io import show
from bokeh.models import HoverTool
from bokeh.plotting import figure
from functions import *
import json

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
list_nodes_lan = []
list_edges = []
mac = {}
ipv4 = {i: [] for i in range(len(data["paquets"]))}
ipv6 = {i: [] for i in range(len(data["paquets"]))}
port = {i: [] for i in range(len(data["paquets"]))}
service = {i: [] for i in range(len(data["paquets"]))}
node_color = {i: "magenta" for i in range(len(data["paquets"]))}
n_pkts = {}
igmp = []

router = 0
mac[router] = []

for packet in data["paquets"]:
    if packet["port_src"] == 80 or packet["port_src"] == 443:
        if packet["src"] not in mac[router]:
            mac[router].append(packet["src"])
            list_nodes_lan.append(packet["src"])
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


# Create local network
graph_lan = nx.Graph()
for packet in data["paquets"]:
    if packet["ip_src"] == "192.168.10.15":
        print("hohoho")
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
        src_index, port_src = data_processing(
            packet, "src", list_nodes_lan, mac, ethertype, ipv6, ipv4, port
        )
        dst_index, port_dst = data_processing(
            packet, "dst", list_nodes_lan, mac, ethertype, ipv6, ipv4, port
        )
        graph_lan.add_edge(src_index, dst_index)

# create wan
graphs_wan = []
list_nodes_wan = []
list_networks = []
network = {}
router_wan = 1

for ip in ipv4[router]:
    parsed_ip = ip.split(".")
    if parsed_ip[0] in [str(i) for i in range(1, 128)]:
        if parsed_ip[0] not in list_networks:
            list_networks.append(parsed_ip[0])
            graphs_wan.append(nx.Graph())
            list_nodes_wan.append([router, router_wan])
        ntwk_index = list_networks.index(parsed_ip[0])
    elif parsed_ip[0] in [str(i) for i in range(128, 192)]:
        if parsed_ip[0] + "." + parsed_ip[1] not in list_networks:
            list_networks.append(parsed_ip[0] + "." + parsed_ip[1])
            graphs_wan.append(nx.Graph())
            list_nodes_wan.append([router, router_wan])
        ntwk_index = list_networks.index(parsed_ip[0] + "." + parsed_ip[1])
    elif parsed_ip[0] in [str(i) for i in range(192, 224)]:
        if parsed_ip[0] + "." + parsed_ip[1] + "." + parsed_ip[2] not in list_networks:
            list_networks.append(parsed_ip[0] + "." + parsed_ip[1] + "." + parsed_ip[2])
            graphs_wan.append(nx.Graph())
            list_nodes_wan.append([router, router_wan])
        ntwk_index = list_networks.index(
            parsed_ip[0] + "." + parsed_ip[1] + "." + parsed_ip[2]
        )
    list_nodes_wan[ntwk_index].append(ip)
    graphs_wan[ntwk_index].add_edge(router_wan, list_nodes_wan[ntwk_index].index(ip))

for i in range(len(list_networks)):
    graphs_wan[i].add_edge(router, router_wan)

ip_wan = [{i: network[i] for i in range(len(network))} for network in list_nodes_wan]

ipv4[router] = None
ipv6[router] = None
port[router] = None
service[router] = None


print("Adjusting layout...")

node_color = {i: {} for i in range(len(list_networks) + 1)}

for subnetwork in graphs_wan:
    ntwk_index = graphs_wan.index(subnetwork)
    for node in subnetwork:
        node_color[ntwk_index + 1][node] = "orange"
    node_color[ntwk_index][1] = "green"
    ip_wan[ntwk_index][1] = None

for node in graph_lan:
    if node == router:
        node_color[0][node] = "green"
    else:
        node_color[0][node] = "cyan"

nx.set_node_attributes(graph_lan, name="MAC", values=mac)
nx.set_node_attributes(graph_lan, name="IP_v4", values=ipv4)
nx.set_node_attributes(graph_lan, name="IP_v6", values=ipv6)
nx.set_node_attributes(graph_lan, name="node color", values=node_color[0])
nx.set_node_attributes(graph_lan, name="port", values=port)
nx.set_node_attributes(graph_lan, name="service", values=service)
nx.set_edge_attributes(graph_lan, name="n_pkts", values=n_pkts)
for subnetwork in graphs_wan:
    ntwk_index = graphs_wan.index(subnetwork)
    nx.set_node_attributes(graphs_wan[ntwk_index], name="IP", values=ip_wan[ntwk_index])
    nx.set_node_attributes(
        graphs_wan[ntwk_index], name="node color", values=node_color[ntwk_index + 1]
    )


plot = figure(
    tooltips=[],
    tools="pan,wheel_zoom,save,reset",
    active_scroll="wheel_zoom",
    x_range=(-2.5, 1.5),
    y_range=(-1.2, 1.2),
    height_policy="max",
    width_policy="max",
)

graphs_renderers_wan = {}
graph_renderer_lan = create_layout(graph_lan, router, (-0.5, 0), scale=1)
dim = math.isqrt(len(graphs_wan))
for index in range(len(graphs_wan)):
    ntwk_index = graphs_wan.index(graphs_wan[index])
    column = round(index // dim)
    graphs_renderers_wan[ntwk_index] = create_layout(
        graphs_wan[ntwk_index],
        router,
        (column + 2.2, index % dim - 1.3),
        scale=0.1,
        other_router=1,
    )


set_style(graph_renderer_lan)
for subnetwork in graphs_wan:
    ntwk_index = graphs_wan.index(subnetwork)
    set_style(graphs_renderers_wan[ntwk_index])

hover_nodes_lan = HoverTool(
    tooltips=[
        ("MAC", "@MAC"),
        ("IP v4", "@IP_v4"),
        ("IP v6", "@IP_v6"),
    ],
    renderers=[graph_renderer_lan.node_renderer],
)


hover_nodes_wan = {}
for subnetwork in graphs_wan:
    ntwk_index = graphs_wan.index(subnetwork)
    hover_nodes_wan[ntwk_index] = HoverTool(
        tooltips=[("IP", "@IP")],
        renderers=[graphs_renderers_wan[ntwk_index].node_renderer],
    )

plot.add_tools(hover_nodes_lan)

for subnetwork in graphs_wan:
    ntwk_index = graphs_wan.index(subnetwork)
    plot.add_tools(hover_nodes_wan[ntwk_index])

for subnetwork in graphs_wan:
    ntwk_index = graphs_wan.index(subnetwork)
    plot.renderers.append(graphs_renderers_wan[ntwk_index])
plot.renderers.append(graph_renderer_lan)

show(plot)
end = time()
print("Done in", end - start, "s")
