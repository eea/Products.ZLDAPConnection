""" LDAP Server Connection Package
"""
from . import testing
from . import ZLDAP


def initialize(context):

    context.registerClass(
        ZLDAP.ZLDAPConnection,
        constructors=(ZLDAP.manage_addZLDAPConnectionForm,
                      ZLDAP.manage_addZLDAPConnection),
        icon='LDAP_conn_icon.gif',
        permissions=('Manage Entry information',
                     'Create New Entry Objects',
                     ),
    )

    context.registerClass(testing.ZLDAPConnectionLayer)
