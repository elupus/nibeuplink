from setuptools import setup, find_packages

setup(
    name='nibeuplink',
    version='0.5.0',
    description='A python wrapper around Nibe Uplink REST API',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    python_requires='>3.5',
    author='Joakim Plate',
    install_requires=[
        'asyncio',
        'aiohttp',
    ],
    extras_require={
        'tests': [
            'pytest',
            'pytest-asyncio',
            'pytest-aiohttp',
            'pytest-cov',
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
