import logging
from abc import abstractmethod
from typing import List

from ops import CharmBase, StatusBase, WaitingStatus, ActiveStatus
from ops.pebble import Layer, ServiceInfo

from functional_base_charm.component import Component


logger = logging.getLogger(__name__)


class PebbleComponent(Component):
    """Wraps a non-service Pebble container."""
    def __init__(self, *args, charm: CharmBase, container_name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._charm = charm
        self.container_name = container_name
        self._events_to_observe: List[str] = [
            pebble_ready_event_from_container_name(self.container_name)
        ]

    def ready_for_execution(self) -> bool:
        """Returns True if Pebble is ready."""
        return self.pebble_ready

    @property
    def pebble_ready(self) -> bool:
        """Returns True if Pebble is ready."""
        return self._charm.unit.get_container(self.container_name).can_connect()

    def execute(self):
        """Execute the given command in the container managed by this Component."""
        raise NotImplementedError()

    def _configure_unit(self, event):
        pass

    def _configure_app_leader(self, event):
        pass

    def _configure_app_non_leader(self, event):
        pass

    @property
    def status(self) -> StatusBase:
        if not self.pebble_ready:
            return WaitingStatus("Waiting for Pebble to be ready.")

        return ActiveStatus()

    @abstractmethod
    def get_layer(self) -> Layer:
        """Pebble configuration layer for the container.

        Override this method with your own layer configuration.
        """


class PebbleServiceComponent(PebbleComponent):
    """Wraps a Pebble container that implements one or more services."""
    def __init__(self, *args, service_name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = service_name

    def _configure_unit(self, event):
        super()._configure_unit(event)
        # TODO: Checks for if we are the leader/there is a leader?  or skip that?
        # TODO: This may need refinement.  Sunbeam does it differently from us.  Why?  Maybe they
        #  dont expect to ever update and existing pebble plan?
        if not self.pebble_ready:
            logging.info("Container {self.container_name} not ready - cannot configure unit.")
            return

        container = self._charm.unit.get_container(self.container_name)
        new_layer = self.get_layer()

        current_layer = container.get_plan()
        if current_layer.services != new_layer.services:
            container.add_layer(self.container_name, new_layer, combine=True)
            # TODO: Add error handling here?  Not sure what will catch them yet so left out for now
            container.replan()

    @property
    def service_ready(self) -> bool:
        """Returns True if all services provided by this container are running."""
        if not self.pebble_ready:
            return False
        return len(self.get_services_not_ready()) == 0

    def get_services_not_ready(self) -> List[ServiceInfo]:
        """Returns a list of Pebble services that are not ready."""
        # TODO: This will raise an exception if pebble is not ready.  Should we catch it or let it
        #  raise?
        container = self._charm.unit.get_container(self.container_name)
        services = container.get_services()
        services_not_ready = [service for service in services.values() if not service.is_running()]
        return services_not_ready

    @property
    def status(self) -> StatusBase:
        """Returns the status of this Pebble service container.

        Status is determined by checking whether the container and service are up.
        """
        # TODO: Report on checks in the Status?
        if not self.pebble_ready:
            return WaitingStatus("Waiting for Pebble to be ready.")
        services_not_ready = self.get_services_not_ready()
        if len(services_not_ready) > 0:
            service_names = ", ".join([service.name for service in services_not_ready])
            return WaitingStatus(
                f"Waiting for Pebble services ({service_names}).  If this persists, it could be a"
                f" blocking configuration error.")
        return ActiveStatus()


def pebble_ready_event_from_container_name(container_name: str) -> str:
    """Returns the name of a pebble-ready event for a given container_name."""
    prefix = container_name.replace("-", "_")
    return f"{prefix}_pebble_ready"
