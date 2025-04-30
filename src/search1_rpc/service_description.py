class ServiceDescription(object):
    def __init__(self, name, id, version=None, summary=None):
        self.name = name
        self.id = id
        self.version = version
        self.summary = summary

    def to_json(self):
        data = {
            'sdversion': '1.0',
            'name': self.name,
            'id': self.id
        }
        if (self.version is not None):
            data['version'] = self.version

        if (self.summary is not None):
            data['summary'] = self.summary

        return data
