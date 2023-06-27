"""Takes a .json file with log data and plots a directed graph representing who communicates with who (not finished at all)
Usage:
=====
    python3 main_v3.py file_name.json

    file_name: name of the file (with the relative path) from which we want data
"""

__authors__ = "Clara Moy"
__contact__ = "c.m0y@yahoo.com"
__copyright__ = "MIT"
__date__ = "2023-06-26"

import sys
from time import time

from bokeh.io import show
from bokeh.models import HoverTool
from bokeh.plotting import figure
from functions import *
import getmac
import holoviews as hv
import json
import numpy as np
import socket


hv.extension("bokeh")

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
list_nodes_wan = []
my_mac_adress = getmac.get_mac_address()
my_ipv4 = []
my_ipv6 = []
ip_wan = {}
my_subnetwork = []
mac = {}
ipv4 = {i: [] for i in range(len(data["paquets"]))}
ipv6 = {i: [] for i in range(len(data["paquets"]))}
port = {i: [] for i in range(len(data["paquets"]))}
service = {i: [] for i in range(len(data["paquets"]))}
node_color = {i: "magenta" for i in range(len(data["paquets"]))}
# outline_color = {i: "black" for i in range(len(data["paquets"]))}
n_pkts = {}

# Create graph
graph = nx.Graph()

# search router
for packet in data["paquets"]:
    if packet["port_src"] == 80:
        router = 0
        mac[router] = packet["src"]
        list_nodes.append(packet["src"])
        break

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
    ):
        # Create mac adress list
        src = packet["src"]
        dst = packet["dst"]
        ipv4_src = packet["ip_src"]
        ipv4_dst = packet["ip_dst"]
        ipv6_src = packet["ip_src"]
        ipv6_dst = packet["ip_dst"]
        port_src = packet["port_src"]
        port_dst = packet["port_dst"]

        if src not in list_nodes:
            list_nodes.append(src)
        if dst not in list_nodes:
            list_nodes.append(dst)

        src_index = list_nodes.index(src)
        dst_index = list_nodes.index(dst)

        mac[src_index] = src
        mac[dst_index] = dst

        if src_index == router:
            if ipv4_src not in list_nodes:
                list_nodes.append(ipv4_src)
            n = list_nodes.index(ipv4_src)
            if n not in list_nodes_wan:
                list_nodes_wan.append(n)
            mac[n] = None
            src_index = n
        if dst_index == router:
            if ipv4_dst not in list_nodes:
                list_nodes.append(ipv4_dst)
            n = list_nodes.index(ipv4_dst)
            if n not in list_nodes_wan:
                list_nodes_wan.append(n)
            mac[n] = None
            dst_index = n

        # Associate ipV6 adress to mac adress
        if ethertype == "ipV6":
            if ipv6_src not in ipv6[src_index]:
                ipv6[src_index].append(ipv6_src)
            if ipv6_dst not in ipv6[dst_index]:
                ipv6[dst_index].append(ipv6_dst)
        # Associate ipV4 adress to mac adress
        else:
            if ipv4_src not in ipv4[src_index]:
                ipv4[src_index].append(ipv4_src)
            if ipv4_dst not in ipv4[dst_index]:
                ipv4[dst_index].append(ipv4_dst)

        # Associate port to mac adress

        if port_src is not None and port_src > 1024:
            port_src = ">1024"
        if port_dst is not None and port_dst > 1024:
            port_dst = ">1024"

        if port_src not in port[src_index]:
            port[src_index].append(port_src)
        if port_dst not in port[dst_index]:
            port[dst_index].append(port_dst)

        # Find service from port and protocol
        proto_number = packet["proto"]
        if proto_number is not None:
            proto = ip_protocols_db[str(proto_number)]["keyword"].lower()
            try:
                if port_src != ">1024" and port_src is not None:
                    service_src = socket.getservbyport(port_src, proto)
                    if service_src not in service[src_index]:
                        service[src_index].append(service_src)
                if port_dst != ">1024" and port_dst is not None:
                    service_dst = socket.getservbyport(port_dst, proto)
                    if service_dst not in service[dst_index]:
                        service[dst_index].append(service_dst)
            except OSError:
                if (
                    port_src != ">1024"
                    and port_src is not None
                    and proto not in service[src_index]
                ):
                    service[src_index].append(proto)
                elif (
                    port_dst != ">1024"
                    and port_dst is not None
                    and proto not in service[dst_index]
                ):
                    service[dst_index].append(proto)

        # count packets between devices
        if (src_index, dst_index) in n_pkts.keys():
            n_pkts[(src_index, dst_index)] += 1
        elif (dst_index, src_index) in n_pkts.keys():
            n_pkts[(dst_index, src_index)] += 1
        else:
            n_pkts[(src_index, dst_index)] = 1
        graph.add_edge(src_index, dst_index)

list_nodes_lan = []
for i in range(len(list_nodes)):
    if i not in list_nodes_wan:
        list_nodes_lan.append(i)


print("Adjusting layout...")

for node in graph:
    if mac[node] == my_mac_adress:
        my_ipv4 += ipv4[node]
        my_ipv6 += ipv6[node]
        node_color[node] = "red"
    elif node == router:
        node_color[node] = "green"
    elif port[node] == [None]:
        node_color[node] = "pink"
    elif ">1024" not in port[node]:
        node_color[node] = "blue"
    elif (
        port[node] != [">1024"]
        and port[node] != [None, ">1024"]
        and port[node] != [">1024", None]
    ):
        node_color[node] = "cyan"

for node in list_nodes_wan:
    node_color[node] = "orange"

nx.set_node_attributes(graph, name="MAC", values=mac)
nx.set_node_attributes(graph, name="IP_v4", values=ipv4)
nx.set_node_attributes(graph, name="IP_v6", values=ipv6)
nx.set_node_attributes(graph, name="node color", values=node_color)
# nx.set_node_attributes(graph_lan, name="outline color", values=outline_color)
nx.set_node_attributes(graph, name="port", values=port)
nx.set_node_attributes(graph, name="service", values=service)
nx.set_edge_attributes(graph, name="n_pkts", values=n_pkts)

hv_graph = hv.Graph.from_networkx(graph, nx.layout.circular_layout).opts(
    tools=["hover"]
)

plot = figure(
    tools="pan,wheel_zoom,save,reset",
    active_scroll="wheel_zoom",
    x_range=(-1.2, 3.3),
    y_range=(-1.2, 1.2),
    height_policy="max",
    width_policy="max",
)

# create layout
fixed_layout = {}
n_servers = len(list_nodes_wan)
n_non_servers = len(list_nodes_lan)
angles = np.linspace(-np.pi / 2, np.pi / 2, n_non_servers)
for i in range(len(list_nodes_lan)):
    fixed_layout[list_nodes_lan[i]] = (np.cos(angles[i]) - 1, np.sin(angles[i]))
pos = np.linspace(-1, 1, n_servers)
for i in range(len(list_nodes_wan)):
    fixed_layout[list_nodes_wan[i]] = (3, pos[i])
fixed_layout_provider = StaticLayoutProvider(graph_layout=fixed_layout)
graph_renderer = from_networkx(graph, nx.spring_layout)
graph_renderer.layout_provider = fixed_layout_provider

hover_nodes = HoverTool(
    tooltips=[
        ("MAC", "@MAC"),
        ("IP v4", "@IP_v4"),
        ("IP v6", "@IP_v6"),
        ("Port", "@port"),
        ("service", "@service"),
    ],
    renderers=[graph_renderer.node_renderer],
)

hover_edges = HoverTool(
    tooltips=[("n pkts", "@n_pkts")],
    renderers=[graph_renderer.edge_renderer],
)

plot.add_tools(hover_edges, hover_nodes)

set_style(graph_renderer)
plot.renderers.append(graph_renderer)

show(plot)
end = time()
print("Done in", end - start, "s")