"""Takes a .json file with log data and plots a graph representing the topology of the network
Usage:
=====
    python3 main.py file_name.json save_file_name

    file_name: name of the file (with the relative path) from which we want data
    save_file_name: name of the file where data are saved
"""

__authors__ = "Clara Moy"
__contact__ = "c.m0y@yahoo.com"
__copyright__ = "MIT"
__date__ = "2023-06-26"

import math
import sys
from time import time

import json
import matplotlib.pyplot as plt
from modified_netgraph import NewInteractiveGraph
import networkx as nx
import numpy as np
import pandas as pd
import pickle
from zoom import ZoomPan

__authors__ = "Clara Moy"
__contact__ = "c.m0y@yahoo.com"
__copyright__ = "MIT"
__date__ = "2023-06-26"


np.seterr(divide="ignore", invalid="ignore")

start = time()
list_nodes = []
prefix_to_router_index = {}
subnetworks = {0: []}
mac = {}
ipv4 = {}
ports = {}
table = {}
mapping = {}

router = 0
mac[router] = []


def load_json(file_name):
    """Load data from a /json file

    Parameters
    ----------
    file_name : str
        name of the .json file

    Returns
    -------
    dict
        data from the .json file sored in a dictionnary
    """
    with open(file_name) as file:
        return json.load(file)


def find_router(data, mac, list_nodes, router):
    """Find the router

    Parameters
    ----------
    data : dict
        data about the packets
    mac : dict
        dict containing the mac adresses of the nodes associated to their index in list_nodes
    list_nodes : list
        list of the identifiers of the nodes (MAC or IP adresses)
    router : int
        index of the router in list_nodes

    Raises
    ------
    NotImplementedError
        if the router is not found
    """
    print("Finding router...")
    router_ip = find_http_communication(data, mac, router)
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
        raise NotImplementedError("Failed to find router")
    else:
        list_nodes.append(mac[router][0])


def find_http_communication(data, mac, router):
    """Find if the packet contains a http communication

    Parameters
    ----------
    data : dict
        data about the packets
    mac : dict
        dict containing the mac adresses of the nodes associated to their index in list_nodes
    router : int
        index of the router in list_nodes

    Returns
    -------
    list
        list of the ip adresses with http or https communications linked with the router
    """
    router_proto = []
    router_ip = []
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
    return router_ip


def process_data(
    packet,
    src_or_dst,
    list_nodes,
    mac,
    ethertype,
    ipv4,
    port,
    prefix_to_router_index,
    subnetworks,
):
    """_summary_

    Parameters
    ----------
    packet : dict
        contain all data from the packet necessary to the program
    src_or_dst : srt
        "src" if working on the sender of the packet, "dst" if working on the reciever of the packet
    list_nodes : list
        contain all nodes. Allows to attribute an index to a node.
    mac : dict
        contain all already seen mac adresses associated to their index in list_nodes
    ethertype : str
        represent the ethertype of the packet (ex : "ipV4")
    ipv4 : dict
        contain all ipV4 adresses associated with their index in list_nodes
    list_subnetworks : list
        contain all subnetworks prefixes already seen. Allows to attribute an index to a subnetwork.
    subnetwork : dict
        contain all subnetworks indexes in list_subnetworks associated with their index in list_nodes
    port : dict
        contain all ports used by devices associated with their index in list_nodes
    prefix_to_router_index : dict
        associate network prefix to the index of ther router of the network
    subnetworks : list of lists
        list of list of nodes grouped by subnetwork

    Returns
    -------
    int
        index of the mac adress of the device in list_nodes
    int
        index of the node identifier in list_nodes (if it's in the local network: index of the mac adress, else: index of the ip adress)
    int
        index of the network in subnetworks
    str
        name of the processus used
    """
    device = packet[src_or_dst]
    if device not in list_nodes:
        list_nodes.append(device)
    index = list_nodes.index(device)
    mac[index] = device
    ipv4[index] = [None]
    if ethertype != "ipV6":
        ipv4_device = packet["ip_" + src_or_dst]
        if index in ipv4.keys():
            if ipv4_device not in ipv4[index]:
                ipv4[index].append(ipv4_device)
        else:
            ipv4[index] = [ipv4_device]
    port_device = packet["port_" + src_or_dst]
    if port_device is not None and port_device > 1024:
        port_device = ">1024"
    if index in port.keys():
        if port_device not in port[index]:
            port[index].append(port_device)
    else:
        port[index] = [port_device]
    if index == 0:
        if ipv4_device not in list_nodes:
            list_nodes.append(ipv4_device)
        new_index = list_nodes.index(ipv4_device)
        ipv4[new_index] = ipv4_device
        parsed_ip = ipv4_device.split(".")
        if parsed_ip[0] in [str(i) for i in range(1, 128)]:
            prefix = parsed_ip[0]
        elif parsed_ip[0] in [str(i) for i in range(128, 192)]:
            prefix = parsed_ip[0] + "." + parsed_ip[1]
        elif parsed_ip[0] in [str(i) for i in range(192, 224)]:
            prefix = parsed_ip[0] + "." + parsed_ip[1] + "." + parsed_ip[2]
        if prefix not in prefix_to_router_index.keys():
            list_nodes.append(prefix)
            ntwk_index = list_nodes.index(prefix)
            subnetworks[ntwk_index] = []
        ntwk_index = list_nodes.index(prefix)
        ipv4[ntwk_index] = prefix
        prefix_to_router_index[prefix] = ntwk_index
        if new_index not in subnetworks[ntwk_index]:
            subnetworks[ntwk_index].append(new_index)
        return index, new_index, ntwk_index, port_device
    else:
        if index not in subnetworks[0]:
            subnetworks[0].append(index)
        return index, index, 0, port_device


def update_table(table, list_nodes, src_index, port_src, dst_index, port_dst):
    """Update table

    Parameters
    ----------
    table : dict
        index in list_nodes linked to the info wanted in the table
    list_nodes : list
        list of the identifiers of the nodes (MAC or IP adresses)
    src_index : int
        index in list_nodes of the source of the packet
    port_src : int or str
        port of the source of the packet
    dst_index : int
        index in list_nodes of the destination of the packet
    port_dst : int or str
        port of the destination of the packet
    """
    if src_index not in table.keys():
        table[src_index] = {
            "distance": [],
            "port src": [],
            "port dst": [],
            "device dst": [],
        }
    if (
        port_src is not None
        and port_src not in table[src_index]["port src"]
        and port_dst not in table[src_index]["port dst"]
        and list_nodes[dst_index] not in table[src_index]["device dst"]
    ):
        table[src_index]["distance"].append("")
        table[src_index]["port src"].append(port_src)
        table[src_index]["port dst"].append(port_dst)
        table[src_index]["device dst"].append(list_nodes[dst_index])


def update_mapping(
    device_1_index,
    device_1_ntwk_index,
    device_1_dist_index,
    device_2_index,
    graph,
    mapping,
):
    """Update mapping with path from device_1 to device_2

    Parameters
    ----------
    device_1_index : int
        index of the mac adress of the device (device_1) in list_nodes (if device_1 is beyond the router, index of the router of the local network)
    device_1_ntwk_index : int
        index of the network of device_1 in subnetworks
    device_1_dist_index : int
        index of the node identifier of device_1 in list_nodes (if it's in the local network: index of the mac adress, else: index of the ip adress)
    device_2_index : int
        index of the mac adress of the device (device_2) in list_nodes
    graph : networkx.Graph
        The graph that wee want to map
    mapping : dict
        contains mapping data linked to the index of the node
    """
    if device_1_index in mapping.keys():
        if device_1_index not in mapping[device_1_index]:
            mapping[device_1_index] = [
                device_1_index,
                device_2_index,
                (device_1_index, device_2_index),
                (device_2_index, device_1_index),
            ]
        elif device_2_index not in mapping[device_1_index]:
            mapping[device_1_index] += [
                device_2_index,
                (device_1_index, device_2_index),
                (device_2_index, device_1_index),
            ]
    else:
        mapping[device_1_index] = [
            device_1_index,
            device_2_index,
            (device_1_index, device_2_index),
            (device_2_index, device_1_index),
        ]
    graph.add_edge(device_1_index, device_2_index)
    if device_1_index == 0:
        graph.add_edge(device_1_dist_index, device_1_ntwk_index)
        graph.add_edge(device_1_ntwk_index, device_1_index)
        update_mapping_wan(
            device_1_dist_index,
            device_1_ntwk_index,
            device_2_index,
            device_1_index,
            mapping,
        )
        update_mapping_wan(
            device_2_index,
            device_1_index,
            device_1_dist_index,
            device_1_ntwk_index,
            mapping,
        )


def update_mapping_wan(
    device_1_index, router_1_index, device_2_index, router_2_index, mapping
):
    """Update mapping for devices beyond the router

    Parameters
    ----------
    device_1_index : int
        index of device_1 in list_nodes
    router_1_index : int
        index of the first router linked with device_1
    device_2_index : int
        index of device_2 in list_nodes
    router_2_index : int
        index of the first router linked with device_2
    mapping : dict
        contains mapping data linked to the index of the node
    """
    if device_1_index in mapping.keys():
        if device_1_index not in mapping[device_1_index]:
            mapping[device_1_index] = [
                router_1_index,
                device_1_index,
                router_2_index,
                device_2_index,
                (router_1_index, router_2_index),
                (device_1_index, router_1_index),
                (device_2_index, router_2_index),
                (router_2_index, router_1_index),
                (router_1_index, device_1_index),
                (router_2_index, device_2_index),
            ]
        elif device_2_index not in mapping[device_1_index]:
            mapping[device_1_index] += [
                device_2_index,
                (router_2_index, device_2_index),
                (device_2_index, router_2_index),
            ]
            if (router_1_index, router_2_index) not in mapping[device_1_index]:
                mapping[device_1_index] += [
                    router_2_index,
                    (router_1_index, router_2_index),
                    (router_2_index, router_1_index),
                ]
    else:
        mapping[device_1_index] = [
            router_2_index,
            device_2_index,
            router_1_index,
            device_1_index,
            (router_1_index, router_2_index),
            (device_1_index, router_1_index),
            (device_2_index, router_2_index),
            (router_2_index, router_1_index),
            (router_1_index, device_1_index),
            (router_2_index, device_2_index),
        ]


def set_colors(graph, subnetworks):
    """Set nodes colors

    Parameters
    ----------
    graph : networkx.Graph
        graph
    subnetworks : dict
        index of the subnetwork associated to all devices in the subnetwork

    Returns
    -------
    dict
        index of the nodes in list_nodes linked to their color in the graph
    """
    node_color = {}
    for node in graph:
        if node in subnetworks.keys():
            node_color[node] = "green"
        elif node in subnetworks[0]:
            node_color[node] = "cyan"
        else:
            node_color[node] = "orange"
    return node_color


def set_layout(subnetworks, scale=1):
    """Set layout for the graph

    Parameters
    ----------
    subnetworks : dict
        index of the subnetwork associated to all devices in the subnetwork
    scale : float, optional
        scale of the graph (allows to change nodes size), by default 1

    Returns
    -------
    dict
        index of the nodes in list_nodes linked to their position in the graph
    """
    layout = {}
    i = 0
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
    return layout


def set_annotations(list_nodes, mac, ipv4):
    """Set annotation for hover

    Parameters
    ----------
    list_nodes : list
        list of the identifiers of the nodes (MAC or IP adresses)
    mac : dict
        dict containing the mac adresses of the nodes associated to their index in list_nodes
    ipv4 : dict
        dict containing the ip adresses of the nodes associated to their index in list_nodes

    Returns
    -------
    dict
        index of the nodes in list_nodes linked to their annotation in the graph
    """
    annotations = {}
    for i in range(len(list_nodes)):
        if i in mac.keys():
            annotations[i] = "MAC : " + str(mac[i]) + "\nIP : "
        else:
            annotations[i] = "MAC : None\nIP : "
        if ipv4[i] is not None:
            for ip in ipv4[i]:
                if ip is not None:
                    annotations[i] += str(ip)
    return annotations


def change_table_type(table):
    """Transforms each element of the table in pandas.DataFrame (needed to plot the graph)

    Parameters
    ----------
    table : dict
        index in list_nodes linked to the info wanted in the table
    """
    for index in table.keys():
        table[index] = pd.DataFrame(table[index])


def save_data(
    node_color,
    graph,
    layout,
    table,
    mapping,
    annotations,
    edge_width=0.6,
    edge_color="black",
):
    """Save data in a .json file

    Parameters
    ----------
    node_color : dict
        index of the nodes in list_nodes linked to their color in the graph
    graph : networkx.Graph
        graph
    layout : dict
        index of the nodes in list_nodes linked to their position in the graph
    table : dict
        index in list_nodes linked to the info wanted in the table
    mapping : dict
        contains mapping data linked to the index of the node
    annotations : dict
        index of the nodes in list_nodes linked to their annotation in the graph
    edge_width : float, optional
        width of the edges in the graph, by default 0.6
    edge_color : str, optional
        color of the edges in the graph, by default "black"
    """
    with open(sys.argv[2] + ".fig.pckl", "wb") as file:
        pickle.dump(
            {
                "node_color": node_color,
                "graph": graph,
                "layout": layout,
                "edge_width": edge_width,
                "edge_color": edge_color,
                "table": table,
                "mapping": mapping,
                "annotations": annotations,
            },
            file,
        )


def plot_graph(
    node_color,
    graph,
    layout,
    table,
    mapping,
    annotations,
    edge_width=0.6,
    edge_color="black",
):
    """Plot the graph

    Parameters
    ----------
    node_color : dict
        index of the nodes in list_nodes linked to their color in the graph
    graph : networkx.Graph
        graph
    layout : dict
        index of the nodes in list_nodes linked to their position in the graph
    table : dict
        index in list_nodes linked to the info wanted in the table
    mapping : dict
        contains mapping data linked to the index of the node
    annotations : dict
        index of the nodes in list_nodes linked to their annotation in the graph
    edge_width : float, optional
        width of the edges in the graph, by default 0.6
    edge_color : str, optional
        color of the edges in the graph, by default "black"

    Returns
    -------
    modified_netgraph.NewInteractiveGraph
        figure to plot
    matplotlib.axes._axes.Axes
        axes
    """
    fig, ax = plt.subplots()

    fig = NewInteractiveGraph(
        graph,
        node_layout=layout,
        node_color=node_color,
        edge_width=edge_width,
        edge_color=edge_color,
        tables=table,
        annotations=annotations,
        mapping=mapping,
    )

    scale = 1.1
    zp = ZoomPan()
    figZoom = zp.zoom_factory(ax, base_scale=scale)
    figPan = zp.pan_factory(ax)
    print(type(fig), type(ax), type((fig, ax)))
    return fig, ax


if __name__ == "__main__":
    print("Extracting data...")

    data = load_json(sys.argv[1])
    ip_protocols_data = load_json("numbers/ip-protocol-numbers.json")
    ethertypes_data = load_json("numbers/ethertypes.json")
    ports_data = load_json("numbers/ports.json")

    find_router(data, mac, list_nodes, router)

    print("Creating graph...")

    graph = nx.Graph()
    for packet in data["paquets"]:
        try:
            ethertype = ethertypes_data[str(packet["type"])]
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
            src_index, src_dist_index, src_ntwk_index, port_src = process_data(
                packet,
                "src",
                list_nodes,
                mac,
                ethertype,
                ipv4,
                ports,
                prefix_to_router_index,
                subnetworks,
            )
            dst_index, dst_dist_index, dst_ntwk_index, port_dst = process_data(
                packet,
                "dst",
                list_nodes,
                mac,
                ethertype,
                ipv4,
                ports,
                prefix_to_router_index,
                subnetworks,
            )
            update_table(
                table, list_nodes, src_dist_index, port_src, dst_dist_index, port_dst
            )
            update_mapping(
                src_index, src_ntwk_index, src_dist_index, dst_index, graph, mapping
            )
            update_mapping(
                dst_index, dst_ntwk_index, dst_dist_index, src_index, graph, mapping
            )

    ipv4[router] = None
    ports[router] = None

    print("Adjusting layout...")

    node_color = set_colors(graph, subnetworks)
    layout = set_layout(subnetworks)
    annotations = set_annotations(list_nodes, mac, ipv4)
    change_table_type(table)
    save_data(node_color, graph, layout, table, mapping, annotations)
    fig, ax = plot_graph(node_color, graph, layout, table, mapping, annotations)

    end = time()
    print("Done in", end - start, "s")
    plt.show()
