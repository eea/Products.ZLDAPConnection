""" LDAP Server Connection Package
"""
from . import ZLDAP


def initialize(context):
    """initialize.

    :param context:
    """

    context.registerClass(
        ZLDAP.ZLDAPConnection,
        constructors=(ZLDAP.manage_addZLDAPConnectionForm,
                      ZLDAP.manage_addZLDAPConnection),
        icon='LDAP_conn_icon.gif',
        permissions=('Manage Entry information',
                     'Create New Entry Objects',
                     ),
    )
