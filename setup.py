from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nibeuplink',
    version='0.7.1',
    description='A python wrapper around Nibe Uplink REST API',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    python_requires='>3.5',
    author='Joakim Plate',
    install_requires=[
        'asyncio',
        'aiohttp',
        'attrs>18.1',
        'cattrs',
    ],
    extras_require={
        'tests': [
            'pytest>3.6.4',
            'pytest-asyncio',
            'pytest-aiohttp',
            'pytest-cov<2.6',
            'coveralls'
        ]
    },
    entry_points = {
        'console_scripts' : ['nibeuplink=nibeuplink.console:main']
    },
    url='https://github.com/elupus/nibeuplink',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Plugins',
        'Framework :: AsyncIO',
    ]
)
