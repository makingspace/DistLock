from setuptools import setup

setup(
    name='DistLock',
    version='0.1.0',
    packages=['distlock'],
    description='Distributed Locking Service',
    url='https://github.com/makingspace/Distlock',
    long_description='Distributed Locking Service',
    install_requires=[
        'consul_kv'
    ],
    tests_require=[
        'python-consul',
        'mock',
        'pytest',
    ]
)
