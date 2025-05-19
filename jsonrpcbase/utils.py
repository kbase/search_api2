import json
import jsonschema
import os
import yaml

from typing import Optional, Any, List, Union

import jsonrpcbase.exceptions as exceptions


# Type of `obj` should be anything that has the __getitem__ method
def get_path(obj: Any, path: List[str]) -> Optional[Any]:
    """
    Get a nested value by a series of keys inside some nested indexable
    containers, returning None if the path does not exist, avoiding any errors.
    Args:
        obj: any indexable (has __getitem__ method) obj
        path: list of accessors, such as dict keys or list indexes
    Examples:
        get_path([{'x': {'y': 1}}], [0, 'x', 'y']) -> 1
    """
    for key in path:
        try:
            obj = obj[key]
        except Exception:
            return None
    return obj


def load_yaml_or_json(path: str) -> dict:
    """
    Load yaml or json data from a file path into a python object
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == '.yaml' or ext == '.yml':
        with open(path) as fd:
            ret = yaml.safe_load(fd)
    elif ext == '.json':
        with open(path) as fd:
            ret = json.load(fd)
    else:
        msg = f'File at path {path} must be YAML or JSON; {ext} is invalid'
        raise exceptions.InvalidFileType(msg)
    return ret


def load_schema(schema: Union[str, dict]) -> dict:
    """
    Load, parse, and validate a JSON-Schema from a YAML or JSON file path.

    Args:
        schema: dict of schema or file path to a JSON or YAML file
    Returns:
        An in-memory, jsonschema-validated python object

    throws InvalidSchemaError
    """
    if isinstance(schema, str):
        schema = load_yaml_or_json(schema)
    elif schema is None:
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
        }
    # Validate the schema
    jsonschema.Draft7Validator.check_schema(schema)
    # Set some defaults
    schema['definitions'] = schema.get('definitions', {})
    schema['definitions']['methods'] = schema['definitions'].get('methods', {})
    # Set service discovery schema
    if 'rpc.discover' in schema['definitions']['methods']:
        msg = "The `rpc.discover` method is reserved and should not be used"
        raise exceptions.InvalidSchemaError(msg)
    # Builtin method schemas
    schema['definitions']['methods']['rpc.discover'] = {}
    return schema


def load_service_info(service_info: Union[dict, str]):
    """Load the service info data, possibly from a file path."""
    if isinstance(service_info, dict):
        info = service_info
    if isinstance(service_info, str):
        info = load_yaml_or_json(service_info)
    jsonschema.validate(info, {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": ["title", "version", "description"],
        "properties": {
            "title": {"type": "string"},
            "version": {"type": "string"},
            "description": {"type": "string"},
        }
    })
    return info


def get_method_schemas(schema: dict, method_name: str):
    """
    Get the params and result schema for a given method by name from the
    service schema.
    """
    params_path = ['definitions', 'methods', method_name, 'params']
    result_path = ['definitions', 'methods', method_name, 'result']
    params = get_path(schema, params_path)
    result = get_path(schema, result_path)
    # Clone the data so it can be safely mutated
    params = dict(params) if params is not None else params
    result = dict(result) if result is not None else result
    return (params, result)


def response_id(req_data):
    """
    Get the ID for the response from a JSON-RPC request
    Return None if ID is missing or invalid
    """
    _id = None
    if isinstance(req_data, dict):
        _id = req_data.get('id')
    if type(_id) in (str, int):
        return _id
    else:
        return None
