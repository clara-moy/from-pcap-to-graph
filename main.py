import json
import networkx as nx
import numpy as np
from bokeh.io import show
import getmac
from bokeh.models import Circle, MultiLine, HoverTool, StaticLayoutProvider
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
from time import time
import socket
from bokeh.resources import CDN
from bokeh.embed import file_html
from IPython.display import display, HTML

print("Extracting data...")
start = time()
with open("data/json_data_Friday.json") as file:
    data = json.load(file)
with open("numbers/ports.json") as file:
    ports_db = json.load(file)
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
graph_lan = nx.Graph()

for packet in data["paquets"]:
    try:
        ethertype = ethertypes[str(packet["type"])]
    except (KeyError, TypeError):
        ethertype = "unknown"
    if (
        packet["ip_src"] != None
        and packet["ip_dst"] != None
        and packet["ip_src"][:4] != "ff02"
        and packet["ip_dst"][:4] != "ff02"
    ):
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

        if ethertype == "ipV6":
            ipv6_src = packet["ip_src"]
            ipv6_dst = packet["ip_dst"]
            if ipv6_src not in ipv6[src_index]:
                ipv6[src_index].append(ipv6_src)
            if ipv6_dst not in ipv6[dst_index]:
                ipv6[dst_index].append(ipv6_dst)
        else:
            ipv4_src = packet["ip_src"]
            ipv4_dst = packet["ip_dst"]
            if ipv4_src not in ipv4[src_index]:
                ipv4[src_index].append(ipv4_src)
            if ipv4_dst not in ipv4[dst_index]:
                ipv4[dst_index].append(ipv4_dst)

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
                    if service_src == "http" or service_src == "https":
                        router = src_index
                        graph_lan.add_node(src_index, pos=(0, 12))
                if port_dst != ">1024" and port_dst != None:
                    service_dst = socket.getservbyport(port_dst, proto)
                    if service_dst not in service[dst_index]:
                        service[dst_index].append(service_dst)
                    if service_dst == "http" or service_dst == "https":
                        router = dst_index
                        graph_lan.add_node(dst_index, pos=(12, 0))
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
        graph_lan.add_edge(src_index, dst_index)

graph_wan = nx.Graph()
list_nodes_wan = []
ip_wan = {}
for ip in ipv4[router]:
    list_nodes_wan.append(ip)
    index = list_nodes_wan.index(ip)
    new_index = index + len(list_nodes_lan)
    graph_wan.add_edge(router, new_index)
    ip_wan[new_index] = ip

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

fixed_layout = nx.spring_layout(graph_lan)
fixed_layout[router] = np.array([1.1, 0])
fixed_layout_provider = StaticLayoutProvider(graph_layout=fixed_layout)

graph_renderer = from_networkx(graph_lan, nx.spring_layout, center=(0, 0))
graph_renderer.layout_provider = fixed_layout_provider

fixed_layout_2 = nx.spring_layout(graph_wan, center=(2.2, 0))
fixed_layout_2[router] = (1.1, 0)
fixed_layout_provider_2 = StaticLayoutProvider(graph_layout=fixed_layout_2)

graph_renderer_2 = from_networkx(graph_wan, nx.spring_layout)
graph_renderer_2.layout_provider = fixed_layout_provider_2

print("Adjusting layout...")
plot = figure(
    tools="pan,wheel_zoom,save,reset",
    active_scroll="wheel_zoom",
    x_range=(-1.2, 3.3),
    y_range=(-1.2, 1.2),
    aspect_ratio=2,
    height_policy="max",
)

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

hover_servers = HoverTool(
    tooltips=[("IP", "@IP")], renderers=[graph_renderer_2.node_renderer]
)


plot.add_tools(hover_edges, hover_nodes, hover_servers)


graph_renderer.node_renderer.glyph = Circle(
    size=8, fill_color="node color"  # , line_color="outline color"
)
graph_renderer.node_renderer.hover_glyph = Circle(
    size=8, fill_color="white", line_width=2
)
graph_renderer.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color="black", line_width=2)


graph_renderer_2.node_renderer.glyph = Circle(
    size=8, fill_color="node color"  # , line_color="outline color"
)
graph_renderer_2.node_renderer.hover_glyph = Circle(
    size=8, fill_color="white", line_width=2
)
graph_renderer_2.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
graph_renderer_2.edge_renderer.hover_glyph = MultiLine(line_color="black", line_width=2)

plot.renderers.append(graph_renderer)
plot.renderers.append(graph_renderer_2)

html = file_html(plot, CDN, theme="dark_minimal")
HTML("<center>{}</center>".format(html))

show(plot)
end = time()
print("Done in", end - start, "s")
