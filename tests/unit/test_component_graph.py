import pytest

from functional_base_charm.component_graph import ComponentGraph
from functional_base_charm.component_graph_item import ComponentGraphItem
from tests.unit.fixtures import MinimallyExtendedComponent


class TestAdd:
    def test_add_new_components_succeeds(self):
        """Tests that adding a new Component succeeds as expected."""
        cg = ComponentGraph()
        cgi1 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component1",
            depends_on=[]
        )

        assert isinstance(cgi1, ComponentGraphItem)

        cgi2 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component2",
            depends_on=[cgi1]
        )

        name = "component3"
        cgi3 = cg.add(
            component=MinimallyExtendedComponent(),
            name=name,
            depends_on=[cgi1, cgi2]
        )

        assert cgi3.name == name
        assert len(cgi3.depends_on) == 2

    def test_add_existing_item_raises(self):
        """Tests that adding two Components of the same name raises an Exception."""
        name = "component"

        cg = ComponentGraph()
        cgi1 = cg.add(
            component=MinimallyExtendedComponent(),
            name=name
        )
        with pytest.raises(ValueError):
            cg.add(
                component=MinimallyExtendedComponent(),
                name=name
            )


class TestGetExecutableComponentItems:

    def test_when_component_graph_is_empty(self):
        cg = ComponentGraph()
        assert len(cg.get_executable_component_items()) == 0

    def test_when_component_graph_has_mix_of_executable_and_not_executable(self):
        cg = ComponentGraph()
        cgi1 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component1",
            depends_on=[]
        )

        cgi2 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component2",
            depends_on=[cgi1]
        )

        cgi3 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component3",
            depends_on=[cgi1]
        )

        # Assert that we have one cgi ready for execution (cgi1)
        executable_cgis = cg.get_executable_component_items()
        assert len(executable_cgis) == 1
        assert executable_cgis[0] == cgi1

        # "execute" cgi1, then check if cgi2 and cgi3 are executable
        cgi1.component.configure_charm("mock event")
        cgi1.executed = True
        executable_cgis = cg.get_executable_component_items()
        assert len(executable_cgis) == 2



class TestYieldExecutableComponentItems:

    def test_no_items(self):
        """Tests that the generator does not yield anything if there are no items."""
        cg = ComponentGraph()
        with pytest.raises(StopIteration):
            next(cg.yield_executable_component_items())

    def test_no_executable_items(self):
        """Tests that the generator does not yield anything if there is nothing executable."""
        cg = ComponentGraph()
        cgi1 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component1",
            depends_on=[]
        )
        cgi1.executed = True

        with pytest.raises(StopIteration):
            next(cg.yield_executable_component_items())

    def test_with_several_component_items(self):
        """An end-to-end style test of ComponentGraph.yield_executable_component_items()."""
        cg = ComponentGraph()
        cgi1 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component1",
            depends_on=[]
        )

        cgi2 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component2",
            depends_on=[cgi1]
        )

        cgi3 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component3",
            depends_on=[cgi1]
        )

        cgi4 = cg.add(
            component=MinimallyExtendedComponent(),
            name="component4",
            depends_on=[cgi2, cgi3]
        )

        cgi_generator = cg.yield_executable_component_items()

        # Assert that we first get cgi1
        assert next(cgi_generator) == cgi1

        # Assert that we don't have anything else ready for execution yet
        assert len(cg.get_executable_component_items()) == 0

        # If we "execute" cgi1, cgi2 and cgi3 should be yielded next
        cgi1.executed = True
        cgi1.component.configure_charm("mock event")

        assert next(cgi_generator) == cgi2
        assert next(cgi_generator) == cgi3

        # And cgi4 should not be available
        assert len(cg.get_executable_component_items()) == 0

        # Even if one of cgi2 and cgi3 are "executed"
        cgi3.executed = True
        cgi3.component.configure_charm("mock event")

        assert len(cg.get_executable_component_items()) == 0

        # But cgi4 will yield if all prerequisites are ready
        cgi2.executed = True
        cgi2.component.configure_charm("mock event")

        assert next(cgi_generator) == cgi4

        # And now the generator should be empty
        with pytest.raises(StopIteration):
            next(cgi_generator)
