import consul
import time

GLOBAL_PREFIX = 'distlock/key'


class DistLockToken:
    """
    An object dispensed by a DistLockConsulInterface's acquire() method
    that facilitates maintaining a lock-entry's state.
    """
    def __init__(self, key, acquired, session_id=None):
        self.key = key
        self.acquired = acquired
        self.session_id = session_id


class DistLockConsulInterface(object):

    DEFAULT_SESSION_TTL = 30
    DEFAULT_SESSION_LOCK_DELAY = 5

    def __init__(self, consul_host, consul_port):
        self.connection = consul.Consul(consul_host, consul_port, 'http')

    def acquire_on_obj(self, obj, **kwargs):
        key = self.get_key(obj)
        return self.acquire(key, **kwargs)

    def acquire(self, key, session_id=None, wait_seconds=0):

        if not session_id:
            session_id = self._create_session()

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

        self.connection.kv.put(key=key, value=None, release=session_id)

        if destroy_session:
            self._destroy_session(session_id)

    def get_key(self, obj, version=1):
        """
        Utility for clients to have
        """
        try:
            class_name = obj.__class__.__name__
        except AttributeError:
            class_name = str(obj)

        try:
            obj_identifier = obj.xid
        except AttributeError:
            obj_identifier = repr(obj)

        return '{}/v{}-{}-{}'.format(GLOBAL_PREFIX, version, class_name, obj_identifier)

    def _create_session(self, session_params=None):
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

    def _destroy_session(self, session_id):
        self.connection.session.destroy(session_id)
