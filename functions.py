"""Program that groups all the functions used in the files main_vx.py (with $x \in \mathbb N$)

Usage:
=====
    Not used directly
"""

__authors__ = "Clara Moy"
__contact__ = "c.m0y@yahoo.com"
__copyright__ = "MIT"
__date__ = "2023-06-26"


import networkx as nx
from bokeh.models import StaticLayoutProvider, NodesAndLinkedEdges
from bokeh.plotting import from_networkx
from bokeh.models import Circle, MultiLine


def create_layout(
    graph: nx.Graph, router_index: int, center: tuple, scale: float, other_router=False
):
    """This function sets up the layout that places the router in (1.1, 0)

    Parameters
    ----------
    graph : nx.Graph
        The graph that we want to plot
    router_index : int
        The index of the router in the dictionnary of nodes
    center : tuple
        the place of the center of the plot
    scale : float
        the scale of the graph

    Returns
    -------
    bokeh.models.renderers.graph_renderer.GraphRenderer
        The graph renderer for the graph
    """
    # move router to (1.1, 0)
    fixed_layout = nx.circular_layout(graph, center=center, scale=scale)
    fixed_layout[router_index] = (1.1, 0)
    if other_router != False:
        fixed_layout[other_router] = center
    fixed_layout_provider = StaticLayoutProvider(graph_layout=fixed_layout)
    # create renderer
    graph_renderer = from_networkx(graph, nx.spring_layout)
    # choose layout
    graph_renderer.layout_provider = fixed_layout_provider
    return graph_renderer


def set_style(graph_renderer):
    """This function sets a style for the graph renderer. It chooses the color of the edges and nodes and describses their behaviour when hovered

    Parameters
    ----------
    graph_renderer : bokeh.models.renderers.graph_renderer.GraphRenderer
        graph renderer with the layout of the graph we want to plot

    Returns
    -------
    None
    """
    graph_renderer.node_renderer.glyph = Circle(
        size=8,
        fill_color="node color",  # If outline parameters are used: , line_color="outline color"
    )
    graph_renderer.node_renderer.hover_glyph = Circle(
        size=8, fill_color="white", line_width=2
    )

    graph_renderer.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(
        line_color="black", line_width=2
    )
    graph_renderer.inspection_policy = NodesAndLinkedEdges()


def data_processing(
    packet,
    src_or_dst,
    list_nodes,
    mac,
    ethertype,
    ipv6,
    ipv4,
    port,
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
    ipv6 : dict
        contain all ipV6 adresses associated with their index in list_nodes
    ipv4 : dict
        contain all ipV4 adresses associated with their index in list_nodes
    list_subnetworks : list
        contain all subnetworks prefixes already seen. Allows to attribute an index to a subnetwork.
    subnetwork : dict
        contain all subnetworks indexes in list_subnetworks associated with their index in list_nodes
    port : dict
        contain all ports used by devices associated with their index in list_nodes

    Returns
    -------
    _type_
        _description_
    """
    device = packet[src_or_dst]
    if device not in list_nodes:
        list_nodes.append(device)
    index = list_nodes.index(device)
    mac[index] = device
    if ethertype == "ipV6":
        ipv6_device = packet["ip_" + src_or_dst]
        if index in ipv6.keys():
            if ipv6_device not in ipv6[index]:
                ipv6[index].append(ipv6_device)
        else:
            ipv6[index] = [ipv6_device]
    else:
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
    return index, port_device
