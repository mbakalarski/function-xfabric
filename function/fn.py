"""A Crossplane composition function."""

import grpc
from crossplane.function import logging, response
from crossplane.function.proto.v1 import run_function_pb2 as fnv1
from crossplane.function.proto.v1 import run_function_pb2_grpc as grpcv1


class FunctionRunner(grpcv1.FunctionRunnerService):
    """A FunctionRunner handles gRPC RunFunctionRequests."""

    def __init__(self):
        """Create a new FunctionRunner."""
        self.log = logging.get_logger()

    async def RunFunction(
        self, req: fnv1.RunFunctionRequest, _: grpc.aio.ServicerContext
    ) -> fnv1.RunFunctionResponse:
        """RunFunction method."""
        log = self.log.bind(tag=req.meta.tag)
        log.info("Running function")

        rsp = response.to(req)

        api_version = req.observed.composite.resource["apiVersion"]
        if api_version != "netclab.github.io/v1alpha1":
            log.error("Unsupported composite apiVersion", api_version=api_version)
            raise grpc.RpcError(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"unsupported composite apiVersion: {api_version}",
            )

        kind = req.observed.composite.resource["kind"]
        if kind != "XFabric":
            log.error("Unsupported composite kind", kind=kind)
            raise grpc.RpcError(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"unsupported composite kind: {kind}",
            )

        nodes = req.observed.composite.resource["spec"]["nodes"]

        for node in nodes:
            name = node["name"]
            nodetype = node["type"]
            url = node["url"]
            interfaces = node["interfaces"]

            kind = nodetype[0].upper() + nodetype[1:]

            rsp.desired.resources[f"{name}"].resource.update(
                {
                    "apiVersion": "netclab.github.io/v1alpha1",
                    "kind": kind,
                    "metadata": {"name": name},
                    "spec": {
                        "interfaces": interfaces,
                        "forProvider": {
                            "url": url,
                        },
                    },
                }
            )

        log.info("Added desired nodes", count=len(nodes))

        return rsp
