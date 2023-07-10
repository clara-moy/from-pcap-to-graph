from netgraph._main import InteractiveGraph, EmphasizeOnHoverGraph


class NewInteractiveGraph(InteractiveGraph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._base_facecolor = dict(
            [(artist, artist.get_facecolor()) for artist in self._selectable_artists]
        )

    def _on_motion(self, event):
        EmphasizeOnHoverGraph._on_motion(self, event)

    def _select_artist(self, artist):
        if not (artist in self._selected_artists):
            linewidth = artist._lw_data
            artist.set_linewidth(max(1.5 * linewidth, 0.003))
            artist.set_edgecolor("black")
            artist.set_facecolor("magenta")
            self._selected_artists.append(artist)
            self.fig.canvas.draw_idle()

    def _deselect_artist(self, artist):
        if artist in self._selected_artists:  # should always be true?
            artist.set_linewidth(self._base_linewidth[artist])
            artist.set_edgecolor(self._base_edgecolor[artist])
            artist.set_facecolor(self._base_facecolor[artist])
            self._selected_artists.remove(artist)
            self.fig.canvas.draw_idle()
