from setuptools import setup

setup(
    name='dist-lock',
    version='0.2.0',
    packages=['distlock'],
    description='Distributed Locking Service',
    url='https://github.com/makingspace/Distlock',
    long_description='Distributed Locking Service',
    install_requires=[
        'consul_kv',
        'python-consul==1.0.1'
    ],
    tests_require=[
        'python-consul==1.0.1',
        'mock',
        'pytest',
    ]
)
