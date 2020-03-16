"""
Implements https://github.com/kbase/KBaseSearchAPI/blob/master/KBaseSearchEngine.spec

Quick type references:

PostProcessing type:
    skip_info - exclude 'parent_guid', 'object_name', and 'timestamp'
    skip_keys - exclude all the type-specific keys ('key_props' in the old indexes)
    skip_data - exclude "raw data" for the object ('data' and 'parent_data')
    ids_only - shortcut to mark all three skips as true
    include_highlight - include highlights of fields that matched the query


ObjectData type:
    guid - string - unique id for the doc ('_id' field in our case)
    parent_guid - string - id of a parent if there is a parent object
    object_name - string - name of object
    timestamp - int - save date of object
    parent_data - object - parent data
    data - object - object-specific data
    key_props
    object_props - dict
          general properties for all objects. This mapping contains the keys
          'creator', 'copied', 'module', 'method', 'module_ver', and 'commit' -
          respectively the user that originally created the object, the user
          that copied this incarnation of the object, and the module and method
          used to create the object and their version and version control
          commit hash. Not all keys may be present; if not their values were
          not available in the search data.
    highlight - dict of string to list of string - search result highlights from ES. TODO
          The keys are the field names and the list contains the sections in
          each field that matched the search query. Fields with no hits will
          not be available. Short fields that matched are shown in their
          entirety. Longer fields are shown as snippets preceded or followed by
          "...".
"""
from src.jsonrpcbase import JSONRPCService

from src.legacy.methods.status import status
from src.legacy.methods.search_types import search_types
from src.legacy.methods.search_types2 import search_types2
from src.legacy.methods.search_objects import search_objects
from src.legacy.methods.search_objects2 import search_objects2
from src.legacy.methods.get_objects import get_objects
from src.legacy.methods.get_objects2 import get_objects2
from src.legacy.methods.list_types import list_types


# RPC method handler index

legacy_service = JSONRPCService()
legacy_service.add(status, 'KBaseSearchEngine.status')
legacy_service.add(search_objects, 'KBaseSearchEngine.search_objects')
legacy_service.add(search_objects2, 'KBaseSearchEngine.search_objects2')
legacy_service.add(search_types, 'KBaseSearchEngine.search_types')
legacy_service.add(search_types2, 'KBaseSearchEngine.search_types2')
legacy_service.add(list_types, 'KBaseSearchEngine.list_types')
legacy_service.add(get_objects, 'KBaseSearchEngine.get_objects')
legacy_service.add(get_objects2, 'KBaseSearchEngine.get_objects2')


def handle(req_body, headers):
    """
    Handle a JSON RPC request body, making it backwards compatible with the previous Java API.
    """
    token = headers.get('authorization', None)
    return legacy_service.call(req_body, token)
