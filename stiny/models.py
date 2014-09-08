from datetime import datetime
from flywheel import Model, Field


class UserPerm(Model):
    __metadata__ = {
        'throughput': {
            'read': 1,
            'write': 1,
        }
    }
    email = Field(hash_key=True)
    start = Field(range_key=True, data_type=datetime)
    end = Field(data_type=datetime)
    perms = Field(data_type=frozenset([str]))

    def __init__(self, email, start, end, perms):
        self.email = email
        self.start = start
        self.end = end
        self.perms = perms

    def __json__(self, request=None):
        data = super(UserPerm, self).__json__(request)
        data['perms'] = list(self.perms)
        return data


class State(Model):
    __metadata__ = {
        'throughput': {
            'read': 1,
            'write': 1,
        }
    }
    name = Field(hash_key=True)
    start = Field(range_key=True, data_type=datetime)
    end = Field(data_type=datetime)

    def __init__(self, name, start=datetime.utcfromtimestamp(0), end=None):
        self.name = name
        self.start = start
        self.end = end
