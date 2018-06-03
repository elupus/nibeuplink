from setuptools import setup, find_packages

setup(
    name='nibeuplink',
    version='0.3.1',
    description='A python wrapper around Nibe Uplink REST API',
    license='MIT',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>3.5',
    install_requires=[
        'asyncio',
        'aiohttp',
    ],
    tests_require=[
        'pytest',
        'pytest-asyncio',
        'pytest-aiohttp',
    ],
    entry_points = {
        'console_scripts' : ['nibeuplink=nibeuplink.console:main']
    }
)