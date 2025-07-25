from dataclasses import dataclass
from typing import Any, Optional

import nexusrpc
import nexusrpc.handler
import pytest
from nexusrpc.handler import StartOperationContext, sync_operation

from temporalio import nexus
from temporalio.nexus import WorkflowRunOperationContext, workflow_run_operation


@dataclass
class _InterfaceImplementationTestCase:
    Interface: type[Any]
    Impl: type[Any]
    error_message: Optional[str]


class ValidImpl(_InterfaceImplementationTestCase):
    @nexusrpc.service
    class Interface:
        op: nexusrpc.Operation[None, None]

    class Impl:
        @sync_operation
        async def op(self, _ctx: StartOperationContext, _input: None) -> None: ...

    error_message = None


class ValidWorkflowRunImpl(_InterfaceImplementationTestCase):
    @nexusrpc.service
    class Interface:
        op: nexusrpc.Operation[str, int]

    class Impl:
        @workflow_run_operation
        async def op(
            self, _ctx: WorkflowRunOperationContext, _input: str
        ) -> nexus.WorkflowHandle[int]:
            raise NotImplementedError

    error_message = None


@pytest.mark.parametrize(
    "test_case",
    [
        ValidImpl,
        ValidWorkflowRunImpl,
    ],
)
def test_service_decorator_enforces_interface_conformance(
    test_case: type[_InterfaceImplementationTestCase],
):
    if test_case.error_message:
        with pytest.raises(Exception) as ei:
            nexusrpc.handler.service_handler(test_case.Interface)(test_case.Impl)
        err = ei.value
        assert test_case.error_message in str(err)
    else:
        nexusrpc.handler.service_handler(service=test_case.Interface)(test_case.Impl)
