# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""A reusable reconcile loop for Charms."""
import logging
from typing import Optional, List

from ops import CharmBase, EventBase, Object, StatusBase

from .component_graph import ComponentGraph

logger = logging.getLogger(__name__)


class CharmReconciler(Object):
    """A reusable reconcile loop for Charms."""

    def __init__(self, charm: CharmBase, component_graph: Optional[ComponentGraph] = None):
        """A reusable reconcile loop for Charms.

        TODO: Do we really need to pass `charm` here?  We barely use it.  I think we need it (or
         really, the framework) to

        Args:
            charm: a CharmBase object to operate from this CharmReconciler
            component_graph: (optional) a ComponentGraph that is used to define the execution order
                             of Components.  If None, an empty ComponentGraph will be created.
        """
        super().__init__(parent=charm, key=None)

        if component_graph is None:
            component_graph = ComponentGraph()

        self._charm = charm
        self.component_graph = component_graph

    def execute_components(self, event: EventBase):
        """Executes all components that are ready for execution, ordered by their dependencies.

        This would be the handler for charm events like config-changed, etc.
        """
        logger.info(f"Starting `execute_components` for event '{event.handle}'")

        # TODO: Think this through again.  Look ok still?
        for component_item in self.component_graph.yield_executable_component_items():
            logger.info(
                f"Executing component_item.component.configure_charm for '{component_item.name}'"
            )

            component_item.component.configure_charm(event)
            # TODO: If this component executes but does not go to ready, is there something we
            #  should do?  Omitted for now.
            # if not component_item.component.ready:
            #     raise NotImplementedError()

        # TODO: Because on.commit didn't work for the Prioritiser, we add a call to Prioritiser
        #  here.  This should be improved on in future.
        logger.info("execute_components execution loop complete.")
        status = self.component_graph.status_prioritiser.highest()
        logger.info(f"Got status {status} from Prioritiser - updating unit status")
        self._charm.unit.status = status

    def install(self, charm: CharmBase):
        """Installs execute_components as the handler for all necessary charm events.

        TODO: This might not be needed if implemented as an extension to CharmBase,
        but would be helpful if a standalone class.  Would include handling
        config-changed, update-status, etc.
        """
        # Install standard events
        charm.framework.observe(charm.on.install, self.execute_components)
        charm.framework.observe(charm.on.config_changed, self.execute_components)

        # Install any custom events our component_graph needs
        additional_events = self.component_graph.get_events_to_observe()
        for event in additional_events:
            charm.framework.observe(event, self.execute_components)

        # Install our status updater
        # TODO: Does this implicitly make an update_status?
        # TODO: Disabled because prioritizer's install doesn't work.  See note on that method
        # self.component_graph.status_prioritiser.install(charm.framework, charm.unit)

    def status(self) -> StatusBase:
        """Returns a status representing the the entire charm execution.

        .install() would attach this to the update-status event.

        Status is assembled from the .status of the Components.  If A and B are
        Active, then this is Active.

        This probably needs context from the dependencies between the Components
        (B is blocked by A).  Could leverage something like the
        Prioritiser class.  This status needs to be passed along somehow to the
        charm's overall status.
        """
