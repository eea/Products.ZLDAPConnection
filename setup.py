from setuptools import setup, find_packages

NAME = 'Products.ZLDAPConnection'
VERSION = '1.0'

setup(name=NAME,
      version=VERSION,
      description="ZLDAPConnection Product",
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
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
      ],
)
