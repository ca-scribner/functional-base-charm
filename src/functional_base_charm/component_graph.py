from __future__ import annotations  # To enable type hinting a method in a class with its own class
from typing import Iterable, List, Optional

from ops import StatusBase

from .component import Component
from .component_graph_item import ComponentGraphItem
from .multistatus import Prioritiser


class ComponentGraph:
    def __init__(self):
        self.component_items = {}
        self.status_prioritiser = Prioritiser()

    def add(
        self,
        component: Component,
        name: str,
        depends_on: Optional[List[ComponentGraphItem]] = None,
    ) -> ComponentGraphItem:
        """Add a component to the graph, returning a ComponentGraphItem for this Component."""
        # TODO: It feels easier to pass Component's in `depends_on`, but then harder for us to
        #  process them here (we identify components by their name).
        if name in self.component_items:
            raise ValueError(
                f"Cannot add component {name} - component named {name} already exists."
            )
        # TODO: Make an actual graph of this
        #  or is this not needed?  If everything knows its dependencies and only says it is ready
        #  if they're satisfied, that might be enough.
        self.component_items[name] = ComponentGraphItem(
            component=component, name=name, depends_on=depends_on
        )

        self.status_prioritiser.add(name, lambda: self.component_items[name].status)

        return self.component_items[name]

    def get_executable_component_items(self) -> List[ComponentGraphItem]:
        """Returns a list of ComponentGraphItems ready for execution."""
        return [item for item in self.component_items.values() if item.ready_for_execution]

    def yield_executable_component_items(self) -> Iterable[Component]:
        """Yields all executable components, marking them as executed as they're yielded.

        Will only yield Components after all their depends_on Components are ready.
        """
        # TODO: Is there any way this can become an infinite loop?  Add a failsafe just in case?
        while len(executable_component_items := self.get_executable_component_items()) > 0:
            executable_component_items[0].executed = True
            yield executable_component_items[0]

    def get_by_name(self, name: str):
        """Returns a component, accessed by name."""
        raise NotImplementedError()

    @property
    def status(self) -> StatusBase:
        """Returns the worst status of all ComponentItems in the collection."""
        return self.status_prioritiser.highest()

    def summarise(self):
        """Placeholder - definitely need something to help writing/debugging
        charms.  Not sure exactly what to put here.
        """
        raise NotImplementedError()
