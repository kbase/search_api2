def list_types(auth):
    """
    List registered searchable object types.
    params:
        type_name - string - optional - specify the type to get a count for
    if type_name not specified, then all types are counted
    output:
        types - dict - type name mapped to dicts of:
            type_name - string
            type_ui_title - string
            keys - list of dicts - "searchable type keyword"
                dicts are:
                    key_name - string
                    key_ui_title - string
                    key_value_title - string
                    hidden - bool
                    link_key - string
    For now, we're leaving this as a no-op, because we haven't seen this in use
    in KBase codebases anywhere.
    """
    return {}
