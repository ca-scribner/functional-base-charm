from typing import List, Callable, Optional

import lightkube
from lightkube.core.exceptions import ApiError
from lightkube.generic_resource import load_in_cluster_generic_resources
from ops import StatusBase, BlockedStatus, ActiveStatus

from charmed_kubeflow_chisme.exceptions import GenericCharmRuntimeError
from charmed_kubeflow_chisme.kubernetes import KubernetesResourceHandler
from charmed_kubeflow_chisme.kubernetes._kubernetes_resource_handler import _in_left_not_right, _hash_lightkube_resource
from functional_base_charm.component import Component


class KubernetesComponent(Component):

    def __init__(self, resource_templates: List[str], krh_labels: dict, lightkube_client: lightkube.Client,
                 context_callable: Optional[Callable] = None):
        super().__init__()
        self._resource_templates = resource_templates
        self._krh_labels = krh_labels
        self._lightkube_client = lightkube_client
        if context_callable is None:
            context_callable = lambda: {}
        self._context_callable = context_callable

    def _configure_unit(self, event):
        # no per-unit actions needed
        pass

    def _configure_app_leader(self, event):
        try:
            krh = self._get_kubernetes_resource_handler()
            krh.apply()
        except ApiError as e:
            # TODO: Blocked?
            raise GenericCharmRuntimeError("Failed to create Kubernetes resources") from e

    def _configure_app_non_leader(self, event):
        # no non-leader application actions needed
        pass

    def _get_kubernetes_resource_handler(self) -> KubernetesResourceHandler:
        """Returns a KubernetesResourceHandler for this class."""
        k8s_resource_handler = KubernetesResourceHandler(
            field_manager="TODO: Make this optional",
            template_files=self._resource_templates,
            context=self._context_callable(),
            lightkube_client=self._lightkube_client,
            labels=self._krh_labels,
        )
        load_in_cluster_generic_resources(k8s_resource_handler.lightkube_client)
        return k8s_resource_handler

    @property
    def status(self) -> StatusBase:
        """Returns the status of this Component based on whether its desired resources exist.

        Todo: This could use improvements on validation, and some of the logic could be moved into
        the KubernetesResourceHandler class.
        """
        # TODO: Add better validation
        krh = self._get_kubernetes_resource_handler()

        # TODO: Move this validation into KRH class
        existing_resources = krh.get_deployed_resources()
        desired_resources = krh.render_manifests()

        # Delete any resources that exist but are no longer in scope
        missing_resources = _in_left_not_right(
            desired_resources, existing_resources, hasher=_hash_lightkube_resource
        )

        # TODO: This feels awkward.  This will happen both if we haven't deployed anything yet (a
        #  typical case of "just wait longer") and if a resource has been lost.  How to handle this
        #  better?
        if len(missing_resources) > 0:
            return BlockedStatus(
                "Not all resources found in cluster.  This may be transient if we haven't tried "
                "to deploy them yet."
            )

        return ActiveStatus()
