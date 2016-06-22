import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-lock-tokens',
    version='0.1',
    packages=['lock_tokens'],
    include_package_data=True,
    description='A Django application that provides a locking mechanism to prevent concurrency editing.',
    long_description=README,
    author='VisionMark',
    author_email='visionmark@visionmark-group.com',
)
