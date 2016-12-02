import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-lock-tokens',
    version='0.1.3',
    packages=['lock_tokens'],
    include_package_data=True,
    description='A Django application that provides a locking mechanism to prevent concurrency editing.',
    long_description=README,
    author='Renaud Parent',
    author_email='renaud.parent@gmail.com',
    url='https://github.com/rparent/django-lock-tokens',
    license='MIT',
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Topic :: Software Development :: Libraries :: Application Frameworks',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.6',
      'Programming Language :: Python :: 2.7',
      'Framework :: Django',
      'Framework :: Django :: 1.7',
      'Framework :: Django :: 1.8',
      'Framework :: Django :: 1.9',
    ],
    keywords='django concurrent editing lock locking tokens'
)
