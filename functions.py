import networkx as nx
from bokeh.models import StaticLayoutProvider
from bokeh.plotting import from_networkx
from bokeh.models import Circle, MultiLine


def create_layout(graph, router, center):
    # move router to (1.1, 0)
    fixed_layout = nx.spring_layout(graph, center=center)
    fixed_layout[router] = (1.1, 0)
    fixed_layout_provider = StaticLayoutProvider(graph_layout=fixed_layout)
    # create renderer
    graph_renderer = from_networkx(graph, nx.spring_layout)
    # choose layout
    graph_renderer.layout_provider = fixed_layout_provider
    return graph_renderer

def set_style(graph_renderer):
    graph_renderer.node_renderer.glyph = Circle(
        size=8, fill_color="node color"  # , line_color="outline color"
    )
    graph_renderer.node_renderer.hover_glyph = Circle(
        size=8, fill_color="white", line_width=2
    )
    graph_renderer.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(
        line_color="black", line_width=2
    )
