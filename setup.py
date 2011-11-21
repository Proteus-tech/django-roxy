import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-roxy",
    version = "0.1.9",
    author = "Proteus Technologies Infrastructure team",
    author_email = "infrastructure@proteus-tech.com",
    description = ("Simple reverse proxy for Django"),
#    long_description = read('README.markdown'),
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
    install_requires = ['httplib2'],
)

