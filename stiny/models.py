""" DynamoDB models. """

from datetime import datetime
from flywheel import Model, Field


class UserPerm(Model):

    """
    A permission grant for a user within a time period.

    Parameters
    ----------
    email : str
        User email. Must be gmail so they can do the G+ signin.
    start : :class:`~datetime.datetime`
        The datetime that the permissions are granted.
    end : :class:`~datetime.datetime`
        The datetime that the permissions are revoked.
    perms : set
        Set of permissions to be granted.

    """

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

    """
    Stored application state.

    Parameters
    ----------
    name : str
        Name of the state being stored.
    start : :class:`~datetime.datetime`, optional
        Starting datetime of the state, if the state is scheduled. If not, then
        this will be the beginning of time.
    end : :class:`~datetime.datetime`, optional
        Ending datetime of the state, if the state is scheduled.

    """

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
