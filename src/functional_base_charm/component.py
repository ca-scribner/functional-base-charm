from abc import ABC, abstractmethod
from typing import List

from ops import ActiveStatus, StatusBase, BoundEvent


class Component(ABC):
    """Abstract class defining the API needed for an atomic piece of work that a charm does.

    This is intended to be extended for different types of operations, such as managing Pebble
    containers or relation libraries.
    """
    def __init__(self):
        self._events_to_observe: List[str] = []

    # Methods that can be used directly from the Component class for most cases
    def configure_charm(self, event):
        """Public API to get this Component to do whatever it should with an Event.

        Generally should be reusable for most use cases.  Ideally, the _private
        methods are where subclasses should modify behaviour.
        """
        self._configure_unit(event)
        self._configure_app(event)

    def _configure_app(self, event):
        """Execute everything this Component should do at the Application level.

        Generally should be reusable for most use cases.  Ideally, override
        _configure_app_leader and _configure_app_non_leader instead.
        """
        self._configure_app_leader(event)
        self._configure_app_non_leader(event)

    @property
    def ready(self) -> bool:
        """Returns boolean indicating if Component is ready (Active)."""
        return isinstance(self.status, ActiveStatus)

    @property
    def ready_for_execution(self) -> bool:
        """Returns boolean indicating if Component is ready for execution.

        Extend this method with custom logic if this Component has validation to run before it can
        be executed.  For example, a PebbleContainer can check wither the container is ready.
        """
        return True

    @property
    def events_to_observe(self) -> List[str]:
        """Returns the list of events this Component wants to observe, by name.

        TODO: Would this be better returning actual BoundEvents instead of their names?
        """
        return self._events_to_observe

    # Methods that should be overridden when creating a Component subclass
    @abstractmethod
    def _configure_unit(self, event):
        """Executes everything this Component should do for every Unit.

        Override this method to implement anything this Component should do for
        every unit in the charm.
        """

    @abstractmethod
    def _configure_app_leader(self, event):
        """Execute everything this Component should do at the Application level for leaders.

        Override this method to implement anything this Component should do for
        the leader unit.
        """

    @abstractmethod
    def _configure_app_non_leader(self, event):
        """Execute everything this Component should do at the Application level for non-Leaders.

        Override this method to implement anything this Component should do for
        every unit that is not the leader.
        """

    @property
    @abstractmethod
    def status(self) -> StatusBase:
        """Returns the status of this Component.

        Override this method to implement the logic that establishes your Component
        status (eg: if I have data from my relation, I am Active)
        """


