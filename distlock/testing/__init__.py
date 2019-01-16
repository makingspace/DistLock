from distlock import DistLockConsulInterface

try:
    # Python 2
    import mock
except ImportError:
    # Python 3
    from unittest import mock


class TestDistLockConsulInterface(DistLockConsulInterface):

    """
    Mocked class for interacting with DistLockConsulInterface in a testing context.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = mock.MagicMock()
