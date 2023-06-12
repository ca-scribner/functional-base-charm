# TODO.  Just storing some stuff here for now
from unittest.mock import patch

from ops import ActiveStatus, WaitingStatus

from fixtures import MinimallyExtendedComponent, harness


class TestMinimallyExtendedComponent:

    def test_status_before_execution(self, harness):
        """Tests that the minimal implementation of Component does not raise a syntax error."""
        component = MinimallyExtendedComponent(charm=harness.framework, name="test-component")
        assert isinstance(component.status, WaitingStatus)

    def test_status_after_execution(self, harness):
        """Tests that the minimal implementation of Component does not raise a syntax error."""
        component = MinimallyExtendedComponent(charm=harness.framework, name="test-component")
        component.configure_charm("mock event")
        assert isinstance(component.status, ActiveStatus)

    def test_configure_charm(self, harness):
        component = MinimallyExtendedComponent(charm=harness.framework, name="test-component")

        with (
                patch.object(component, "_configure_app_leader", wraps=component._configure_app_leader) as spied_configure_app_leader,
                patch.object(component, "_configure_app_non_leader", wraps=component._configure_app_non_leader) as spied_configure_app_non_leader,
                patch.object(component, "_configure_unit", wraps=component._configure_unit) as spied_configure_unit,
        ):
            # TODO: Make a real event somehow
            event = "TODO: make this a real event"
            component.configure_charm(event)

            spied_configure_app_leader.assert_called()
            spied_configure_app_non_leader.assert_called()
            spied_configure_unit.assert_called()
