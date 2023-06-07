# TODO.  Just storing some stuff here for now
from unittest.mock import patch

from ops import StatusBase, ActiveStatus, WaitingStatus
from functional_base_charm.component import Component



class TestMinimallyExtendedComponent:
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

        def status(self) -> StatusBase:
            if not self._completed_work:
                return WaitingStatus("Waiting for execution")

            return ActiveStatus()

        def _configure_unit(self, event):
            self._completed_work = "some work"

    def test_status_before_execution(self):
        """Tests that the minimal implementation of Component does not raise a syntax error."""
        component = self.MinimallyExtendedComponent()
        status = component.status()
        assert isinstance(status, WaitingStatus)

    def test_status_after_execution(self):
        """Tests that the minimal implementation of Component does not raise a syntax error."""
        component = self.MinimallyExtendedComponent()
        component.configure_charm("mock event")
        status = component.status()
        assert isinstance(status, ActiveStatus)

    def test_configure_charm(self):
        component = self.MinimallyExtendedComponent()

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
