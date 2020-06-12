""" Doc tests
"""
import doctest
import unittest
from Products.ZLDAPConnection.testing import FUNCTIONAL_TESTING
from plone.testing import layered

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


def test_suite():
    """ Suite
    """
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                'README.txt',
                optionflags=OPTIONFLAGS,
                package='Products.ZLDAPConnection'),
            layer=FUNCTIONAL_TESTING),
    ])
    return suite
