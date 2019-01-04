import collections
import mock
import pytest

from distlock import GLOBAL_PREFIX, DistLockConsulInterface, DistLockToken


MOCK_OBJ_CLASS_NAME = 'MyTestClass'
MOCK_OBJ_XID = 'my-xid'


@pytest.fixture
def mock_obj():
    MockObj = collections.namedtuple(MOCK_OBJ_CLASS_NAME, ['xid'])
    return MockObj(MOCK_OBJ_XID)


@pytest.fixture
def consul_lock():
    consul_lock = DistLockConsulInterface('fake-host', service_name='fake-service')
    consul_lock.connection = mock.MagicMock()
    return consul_lock


def test_get_key(mock_obj, consul_lock):
    """
    Verify our key generation logic.
    """
    v = 1  # version
    objects = [mock_obj, 1, {'my_mock_key': 'my_mock-value'}]
    for obj in objects:
        obj_identifier = getattr(obj, 'xid', repr(obj))
        expected_key = '{}/v{}-{}-{}-{}'.format(
            GLOBAL_PREFIX, v, consul_lock.service_name, obj.__class__.__name__, obj_identifier
        )
        actual_key = consul_lock.get_key(obj, version=v)
        assert expected_key == actual_key
        v += 1


def test_acquire_on_obj(mock_obj, consul_lock):
    """
    Verify acquire_on_obj() subsequently calls acquire() on the provided obj's key.
    """

    consul_lock.acquire = mock.MagicMock()
    consul_lock.acquire_on_obj(mock_obj)

    consul_lock.acquire.assert_called_once_with(consul_lock.get_key(mock_obj))


def test_acquire(consul_lock):
    """
    Verify basic lock acquisition behavior.
    """

    expected_sessions_created = 0
    consul_lock.create_session = mock.MagicMock()
    outcomes = [True, False]

    for outcome in outcomes:
        consul_lock.connection.kv.put.return_value = outcome
        lock_token = consul_lock.acquire('my_key')
        assert isinstance(lock_token, DistLockToken)
        assert lock_token.acquired == outcome

        expected_sessions_created += 1
        assert consul_lock.create_session.call_count == expected_sessions_created


def test_release(consul_lock):
    """
    Verify fundamental lock release behavior.
    """
    k = 'my_locked_key'
    session_id = '123'
    consul_lock.connection.kv.put = mock.MagicMock()
    consul_lock.destroy_session = mock.MagicMock()
    expected_destroy_count = 0
    destroy_options = [True, False]

    for destroy_option in destroy_options:
        consul_lock.release(k, session_id, destroy_session=destroy_option)
        consul_lock.connection.kv.put.assert_called_once_with(key=k, value=None, release=session_id)
        consul_lock.connection.kv.put.reset_mock()
        if destroy_option:
            expected_destroy_count += 1
        assert consul_lock.destroy_session.call_count == expected_destroy_count
