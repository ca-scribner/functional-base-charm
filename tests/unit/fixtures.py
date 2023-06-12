import pytest
from ops import ActiveStatus, StatusBase, WaitingStatus, BlockedStatus, CharmBase
from ops.testing import Harness

from functional_base_charm.component import Component
from functional_base_charm.component_graph_item import ComponentGraphItem


COMPONENT_NAME = "component"


class MinimallyExtendedComponent(Component):
    """A minimal example of a complete implementation of the abstract Component class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mock placeholder for state that indicates this Component's work is complete
        self._completed_work = None

    def _configure_app_leader(self, event):
        pass

    def _configure_app_non_leader(self, event):
        pass

    @property
    def status(self) -> StatusBase:
        """Returns ActiveStatus if self._completed_work is not Falsey, else WaitingStatus."""
        if not self._completed_work:
            return WaitingStatus("Waiting for execution")

        return ActiveStatus()

    def _configure_unit(self, event):
        """Fake doing some work."""
        self._completed_work = "some work"


class MinimallyBlockedComponent(MinimallyExtendedComponent):
    """A minimal Component that defaults to being Blocked."""
    @property
    def status(self) -> StatusBase:
        """Returns ActiveStatus if self._completed_work is not Falsey, else WaitingStatus."""
        if not self._completed_work:
            return BlockedStatus("Waiting for execution")

        return ActiveStatus()


@pytest.fixture()
def component_active_factory():
    """Returns a factory for Components that will be Active."""
    def factory() -> Component:
        component = MinimallyExtendedComponent()
        # "execute" the Component, making it now be Active because work has been done
        component.configure_charm("mock event")
        return component
    return factory


@pytest.fixture()
def component_inactive_factory():
    """Returns a factory for Components that will not be Active."""
    def factory() -> Component:
        return MinimallyExtendedComponent()
    return factory


@pytest.fixture()
def component_graph_item_factory():
    """Returns a factory for a ComponentGraphItem with a very minimal Component."""
    def factory() -> ComponentGraphItem:
        return ComponentGraphItem(
            component=MinimallyExtendedComponent(),
            name=COMPONENT_NAME,
        )
    return factory


@pytest.fixture()
def component_graph_item_active_factory(component_active_factory):
    """Returns a factory for a ComponentGraphItem with a very minimal Component that is Active."""
    def factory() -> ComponentGraphItem:
        cgi = ComponentGraphItem(
            component=component_active_factory(),
            name=COMPONENT_NAME,
        )
        cgi.executed = True
        return cgi
    return factory


@pytest.fixture()
def component_graph_item_with_depends_not_active_factory(component_graph_item_factory):
    """Returns a factory for a ComponentGraphItem that depends on another that is not Active."""
    def factory() -> ComponentGraphItem:
        return ComponentGraphItem(
            component=MinimallyExtendedComponent(),
            name=COMPONENT_NAME,
            depends_on=[component_graph_item_factory()]
        )
    return factory


@pytest.fixture()
def component_graph_item_with_depends_active_factory(component_graph_item_active_factory):
    """Returns a factory for a ComponentGraphItem that depends on another that is Active."""
    def factory() -> ComponentGraphItem:
        return ComponentGraphItem(
            component=MinimallyExtendedComponent(),
            name=COMPONENT_NAME,
            depends_on=[component_graph_item_active_factory()]
        )
    return factory


class DummyCharm(CharmBase):
    pass


@pytest.fixture()
def harness():
    harness = Harness(DummyCharm, meta="")
    harness.begin()
    return harness


METADATA_WITH_CONTAINER = """
name: test-charm
containers:
  test-container:
"""


@pytest.fixture()
def harness_with_container():
    harness = Harness(DummyCharm, meta=METADATA_WITH_CONTAINER)
    harness.begin()
    return harness
