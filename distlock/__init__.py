import contextlib
import time

import consul
from six import string_types


DEFAULT_VERSION = 1
GLOBAL_PREFIX = 'distlock/key'


class DistLockException(Exception):

    def __init__(self, service_name, key, *args, **kwargs):
        self.service_name = service_name
        self.key = key
        super(DistLockException, self).__init__(*args, **kwargs)

    def __str__(self):
        return 'Lock acquisition failed. Service: {} Key: {}'.format(self.service_name, self.key)


class DistLockToken:
    """
    An object dispensed by a DistLockInterface's acquire() method
    that facilitates maintaining a lock-entry's state.
    """
    def __init__(self, key, acquired, session_id=None):
        self.key = key
        self.acquired = acquired
        self.session_id = session_id


class DistLockConsulInterface(object):
    """
    Interface to achieve distributed locking leveraging Consul.
    https://www.consul.io/docs/guides/semaphore.html
    """

    DEFAULT_SESSION_TTL = 30
    DEFAULT_SESSION_LOCK_DELAY = 5

    def __init__(self, consul_host, consul_port=8500, service_name=None):
        self.service_name = service_name or 'unspecified-service'
        self.connection = consul.Consul(consul_host, consul_port, 'http')

    def acquire_on_obj(self, obj, **kwargs):
        """
        Convenience method that facilitates ease of use
        when attempting to acquire a lock on a generic object.
        """
        key = self.get_key(obj)
        return self.acquire(key, **kwargs)

    def acquire(self, key, session_id=None, wait_seconds=0):
        """
        Attempt to acquire a lock for the given key.
        Utilize the provided session_id, or create one if not provided.
        If not acquired, retry for as long as the client is willing to wait.
        """

        if not session_id:
            session_id = self.create_session()

        acquired = self.connection.kv.put(key=key, value=None, acquire=session_id)

        if not acquired and wait_seconds:
            deadline = time.time() + wait_seconds
            while time.time() < deadline:
                acquired = self.connection.kv.put(key=key, value=None, acquire=session_id)
                if acquired:
                    break
                else:
                    time.sleep(float(1/3))

        return DistLockToken(key=key, acquired=acquired, session_id=session_id)

    def release(self, key, session_id, destroy_session=True):
        """
        Relinquish the provided session's lock on the specified key.
        Will destroy the session, by default.
        """

        self.connection.kv.put(key=key, value=None, release=session_id)

        if destroy_session:
            self.destroy_session(session_id)

    def get_key(self, obj, obj_class_name=None, obj_identifier=None, version=DEFAULT_VERSION):
        """
        Best effort attempt at serializing the provided obj into a standardized DistLock key.
        """
        if not obj_class_name:
            try:
                obj_class_name = obj.__class__.__name__
            except AttributeError:
                obj_class_name = str(obj)

        if not obj_identifier:
            if hasattr(obj, 'uuid'):
                obj_identifier = obj.uuid
            elif hasattr(obj, 'xid'):
                obj_identifier = obj.xid
            else:
                obj_identifier = obj if isinstance(obj, string_types) else repr(obj)

        key = '{}/v{}-{}-{}'.format(
            GLOBAL_PREFIX,
            version,
            obj_class_name,
            obj_identifier
        ).lower()

        return key

    def create_session(self, session_params=None):
        """
        Creates a Consul session, and returns the session id.
        """
        if session_params is None:
            session_params = {}

        # Warning: Consul only ensures a session isn't invalidated _before_ the TTL is reached.
        # The session's actual duration may be up to ~2x the specified TTL duration!
        # See GitHub issue: https://github.com/hashicorp/consul/issues/2966
        session_params.setdefault('ttl', self.DEFAULT_SESSION_TTL)
        session_params.setdefault('lock_delay', self.DEFAULT_SESSION_LOCK_DELAY)

        return self.connection.session.create(**session_params)

    def destroy_session(self, session_id):
        """
        Destroy a Consul session.
        """
        self.connection.session.destroy(session_id)

    @contextlib.contextmanager
    def lock_or_raise(self, obj, wait_seconds=0, exception=None, key_params=None):
        """
        Attempt to acquire a lock on an object.
        Utilize wait_seconds to specify how long you are willing to wait for a lock.
        If a lock acquisition fails, raise DistLockException if an exception is not specified.

        :param obj: Obj you want to acquire a lock on.
        :param wait_seconds: The duration of time you are willing to wait for a lock.
        :param exception: Custom exception you'd like raised if acquisition fails.
        :param key_params: Dictionary of custom fields you'd like to pass into get_key().
        """
        key_params = key_params or {}
        key = self.get_key(obj, **key_params)
        exception = exception or DistLockException(self.service_name, key)

        try:
            lock_token = self.acquire(key, wait_seconds=wait_seconds)
            if not lock_token.acquired:
                raise exception
        except Exception:
            raise exception

        yield lock_token

        self.release(lock_token.key, lock_token.session_id)
