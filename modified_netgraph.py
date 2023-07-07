from netgraph._main import InteractiveGraph, EmphasizeOnHoverGraph


class NewInteractiveGraph(InteractiveGraph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _on_motion(self, event):
        EmphasizeOnHoverGraph._on_motion(self, event)
