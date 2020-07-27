from src.utils.obj_utils import get_path, get_any


def test_get_path_valid():
    obj = {'x': {'y': [1, {'z': 'hi'}]}}
    res = get_path(obj, ['x', 'y', 1, 'z'])
    assert res == 'hi'


def test_get_path_none():
    obj = {'x': {'y': [1, {'z': 'hi'}]}}
    res = get_path(obj, ['x', 'z'])
    assert res is None


def test_get_any_valid():
    obj = {'x': 0, 'y': 1, 'z': 2}
    res = get_any(obj, ['x', 'q'])
    assert res == 0


def test_get_any_valid2():
    obj = {'x': 0, 'y': 1, 'z': 2}
    res = get_any(obj, ['q'], 'hi')
    assert res == 'hi'


def test_get_any_valid3():
    obj = {'x': 0, 'y': 1, 'z': 2}
    res = get_any(obj, ['q', 'y', 'z'], 'hi')
    assert res == 1
