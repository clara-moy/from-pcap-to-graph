"""
Modifid netgraph that allows new features such as EmphasizeOnClick and TableOnHover
"""

from netgraph._main import (
    Graph,
    DraggableGraphWithGridMode,
    AnnotateOnClickGraph,
    AnnotateOnClick,
)
import matplotlib as plt


class EmphasizeOnClick(object):
    """Emphasize matplotlib artists when clicking on them by desaturating all other artists."""

    def __init__(self, artist_to_mapping):
        self.artist_to_mapping = artist_to_mapping
        self.emphasizeable_artists = self.artist_to_mapping.keys()
        self.artists = list(self.node_artists.values()) + list(
            self.edge_artists.values()
        )
        keys = list(self.node_artists.keys()) + list(self.edge_artists.keys())
        self.artist_to_key = dict(zip(self.artists, keys))
        self.mapping = None
        self._base_alpha = {artist: artist.get_alpha() for artist in self.artists}
        self.deemphasized_artists = []

        try:
            (self.fig,) = set(list(artist.figure for artist in self.artists))
        except ValueError:
            raise Exception("All artists have to be on the same figure!")

        try:
            (self.ax,) = set(list(artist.axes for artist in self.artists))
        except ValueError:
            raise Exception("All artists have to be on the same axis!")

        self.fig.canvas.mpl_connect("button_release_event", self._on_release)

    def _add_mapping(self, selected_artist):
        self.mapping = self.artist_to_mapping[selected_artist]
        emphasized_artists = []
        for value in self.mapping:
            if value in self.node_artists:
                emphasized_artists.append(self.node_artists[value])
            elif value in self.edge_artists:
                emphasized_artists.append(self.edge_artists[value])
        for artist in self.artists:
            if artist not in emphasized_artists:
                artist.set_alpha(self._base_alpha[artist] / 5)
                self.deemphasized_artists.append(artist)

    def _remove_mapping(self):
        for artist in self.deemphasized_artists:
            artist.set_alpha(self._base_alpha[artist])
        self.deemphasized_artists = []
        self.mapping = None

    def _on_release(self, event):
        if event.inaxes == self.ax:
            for artist in self.emphasizeable_artists:
                if artist.contains(event)[0]:
                    if self.mapping:
                        self._remove_mapping()
                    else:
                        self._add_mapping(artist)
                    self.fig.canvas.draw()
                    break
            else:
                if self.mapping:
                    self._remove_mapping()
                    self.fig.canvas.draw()


class EmphasizeOnClickGraph(Graph, EmphasizeOnClick):
    """Combines `EmphasizeOnClick` with the `Graph` class such that nodes are emphasized when clicking on them with the mouse.

    Parameters
    ----------
    graph : various formats
        Graph object to plot. Various input formats are supported.
        In order of precedence:

        - Edge list:
          Iterable of (source, target) or (source, target, weight) tuples,
          or equivalent (E, 2) or (E, 3) ndarray, where E is the number of edges.
        - Adjacency matrix:
          Full-rank (V, V) ndarray, where V is the number of nodes/vertices.
          The absence of a connection is indicated by a zero.

          .. note:: If V <= 3, any (2, 2) or (3, 3) matrices will be interpreted as edge lists.**

        - networkx.Graph, igraph.Graph, or graph_tool.Graph object

    mouseover_highlight_mapping : dict or None, default None
        Determines which nodes and/or edges are highlighted when hovering over any given node or edge.
        The keys of the dictionary are node and/or edge IDs, while the values are iterables of node and/or edge IDs.
        If the parameter is None, a default dictionary is constructed, which maps

        - edges to themselves as well as their source and target nodes, and
        - nodes to themselves as well as their immediate neighbours and any edges between them.

    *args, **kwargs
        Parameters passed through to `Graph`. See its documentation for a full list of available arguments.

    Attributes
    ----------
    node_artists : dict
        Mapping of node IDs to matplotlib PathPatch artists.
    edge_artists : dict
        Mapping of edge IDs to matplotlib PathPatch artists.
    node_label_artists : dict
        Mapping of node IDs to matplotlib text objects (if applicable).
    edge_label_artists : dict
        Mapping of edge IDs to matplotlib text objects (if applicable).
    node_positions : dict node : (x, y) tuple
        Mapping of node IDs to node positions.

    See also
    --------
    Graph

    """

    def __init__(self, graph, mouseover_highlight_mapping=None, *args, **kwargs):
        Graph.__init__(self, graph, *args, **kwargs)

        artists = list(self.node_artists.values()) + list(self.edge_artists.values())
        keys = list(self.node_artists.keys()) + list(self.edge_artists.keys())
        self.artist_to_key = dict(zip(artists, keys))
        EmphasizeOnClick.__init__(self, mouseover_highlight_mapping)
        self.mouseover_highlight_mapping = mouseover_highlight_mapping


class TableOnHover(object):
    """Show or hide tabular information when hovering over matplotlib artists."""

    def __init__(self, artist_to_table, table_kwargs=None):
        self.artist_to_table = artist_to_table
        self.artists = list(self.node_artists.values()) + list(
            self.edge_artists.values()
        )
        self.table = None
        self.table_fontsize = None
        self.table_kwargs = dict(
            # bbox = [1.1, 0.1, 0.5, 0.8],
            # edges = 'horizontal',
        )

        if table_kwargs:
            if "fontsize" in table_kwargs:
                self.table_fontsize = table_kwargs["fontsize"]
            self.table_kwargs.update(table_kwargs)

        try:
            (self.fig,) = set(list(artist.figure for artist in artist_to_table))
        except ValueError:
            raise Exception("All artists have to be on the same figure!")

        try:
            (self.ax,) = set(list(artist.axes for artist in artist_to_table))
        except ValueError:
            raise Exception("All artists have to be on the same axis!")

        self.fig.canvas.mpl_connect("motion_notify_event", self._on_motion)
        if self.table:
            self.table.remove()
        self.table = None

    def _on_motion(self, event):
        if event.inaxes == self.ax:
            # on artist
            selected_artist = None
            for artist in self.artists:
                if artist.contains(event)[0]:  # returns two arguments for some reason
                    selected_artist = artist
                    break

            if selected_artist:
                try:
                    df = self.artist_to_table[selected_artist]
                except KeyError:
                    return
                if not df.empty:
                    self.table = self.ax.table(
                        cellText=df.values.tolist(),
                        rowLabels=df.index.values,
                        colLabels=df.columns.values,
                        **self.table_kwargs,
                    )
                    self.fig.canvas.draw_idle()

            # not on any artist
            if selected_artist is None:
                if self.table:
                    for children in self.ax.get_children():
                        if type(children) == plt.table.Table:
                            children.remove()
                self.table = None
                self.fig.canvas.draw_idle()


class TableOnHoverGraph(Graph, TableOnHover):
    """Combines `TableOnHover` with the `Graph` class such that nodes or edges can have toggleable tabular annotations."""

    def __init__(self, *args, **kwargs):
        Graph.__init__(self, *args, **kwargs)

        self.artist_to_table = dict()
        if "tables" in kwargs:
            for key, table in kwargs["tables"].items():
                if key in self.nodes:
                    self.artist_to_table[self.node_artists[key]] = table
                elif key in self.edges:
                    self.artist_to_table[self.edge_artists[key]] = table
                else:
                    raise ValueError(
                        f"There is no node or edge with the ID {key} for the table '{table}'."
                    )

        if "table_kwargs" in kwargs:
            TableOnHover.__init__(self, self.artist_to_table, kwargs["table_kwargs"])
        else:
            TableOnHover.__init__(self, self.artist_to_table)


class AnnotateOnHover(object):
    """Show or hide annotations when hovering on matplotlib artists."""

    def __init__(self, artist_to_annotation, annotation_fontdict=None):
        self.artists = list(self.node_artists.values()) + list(
            self.edge_artists.values()
        )
        self.artist_to_annotation = artist_to_annotation
        self.annotated_artists = set()
        self.artist_to_text_object = dict()
        self.annotation_fontdict = dict(backgroundcolor="white", clip_on=False)
        if annotation_fontdict:
            self.annotation_fontdict.update(annotation_fontdict)

        self.fig.canvas.mpl_connect("motion_notify_event", self._on_motion)

    def _on_motion(self, event):
        if event.inaxes == self.ax:
            # on artist
            selected_artist = None
            for artist in self.artists:
                if artist.contains(event)[0]:  # returns two arguments for some reason
                    selected_artist = artist
                    break

            if selected_artist:
                params = self.annotation_fontdict.copy()
                try:
                    if isinstance(self.artist_to_annotation[selected_artist], str):
                        self.artist_to_text_object[selected_artist] = self.ax.text(
                            -2,
                            0,
                            self.artist_to_annotation[selected_artist],
                            **params,
                        )
                    elif isinstance(self.artist_to_annotation[selected_artist], dict):
                        params.update(self.artist_to_annotation[selected_artist].copy())
                        self.artist_to_text_object[selected_artist] = self.ax.text(
                            -2, 0, **params
                        )
                    self.fig.canvas.draw_idle()
                except KeyError:
                    return

            # not on any artist
            if selected_artist is None:
                if self.artist_to_text_object != {}:
                    for children in self.ax.get_children():
                        if (
                            type(children) == plt.text.Text
                            and str(children)[:10] == "Text(-2, 0"
                        ):
                            children.remove()
                self.fig.canvas.draw_idle()


class AnnotateOnHoverGraph(Graph, AnnotateOnHover):
    """Combines `AnnotateOnHover` with the `Graph` class such that nodes or edges can have toggleable annotations."""

    def __init__(self, *args, **kwargs):
        Graph.__init__(self, *args, **kwargs)

        artist_to_annotation = dict()
        if "annotations" in kwargs:
            for key, annotation in kwargs["annotations"].items():
                if key in self.nodes:
                    artist_to_annotation[self.node_artists[key]] = annotation
                elif key in self.edges:
                    artist_to_annotation[self.edge_artists[key]] = annotation
                else:
                    raise ValueError(
                        f"There is no node or edge with the ID {key} for the annotation '{annotation}'."
                    )

        AnnotateOnHover.__init__(self, artist_to_annotation)


class NewInteractiveGraph(
    EmphasizeOnClickGraph,
    TableOnHoverGraph,
    DraggableGraphWithGridMode,
    AnnotateOnHoverGraph,
):
    def __init__(self, *args, **kwargs):
        DraggableGraphWithGridMode.__init__(self, *args, **kwargs)
        artists = list(self.node_artists.values()) + list(self.edge_artists.values())
        keys = list(self.node_artists.keys()) + list(self.edge_artists.keys())
        self.artist_to_key = dict(zip(artists, keys))
        self._base_facecolor = dict(
            [(artist, artist.get_facecolor()) for artist in self._selectable_artists]
        )

        artist_to_annotation = dict()
        if "annotations" in kwargs:
            for key, annotation in kwargs["annotations"].items():
                # Test membership of edges first, as edge keys may
                # result in a ValueError when testing membership of nodes.
                if key in self.edges:
                    artist_to_annotation[self.edge_artists[key]] = annotation
                elif key in self.nodes:
                    artist_to_annotation[self.node_artists[key]] = annotation
                else:
                    raise ValueError(
                        f"There is no node or edge with the ID {key} for the annotation '{annotation}'."
                    )

        if "annotation_fontdict" in kwargs:
            AnnotateOnHover.__init__(
                self, artist_to_annotation, kwargs["annotation_fontdict"]
            )
        else:
            AnnotateOnHover.__init__(self, artist_to_annotation)

        if "mapping" in kwargs:
            mapping = dict()
            for key, linked_nodes in kwargs["mapping"].items():
                if key in self.nodes:
                    mapping[self.node_artists[key]] = linked_nodes
                elif key in self.edges:
                    mapping[self.edge_artists[key]] = linked_nodes
                else:
                    raise ValueError(
                        f"There is no node or edge with the ID {key} for the table '{linked_nodes}'."
                    )
            EmphasizeOnClick.__init__(self, mapping)

        if "tables" in kwargs:
            artist_to_table = dict()
            if "tables" in kwargs:
                for key, table in kwargs["tables"].items():
                    if key in self.nodes:
                        artist_to_table[self.node_artists[key]] = table
                    elif key in self.edges:
                        artist_to_table[self.edge_artists[key]] = table
                    else:
                        raise ValueError(
                            f"There is no node or edge with the ID {key} for the table '{table}'."
                        )
            TableOnHover.__init__(self, artist_to_table)

    def _on_release(self, event):
        if self._currently_dragging is False:
            if hasattr(self, "mapping"):
                EmphasizeOnClick._on_release(self, event)
        else:
            if self.artist_to_annotation:
                self._redraw_annotations(event)

    def _on_motion(self, event):
        if self.artist_to_annotation:
            AnnotateOnHoverGraph._on_motion(self, event)
        TableOnHoverGraph._on_motion(self, event)

    def _select_artist(self, artist):
        if not (artist in self._selected_artists):
            linewidth = artist._lw_data
            artist.set_linewidth(max(1.5 * linewidth, 0.003))
            artist.set_edgecolor("black")
            artist.set_facecolor("magenta")
            self._selected_artists.append(artist)
            self.fig.canvas.draw_idle()

    def _deselect_artist(self, artist):
        if artist in self._selected_artists:
            artist.set_linewidth(self._base_linewidth[artist])
            artist.set_edgecolor(self._base_edgecolor[artist])
            artist.set_facecolor(self._base_facecolor[artist])
            self._selected_artists.remove(artist)
            self.fig.canvas.draw_idle()
