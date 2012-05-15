import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-roxy",
    version = "0.2.5",
    author = "Proteus Technologies Development team",
    author_email = "infrastructure@proteus-tech.com",
    description = ("Simple reverse proxy for Django"),
    long_description = read('readme.txt'),
    license = "Boost Software License - Version 1.0 - August 17th, 2003",
    keywords = "reverse proxy roxy django",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Boost Software License - Version 1.0 - August 17th, 2003",
    ],
    packages = ['roxy', 'roxy.tests'],
    install_requires = ['httplib2', 'urlobject'],
)

