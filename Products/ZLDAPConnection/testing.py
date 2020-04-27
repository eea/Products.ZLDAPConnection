# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

import Products.ZLDAPConnection


class ZLDAPConnectionLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=Products.ZLDAPConnection)


ZLDAPConnection_FIXTURE = ZLDAPConnectionLayer()

ZLDAPConnection_INTEGRATION_TESTING = IntegrationTesting(
    bases=(ZLDAPConnection_FIXTURE,),
    name='ZLDAPConnectionLayer:IntegrationTesting',
)
