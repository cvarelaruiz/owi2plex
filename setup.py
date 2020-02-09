import os
from setuptools import setup


__version__ = ''
exec(open('./version.py').read())


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='OWi2Plex',
    version=__version__,
    scripts=['owi2plex.py', 'version.py'],
    install_requires=[
        'click==7.0',
        'requests==2.21.0',
        'lxml==4.3.2',
        'future==0.17.1',
        'pyyaml==5.1.2'
    ],
    #python_requires='>=3.6',
    author='Cristian Varela',
    author_email='cvarelaruiz@gmail.com',
    description='Exporter of EPG from OpenWebif to XMLTV to use with Plex',
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    license="MPL-2.0",
    keywords="plex openwebif xmltv",
    url="https://github.com/cvarelaruiz/owi2plex",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Topic :: Other/Nonlisted Topic"
    ],
    entry_points='''
        [console_scripts]
        owi2plex=owi2plex:main
    ''' 
)
