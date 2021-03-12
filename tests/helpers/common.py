import time


def wait_for_line(fname, predicate, timeout=10, line_count=1):
    f = open(fname, 'r')
    started = time.time()
    times = 0
    while True:
        if (time.time() - started) > timeout:
            f.close()
            return False
        line = f.readline()
        if not line or not line.endswith('\n'):
            time.sleep(0.1)
            continue
        if predicate(line):
            times = times + 1
            if times >= line_count:
                f.close()
                return True


def assert_jsonrpc20_result(actual, expected):
    assert actual['jsonrpc'] == '2.0'
    assert actual['id'] == expected['id']
    assert 'result' in actual
    result = actual['result']
    assert isinstance(result,  list)
    assert 'error' not in actual
    return result


def assert_jsonrpc20_error(actual, expected):
    assert actual['jsonrpc'] == '2.0'
    assert actual['id'] == expected['id']
    assert 'result' not in actual
    assert 'error' in actual
    error = actual['error']
    assert isinstance(error, dict)
    return error

def assert_jsonrpc11_result(actual, expected):
    assert actual['version'] == '1.1'
    if 'id' in actual:
        assert actual['id'] == expected['id']
    assert 'result' in actual
    result = actual['result']
    assert isinstance(result,  list)
    assert 'error' not in actual
    return result


def assert_jsonrpc11_error(actual, expected):
    assert actual['version'] == '1.1'
    if 'id' in actual:
        assert actual['id'] == expected['id']
    assert 'result' not in actual
    assert 'error' in actual
    error = actual['error']
    assert isinstance(error, dict)
    return error


def equal(d1, d2, path=[]):
    if isinstance(d1, dict):
        if isinstance(d2, dict):
            d1_keys = set(d1.keys())
            d2_keys = set(d2.keys())
            if len(d1_keys.difference(d2_keys)) > 0:
                return [False, path]
            for key in d1_keys:
                path.append(key)
                if not equal(d1[key], d2[key], path):
                    return [False, path]
                path.pop()

            return [True, path]
        else:
            return [False, path]
    elif isinstance(d1, list):
        if isinstance(d2, list):
            if len(d1) != len(d2):
                return [False, path]
            i = 0
            for d1value, d2value in zip(d1, d2):
                i += 1
                path.append(i)
                if not equal(d1value, d2value, path):
                    return [False, path]
            return [True, path]
    else:
        return [d2 == d1, path]
