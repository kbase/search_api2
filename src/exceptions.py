

class Search2Error(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class UnknownIndex(Search2Error):
    pass
