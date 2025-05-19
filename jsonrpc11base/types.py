from typing import Optional, Union


# RPC ID field
Identifier = Union[int, str, dict, list, bool, None]

# RPC params or result field
ParamsResult = Optional[Union[dict, list]]

# Request structure
MethodRequest = dict

# Result structure for a JSON-RPC 1.1 request
# Will be None if the request was a notification
# Otherwise a structure (dict)
MethodResult = Optional[dict]
