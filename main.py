import json
import networkx as nx
from bokeh.io import show
from bokeh.models import (
    Circle,
    MultiLine,
    HoverTool,
)
from bokeh.plotting import figure, curdoc
from bokeh.plotting import from_networkx
from time import time
import socket

print("Extracting data...")
start = time()
with open("data/json_data_3.json") as file:
    data = json.load(file)
with open("numbers/ports.json") as file:
    ports_db = json.load(file)
with open("numbers/ip-protocol-numbers.json") as file:
    ip_protocols_db = json.load(file)

print("Creating graph...")

# Initialize variables
list_nodes = []
list_edges = []
mac = {}
ip = {i: [] for i in range(len(data["paquets"]))}
port = {i: [] for i in range(len(data["paquets"]))}
service = {i: [] for i in range(len(data["paquets"]))}
node_color = {i: "magenta" for i in range(len(data["paquets"]))}
n_pkts = {}
graph = nx.Graph()

for packet in data["paquets"]:
    src = packet["src"]
    dst = packet["dst"]

    if src not in list_nodes:
        list_nodes.append(src)
    if dst not in list_nodes:
        list_nodes.append(dst)

    src_index = list_nodes.index(src)
    dst_index = list_nodes.index(dst)

    mac[src_index] = src
    mac[dst_index] = dst

    ip_src = packet["ip_src"]
    ip_dst = packet["ip_dst"]
    if ip_src not in ip[src_index]:
        ip[src_index].append(ip_src)
    if ip_dst not in ip[dst_index]:
        ip[dst_index].append(ip_dst)

    port_src = packet["port_src"]
    port_dst = packet["port_dst"]

    if port_src != None and port_src > 1024:
        port_src = ">1024"
    if port_dst != None and port_dst > 1024:
        port_dst = ">1024"

    if port_src not in port[src_index]:
        port[src_index].append(port_src)
    if port_dst not in port[dst_index]:
        port[dst_index].append(port_dst)

    proto_number = packet["proto"]
    if proto_number != None:
        proto = ip_protocols_db[str(proto_number)]["keyword"].lower()
        try:
            if port_src != ">1024" and port_src != None:
                service_src = socket.getservbyport(port_src, proto)
                if service_src not in service[src_index]:
                    service[src_index].append(service_src)
            if port_dst != ">1024" and port_dst != None:
                service_dst = socket.getservbyport(port_dst, proto)
                if service_dst not in service[dst_index]:
                    service[dst_index].append(service_dst)
        except OSError:
            if (
                port_src != ">1024"
                and port_src != None
                and proto not in service[src_index]
            ):
                service[src_index].append(proto)
            elif (
                port_dst != ">1024"
                and port_dst != None
                and proto not in service[dst_index]
            ):
                service[dst_index].append(proto)

    if (src_index, dst_index) in n_pkts.keys():
        n_pkts[(src_index, dst_index)] += 1
    elif (dst_index, src_index) in n_pkts.keys():
        n_pkts[(dst_index, src_index)] += 1
    else:
        n_pkts[(src_index, dst_index)] = 1

    graph.add_edge(src_index, dst_index)

for node in graph:
    if "http" in service[node] or "https" in service[node]:
        node_color[node] = "green"
    elif port[node] == [None]:
        node_color[node] = "pink"
    elif ">1024" not in port[node]:
        node_color[node] = "blue"
    elif port[node] != [">1024"]:
        node_color[node] = "cyan"

nx.set_node_attributes(graph, name="MAC", values=mac)
nx.set_node_attributes(graph, name="IP", values=ip)
nx.set_node_attributes(graph, name="node color", values=node_color)
nx.set_node_attributes(graph, name="port", values=port)
nx.set_node_attributes(graph, name="service", values=service)
nx.set_edge_attributes(graph, name="n_pkts", values=n_pkts)

graph_renderer = from_networkx(graph, nx.spring_layout, scale=10, center=(0, 0))

print("Adjusting layout...")
plot = figure(
    tools="pan,wheel_zoom,save,reset",
    active_scroll="wheel_zoom",
    x_range=(-12, 12),
    y_range=(-12, 12),
)

hover_nodes = HoverTool(
    tooltips=[
        ("MAC", "@MAC"),
        ("IP", "@IP"),
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

plot.renderers.append(graph_renderer)
curdoc().add_root(plot)


graph_renderer.node_renderer.glyph = Circle(size=8, fill_color="node color")
graph_renderer.node_renderer.hover_glyph = Circle(
    size=8, fill_color="white", line_width=2
)
graph_renderer.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color="black", line_width=2)


plot.renderers.append(graph_renderer)

show(plot)
end = time()
print("Done", end - start)
