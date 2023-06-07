import pytest
from ops import ActiveStatus, StatusBase, WaitingStatus, MaintenanceStatus

from functional_base_charm.component import Component
from functional_base_charm.component_graph_item import ComponentGraphItem


COMPONENT_NAME = "component"


# TODO: Duplicate with other tests.  Can it be shared?
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
        if not self._completed_work:
            return WaitingStatus("Waiting for execution")

        return ActiveStatus()

    def _configure_unit(self, event):
        self._completed_work = "some work"


@pytest.fixture()
def component_active_factory():
    """Returns a factory for Components that will be Active."""
    def factory() -> Component:
        component = MinimallyExtendedComponent()
        component._completed_work = "some work"
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

class TestExecuted:
    """Tests for the .executed property."""
    def test_default(self, component_graph_item_factory):
        """Tests that the default value of executed is False."""
        assert component_graph_item_factory().executed is False

    def test_set_to_true(self, component_graph_item_factory):
        """Tests that executed can be updated to True."""
        component_graph_item = component_graph_item_factory()
        component_graph_item.executed = True
        assert component_graph_item.executed is True

    def test_set_to_invalid(self, component_graph_item_factory):
        """Tests that executed rejects invalid types."""
        with pytest.raises(ValueError):
            component_graph_item_factory().executed = "something else"


class TestReadyForExecution:
    def test_no_depends_not_executed(self, component_graph_item_factory):
        """Tests that CGI ready for execution when it has no depends_on and has not executed."""
        component_graph_item = component_graph_item_factory()
        assert component_graph_item.ready_for_execution is True

    def test_no_depends_already_executed(self, component_graph_item_factory):
        """Tests that ComponentGraphItem is not ready for execution if it has already executed."""
        component_graph_item = component_graph_item_factory()
        component_graph_item.executed = True
        assert component_graph_item.ready_for_execution is False

    def test_when_depends_not_ready(self, component_graph_item_with_depends_not_active_factory):
        """Tests that ComponentGraphItem is not ready for execution if its depends_on are not."""
        component_graph_item = component_graph_item_with_depends_not_active_factory()
        assert component_graph_item.ready_for_execution is False

    def test_when_depends_ready(self, component_graph_item_with_depends_active_factory):
        """Tests if this ComponentGraphItem is ready for execution if its depends_on are ready."""
        component_graph_item = component_graph_item_with_depends_active_factory()
        assert component_graph_item.ready_for_execution is True


class TestStatus:
    def test_prerequisites_inactive(self, component_graph_item_with_depends_not_active_factory):
        """Tests status when CGI prerequisites are not active."""
        cgi = component_graph_item_with_depends_not_active_factory()
        assert isinstance(cgi.status, MaintenanceStatus)
        assert "waiting on" in cgi.status.message

    def test_prerequisites_active_not_executed(self, component_graph_item_with_depends_active_factory):
        """Tests status when CGI prerequisites are active but this CGI has not executed."""
        cgi = component_graph_item_with_depends_active_factory()
        assert isinstance(cgi.status, MaintenanceStatus)
        assert "waiting on" not in cgi.status.message

    def test_prerequisites_active_is_executed_status_waiting(self, component_graph_item_with_depends_active_factory):
        """Tests status when CGI prerequisites are active but this CGI has non-active Status."""
        cgi = component_graph_item_with_depends_active_factory()
        cgi.executed = True
        assert isinstance(cgi.status, WaitingStatus)

    def test_prerequisites_active_is_executed_status_active(self, component_graph_item_with_depends_active_factory):
        """Tests status when CGI prerequisites are active and this CGI is Active and executed."""
        cgi = component_graph_item_with_depends_active_factory()
        cgi.executed = True
        cgi.component._completed_work = "some work"
        assert isinstance(cgi.status, ActiveStatus)

    def test_no_prerequisites_is_executed_status_active(self, component_graph_item_active_factory):
        """Tests status when CGI is executed, active, and has no prerequisites."""
        cgi = component_graph_item_active_factory()
        assert isinstance(cgi.status, ActiveStatus)


class TestInactivePrerequisites:
    def test_no_depends(self, component_graph_item_factory):
        """Tests inactive_prerequisites when CGI has no depends_on."""
        assert len(component_graph_item_factory()._inactive_prerequisites()) == 0

    def test_depends_active(self, component_graph_item_with_depends_active_factory):
        """Tests inactive_prerequisites when CGI depends_on that are all Active."""
        assert len(component_graph_item_with_depends_active_factory()._inactive_prerequisites()) == 0

    def test_depends_not_active(self, component_graph_item_with_depends_not_active_factory):
        """Tests inactive_prerequisites when CGI depends_on that are all not Active."""
        assert len(component_graph_item_with_depends_not_active_factory()._inactive_prerequisites()) > 0

    def test_depends_mixed(self, component_inactive_factory, component_graph_item_factory, component_graph_item_active_factory):
        """Tests inactive_prerequisites when CGI has depends_on that has a mix of Active and not Active."""
        cgi = ComponentGraphItem(
            component=component_inactive_factory(),
            name=COMPONENT_NAME,
            depends_on=[
                component_graph_item_active_factory(),
                component_graph_item_factory(),
                component_graph_item_factory(),
            ]
        )
        assert len(cgi._inactive_prerequisites()) == 2
