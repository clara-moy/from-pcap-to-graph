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
from bokeh.models import StaticLayoutProvider
from bokeh.plotting import from_networkx
from bokeh.models import Circle, MultiLine


def create_layout(graph: nx.Graph, router_index: int, center: tuple):
    """This function sets up the layout that places the router in (1.1, 0)

    Parameters
    ----------
    graph : nx.Graph
        The graph that we want to plot
    router_index : int
        The index of the router in the dictionnary of nodes
    center : _type_
        the place of the center of the plot

    Returns
    -------
    bokeh.models.renderers.graph_renderer.GraphRenderer
        The graph renderer for the graph
    """
    # move router to (1.1, 0)
    fixed_layout = nx.spring_layout(graph, center=center)
    fixed_layout[router_index] = (1.1, 0)
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
