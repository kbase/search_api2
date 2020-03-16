# from src.validation.validation import Validation
# validation = Validation(load_schemas=True)


def status(auth):
    """
    Example status response from the Java API:
    [{
        "state": "OK",
        "message":"",
        "version":"0.2.2-dev1",
        "git_url":"https://github.com/kbase/KBaseSearchEngine.git",
        "git_commit_hash":"1935768d49d0fe6032a1195de10156d9f319d8ce"}]
    }]
    """
    # TODO: the version should be taken from the config
    #       In kb-sdk this is generated at compile time; we need
    #       to mimic that.
    return {
        'state': 'OK',
        'version': '0.1.1',
        'message': '',
        'git_url': '',
        'git_commit_hash': ''
    }
