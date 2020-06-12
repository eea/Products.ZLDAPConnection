# -*- coding: utf-8 -*-
''' testing module - defining layers '''
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import FunctionalTesting
from plone.app.testing import PLONE_FIXTURE


class EEAFixture(PloneSandboxLayer):
    """ EEA Testing Policy
    """
    defaultBases = (PLONE_FIXTURE,)


FIXTURE = EEAFixture()
FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE,), name='ZLDAPConnection:Functional')
