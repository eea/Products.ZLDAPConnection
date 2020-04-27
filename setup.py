from setuptools import setup, find_packages
from os.path import join

NAME = 'Products.ZLDAPConnection'
PATH = NAME.split('.') + ['version.txt']
VERSION = open(join(*PATH)).read().strip()

setup(name=NAME,
      version=VERSION,
      long_description_content_type="text/x-rst",
      long_description=open("README.rst").read() + "\n" + open(
          join("docs", "HISTORY.txt")).read(),
      description="ZLDAPConnection Product",
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python",
          "Framework :: Zope :: 2",
          "Framework :: Plone :: 5.1",
          "License :: OSI Approved :: GNU General Public License (GPL)",
      ],
      keywords='',
      author='European Environment Agency: IDM2 A-Team',
      author_email='eea-edw-a-team-alerts@googlegroups.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Zope',
      ],
      )
