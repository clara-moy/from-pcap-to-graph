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

import sys
from time import time

from bokeh.io import show
from bokeh.models import HoverTool
from bokeh.plotting import figure
from functions import *
import getmac
import json
import socket

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
my_mac_adress = getmac.get_mac_address()
my_ipv4 = []
my_ipv6 = []
my_subnetwork = []
mac = {}
ipv4 = {i: [] for i in range(len(data["paquets"]))}
ipv6 = {i: [] for i in range(len(data["paquets"]))}
port = {i: [] for i in range(len(data["paquets"]))}
service = {i: [] for i in range(len(data["paquets"]))}
node_color = {i: "magenta" for i in range(len(data["paquets"]))}
# outline_color = {i: "black" for i in range(len(data["paquets"]))}
n_pkts = {}

# Create local network
graph_lan = nx.Graph()
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

        if src not in list_nodes_lan:
            list_nodes_lan.append(src)
        if dst not in list_nodes_lan:
            list_nodes_lan.append(dst)

        src_index = list_nodes_lan.index(src)
        dst_index = list_nodes_lan.index(dst)

        mac[src_index] = src
        mac[dst_index] = dst

        # Associate ipV6 adress to mac adress
        if ethertype == "ipV6":
            ipv6_src = packet["ip_src"]
            ipv6_dst = packet["ip_dst"]
            if ipv6_src not in ipv6[src_index]:
                ipv6[src_index].append(ipv6_src)
            if ipv6_dst not in ipv6[dst_index]:
                ipv6[dst_index].append(ipv6_dst)
        # Associate ipV4 adress to mac adress
        else:
            ipv4_src = packet["ip_src"]
            ipv4_dst = packet["ip_dst"]
            if ipv4_src not in ipv4[src_index]:
                ipv4[src_index].append(ipv4_src)
            if ipv4_dst not in ipv4[dst_index]:
                ipv4[dst_index].append(ipv4_dst)

        # Associate port to mac adress
        port_src = packet["port_src"]
        port_dst = packet["port_dst"]

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
                    if service_src == "http" or service_src == "https":
                        router = src_index
                        graph_lan.add_node(src_index, pos=(0, 12))
                if port_dst != ">1024" and port_dst is not None:
                    service_dst = socket.getservbyport(port_dst, proto)
                    if service_dst not in service[dst_index]:
                        service[dst_index].append(service_dst)
                    if service_dst == "http" or service_dst == "https":
                        router = dst_index
                        graph_lan.add_node(dst_index, pos=(12, 0))
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
        graph_lan.add_edge(src_index, dst_index)

# create wan
graph_wan = nx.Graph()
list_nodes_wan = []
ip_wan = {}

for ip in ipv4[router]:
    list_nodes_wan.append(ip)
    index = list_nodes_wan.index(ip)
    new_index = index + len(list_nodes_lan)
    graph_wan.add_edge(router, new_index)
    ip_wan[new_index] = ip

for ip in ipv6[router]:
    list_nodes_wan.append(ip)
    index = list_nodes_wan.index(ip)
    new_index = index + len(list_nodes_lan)
    graph_wan.add_edge(router, new_index)
    ip_wan[new_index] = ip

ipv4[router] = None
ipv6[router] = None
port[router] = None
service[router] = None


print("Adjusting layout...")
for node in graph_wan:
    node_color[node] = "orange"

for node in graph_lan:
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

nx.set_node_attributes(graph_lan, name="MAC", values=mac)
nx.set_node_attributes(graph_lan, name="IP_v4", values=ipv4)
nx.set_node_attributes(graph_lan, name="IP_v6", values=ipv6)
nx.set_node_attributes(graph_lan, name="node color", values=node_color)
# nx.set_node_attributes(graph_lan, name="outline color", values=outline_color)
nx.set_node_attributes(graph_lan, name="port", values=port)
nx.set_node_attributes(graph_lan, name="service", values=service)
nx.set_edge_attributes(graph_lan, name="n_pkts", values=n_pkts)
nx.set_node_attributes(graph_wan, name="IP", values=ip_wan)
nx.set_node_attributes(graph_wan, name="node color", values=node_color)


graph_renderer_lan = create_layout(graph_lan, router, (0, 0))
graph_renderer_wan = create_layout(graph_wan, router, (2.2, 0))

plot = figure(
    tools="pan,wheel_zoom,save,reset",
    active_scroll="wheel_zoom",
    x_range=(-1.2, 3.3),
    y_range=(-1.2, 1.2),
    height_policy="max",
    width_policy="max",
)

hover_nodes_lan = HoverTool(
    tooltips=[
        ("MAC", "@MAC"),
        ("IP v4", "@IP_v4"),
        ("IP v6", "@IP_v6"),
        ("Port", "@port"),
        ("service", "@service"),
    ],
    renderers=[graph_renderer_lan.node_renderer],
)

hover_edges_lan = HoverTool(
    tooltips=[("n pkts", "@n_pkts")],
    renderers=[graph_renderer_lan.edge_renderer],
)

hover_nodes_wan = HoverTool(
    tooltips=[("IP", "@IP")], renderers=[graph_renderer_wan.node_renderer]
)

plot.add_tools(hover_edges_lan, hover_nodes_lan, hover_nodes_wan)


set_style(graph_renderer_lan)
set_style(graph_renderer_wan)

plot.renderers.append(graph_renderer_lan)
plot.renderers.append(graph_renderer_wan)

show(plot)
end = time()
print("Done in", end - start, "s")
