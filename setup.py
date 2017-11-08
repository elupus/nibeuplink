from setuptools import setup, find_packages

setup(
	name='nibe-uplink',
	version='0.1',
	description='A python wrapper around Nibe Uplink REST API',
	license='MIT',
	packages=find_packages(exclude=['contrib', 'docs', 'tests'])
)