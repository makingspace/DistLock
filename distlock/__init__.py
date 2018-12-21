import consul
import time

GLOBAL_PREFIX = 'distlock/key'


class DistLockConsulApp(object):

    def __init__(self, consul_host, consul_port):
        self.connection = consul.Consul(consul_host, consul_port, 'http')

    def acquire(self, key, session_id=None, wait_seconds=0):

        if session_id:
            session_created = False
        else:
            session_id = self._create_session()
            session_created = True

        acquired = self.connection.kv.put(key=key, value=None, acquire=session_id)

        if not acquired and wait_seconds:
            deadline = time.time() + wait_seconds
            while time.time() < deadline:
                acquired = self.connection.kv.put(key=key, value=None, acquire=session_id)
                if acquired:
                    break
                else:
                    time.sleep(float(1/3))

        if session_created:
            # Clean up the session we made.
            self._destroy_session(session_id)

        return (True, session_id) if acquired else (False, None)

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
        return self.connection.session.create(**session_params)

    def _destroy_session(self, session_id):
        self.connection.session.destroy(session_id)
