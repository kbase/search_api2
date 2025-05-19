from typing import Dict, List, Optional, Union, Callable, NamedTuple


class ServiceInfo(NamedTuple):
    """
    Metadata about the whole service.
    """
    title: str
    description: str
    version: str


class Method(NamedTuple):
    """
    Method function handler, and any other metadata we may need in the future
    """
    method: Callable


# Mapping of method name to a namedtuple of handler function and anything else we need
MethodData = Dict[str, Method]

# RPC ID field
Identifier = Optional[Union[int, str]]
# RPC params or result field
ParamsResult = Optional[Union[dict, list]]

# Request structure
MethodRequest = Union[dict, List[dict]]

# Result structure for a JSON-RPC 2.0 request
# Will be None if the request was a notification
# Will be a list of results if request was batch
MethodResult = Optional[Union[dict, List[dict]]]
