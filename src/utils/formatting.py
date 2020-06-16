import datetime


def iso8601_to_epoch(time_string):
    return round(datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S%z').timestamp())
