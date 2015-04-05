import sys

import setuptools
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='Flask-aiohttp',
    version='0.1.0',
    packages=setuptools.find_packages(exclude=['flask_aiohttp.tests']),
    url='https://github.com/hardtack/flask-aiohttp',
    license='MIT LICENSE',
    author='Geonu Choi',
    author_email='6566gun@gmail.com',
    description="Asynchronous Flask using aiohttp",
    install_requires=[
        'aiohttp >= 0.15',
        'Flask >= 0.10.0',
    ],

    # Test
    test_requires=[
        'pytest',
        'websocket',
    ],

    # Cmd
    cmdclass={
        'test': PyTest,
    }
)
