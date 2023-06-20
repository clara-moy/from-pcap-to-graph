import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from bokeh.io import show
from bokeh.models import Range1d, Circle, MultiLine, NodesAndLinkedEdges
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
from time import time

print("Extracting data...")
start = time()
with open("data/json_data_3.json") as file:
    data = json.load(file)

print("Creating graph...")
list_nodes = []
list_edges = []
mac = {}
ip = {}
for index in range(len(data["paquets"])):
    ip[index] = []
port = {}
for index in range(len(data["paquets"])):
    port[index] = []
node_color = {}
for index in range(len(data["paquets"])):
    node_color[index] = "magenta"
graph = nx.Graph()
for packet in data["paquets"]:
    src = packet["src"]
    dst = packet["dst"]
    ip_src = packet["ip_src"]
    ip_dst = packet["ip_dst"]
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
    if port_src != None and port_src < 1024:
        node_color[src_index] = "cyan"
    if port_dst != None and port_dst < 1024:
        node_color[dst_index] = "cyan"
    if str(ip_src) not in ip[src_index]:
        ip[src_index].append(str(ip_src))
    if str(ip_dst) not in ip[dst_index]:
        ip[dst_index].append(str(ip_dst))
    graph.add_edge(src_index, dst_index)
    if str(port_src) not in port[src_index]:
        port[src_index].append(str(port_src))
    if str(port_dst) not in port[dst_index]:
        port[dst_index].append(str(port_dst))
    graph.add_edge(src_index, dst_index)
nx.set_node_attributes(graph, name="MAC", values=mac)
nx.set_node_attributes(graph, name="IP", values=ip)
nx.set_node_attributes(graph, name="node color", values=node_color)
nx.set_node_attributes(graph, name="port", values=port)


print("Adjusting layout...")
plot = figure(
    tooltips=[("MAC", "@MAC"), ("IP", "@IP"), ("Port", "@port")],
    tools="pan,wheel_zoom,save,reset",
    active_scroll="wheel_zoom",
    x_range=Range1d(-10.1, 10.1),
    y_range=Range1d(-10.1, 10.1),
)
network_graph = from_networkx(graph, nx.spring_layout, scale=10, center=(0, 0))
network_graph.node_renderer.glyph = Circle(size=8, fill_color="node color")
network_graph.node_renderer.hover_glyph = Circle(
    size=8, fill_color="white", line_width=2
)
network_graph.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
network_graph.edge_renderer.hover_glyph = MultiLine(line_color="black", line_width=2)
network_graph.inspection_policy = NodesAndLinkedEdges()
plot.renderers.append(network_graph)

show(plot)
end = time()
print("Done", end - start)
