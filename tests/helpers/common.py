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
