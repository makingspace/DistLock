## DistLock

A Python client library to implement distributed locking.
Allows distributed projects and applications to acquire locks on
generic resources via a common locking backend.

# Backends

### Consul by HashiCorp
   [Consul](https://www.consul.io/):
    
    Consul is a distributed service mesh to connect, secure,
    and configure services across any runtime platform and public
    or private cloud.

Consul was purpose build to make distributed systems more cohesive,
and it provides native locking support.

##### Usage
You can manually interact with the DistLockConsulInterface methods
such as `acquire()` and `release()`, but you'll likely find the `lock_or_raise()`
context manager a convenient alternative.


### Redis (Coming Soon)
[Redis](https://redis.io/)

    Redis is an open source (BSD licensed), in-memory data structure store,
    used as a database, cache and message brokerRedis is an open source
    (BSD licensed), in-memory data structure store, used as a database,
    cache and message broker. 

Redis provides a flexible key-value store that can be leveraged to
facilitate distributed locking.

