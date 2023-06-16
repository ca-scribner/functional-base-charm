import logging
from abc import abstractmethod
from typing import List

from ops import CharmBase, StatusBase, WaitingStatus, ActiveStatus
from ops.pebble import Layer, ServiceInfo

from functional_base_charm.component import Component


logger = logging.getLogger(__name__)


class PebbleComponent(Component):
    """Wraps a non-service Pebble container."""
    def __init__(self, charm: CharmBase, container_name: str):
        """Instantiate the PebbleComponent.

        Args:
            charm:
            container_name: Name of this container.  Note that this name is also used as the
                            parent object's Component.name parameter.
        """
        super().__init__(charm=charm, name=container_name)
        self.container_name = self.name
        # TODO: Should a PebbleComponent automatically be subscribed to this event?  Or just
        #  a PebbleServiceComponent?
        self._events_to_observe: List[str] = [
            get_pebble_ready_event_from_charm(self._charm, self.container_name)
        ]

    @property
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


class PebbleServiceComponent(PebbleComponent):
    """Wraps a Pebble container that implements one or more services."""
    def __init__(self, *args, service_name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = service_name

    def _configure_unit(self, event):
        # TODO: Need to call super()._configure_unit()?
        super()._configure_unit(event)
        # TODO: Checks for if we are the leader/there is a leader?  or skip that?
        # TODO: This may need refinement.  Sunbeam does it differently from us.  Why?  Maybe they
        #  dont expect to ever update and existing pebble plan?
        if not self.pebble_ready:
            logging.info(f"Container {self.container_name} not ready - cannot configure unit.")
            return

        container = self._charm.unit.get_container(self.container_name)
        new_layer = self.get_layer()

        current_layer = container.get_plan()
        if current_layer.services != new_layer.services:
            container.add_layer(self.container_name, new_layer, combine=True)
            # TODO: Add error handling here?  Not sure what will catch them yet so left out for now
            container.replan()

    @abstractmethod
    def get_layer(self) -> Layer:
        """Pebble configuration layer for the container.

        Override this method with your own layer configuration.
        """

    @property
    def service_ready(self) -> bool:
        """Returns True if all services provided by this container are running."""
        if not self.pebble_ready:
            return False
        return len(self.get_services_not_active()) == 0

    def get_services_not_active(self) -> List[ServiceInfo]:
        """Returns a list of Pebble services that are defined in get_layer but not active."""
        # Get the expected services by inspecting our layer specification
        services_expected = [ServiceInfo(service_name, "disabled", "inactive") for service_name in self.get_layer().services.keys()]
        if not self.pebble_ready:
            return services_expected

        container = self._charm.unit.get_container(self.container_name)
        services = container.get_services()

        # Get any services that should be active, but are not in the container at all
        services_not_found = [service for service in services_expected if service.name not in services.keys()]
        services_not_active = [service for service in services.values() if not service.is_running()]

        services_not_ready = services_not_found + services_not_active

        return services_not_ready

    @property
    def status(self) -> StatusBase:
        """Returns the status of this Pebble service container.

        Status is determined by checking whether the container and service are up.
        """
        # TODO: Report on checks in the Status?
        if not self.pebble_ready:
            return WaitingStatus("Waiting for Pebble to be ready.")
        services_not_ready = self.get_services_not_active()
        if len(services_not_ready) > 0:
            service_names = ", ".join([service.name for service in services_not_ready])
            return WaitingStatus(
                f"Waiting for Pebble services ({service_names}).  If this persists, it could be a"
                f" blocking configuration error.")
        return ActiveStatus()


def get_pebble_ready_event_from_charm(charm: CharmBase, container_name: str) -> str:
    """Returns the pebble-ready event for a given container_name."""
    prefix = container_name.replace("-", "_")
    event_name = f"{prefix}_pebble_ready"
    return getattr(charm.on, event_name)
