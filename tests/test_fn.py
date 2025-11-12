import dataclasses
import unittest

from crossplane.function import logging, resource
from crossplane.function.proto.v1 import run_function_pb2 as fnv1
from google.protobuf import duration_pb2 as durationpb
from google.protobuf import json_format
from google.protobuf import struct_pb2 as structpb

from function import fn


class TestFunctionRunner(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        logging.configure(level=logging.Level.DISABLED)
        self.maxDiff = None

    async def test_run_function(self) -> None:
        @dataclasses.dataclass
        class TestCase:
            reason: str
            req: fnv1.RunFunctionRequest
            want: fnv1.RunFunctionResponse

        input_dict = {
            "apiVersion": "netclab.github.io/v1alpha1",
            "kind": "XFabric",
            "metadata": {"name": "example-fabric"},
            "spec": {
                "networks": [{"name": "s1"}, {"name": "l1"}],
                "nodes": [
                    {
                        "name": "spine1",
                        "type": "srlinux",
                        "url": "gnmi://spine1.default.svc.cluster.local:9339",
                        "interfaces": [{"name": "e1-49", "network": "s1"}],
                    },
                    {
                        "name": "leaf1",
                        "type": "srlinux",
                        "url": "gnmi://leaf1.default.svc.cluster.local:9339",
                        "interfaces": [
                            {"name": "e1-49", "network": "s1"},
                            {"name": "e1-1", "network": "l1"},
                        ],
                    },
                    {
                        "name": "srv1",
                        "type": "linux",
                        "url": "ssh://srv1.default.svc.cluster.local:22",
                        "interfaces": [{"name": "eth1", "network": "l1"}],
                    },
                ],
            },
        }

        output_dict = [
            {
                "apiVersion": "netclab.github.io/v1alpha1",
                "kind": "Srlinux",
                "metadata": {"name": "leaf1"},
                "spec": {
                    "forProvider": {
                        "url": "gnmi://leaf1.default.svc.cluster.local:9339"
                    },
                    "interfaces": [
                        {"name": "e1-49", "network": "s1"},
                        {"name": "e1-1", "network": "l1"},
                    ],
                },
            },
            {
                "apiVersion": "netclab.github.io/v1alpha1",
                "kind": "Srlinux",
                "metadata": {"name": "spine1"},
                "spec": {
                    "forProvider": {
                        "url": "gnmi://spine1.default.svc.cluster.local:9339"
                    },
                    "interfaces": [{"name": "e1-49", "network": "s1"}],
                },
            },
            {
                "apiVersion": "netclab.github.io/v1alpha1",
                "kind": "Linux",
                "metadata": {"name": "srv1"},
                "spec": {
                    "forProvider": {"url": "ssh://srv1.default.svc.cluster.local:22"},
                    "interfaces": [{"name": "eth1", "network": "l1"}],
                },
            },
        ]

        cases = [
            TestCase(
                reason="The function should compose 2x Srlinux and 1x Linux.",
                req=fnv1.RunFunctionRequest(
                    observed=fnv1.State(
                        composite=fnv1.Resource(
                            resource=resource.dict_to_struct(input_dict)
                        )
                    )
                ),
                want=fnv1.RunFunctionResponse(
                    meta=fnv1.ResponseMeta(ttl=durationpb.Duration(seconds=60)),
                    desired=fnv1.State(
                        resources={
                            node["metadata"]["name"]: fnv1.Resource(
                                resource=resource.dict_to_struct(node)
                            )
                            for node in output_dict
                        }
                    ),
                    context=structpb.Struct(),
                ),
            ),
        ]

        runner = fn.FunctionRunner()

        for case in cases:
            got = await runner.RunFunction(case.req, None)
            self.assertEqual(
                json_format.MessageToDict(got),
                json_format.MessageToDict(case.want),
                f"Failed test: {case.reason}",
            )


if __name__ == "__main__":
    unittest.main()
