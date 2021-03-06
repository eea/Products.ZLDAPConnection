"""
   An LDAP connection product.  Depends on David Leonard's ldapmodule.
   $Id: ZLDAP.py 41317 2018-04-27 07:35:48Z dumitval $
   Started by Anthony Baxter, <anthony@interlink.com.au>
   Continued by the folks @ CodeIt <http://www.codeit.com/>

   Now by Jeffrey P Shell <jeffrey@Digicool.com>.
"""
# pylint: disable=no-init,old-style-class,too-many-public-methods
# pylint: disable=too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-function-args
import time
import six.moves.urllib.request
import six.moves.urllib.parse
import six.moves.urllib.error
import ldap
import Acquisition
import OFS
from Persistence import Persistent
from App.Dialogs import MessageDialog
from App.special_dtml import HTMLFile

from . import LDCAccessors
from .Entry import ZopeEntry, GenericEntry, TransactionalEntry

ConnectionError = 'ZLDAP Connection Error'

manage_addZLDAPConnectionForm = HTMLFile('add', globals())


class NoBrainer:
    """ Empty class for mixin to EntryFactory """


class ZLDAPConnection(Acquisition.Implicit, Persistent, OFS.SimpleItem.Item,
                      LDCAccessors.LDAPConnectionAccessors,
                      OFS.role.RoleManager):
    '''LDAP Connection Object'''

    isPrincipiaFolderish = 1

    meta_type = 'LDAP Connection'
    zmi_icon = 'fa fa-server'

    manage_options = (
        {'label': 'Connection Properties', 'action': 'manage_main'},
        {'label': 'Open/Close', 'action': 'manage_connection'},
        {'label': 'Browse', 'action': 'manage_browse'},
        {'label': 'Security', 'action': 'manage_access'},
    )

    __ac_permissions__ = (
        ('Access contents information',
         ('canBrowse',),),
        ('View management screens', ('manage_tabs', 'manage_main'),
         ('Manager',)),
        ('Edit connection', ('manage_edit',), ('Manager',)),
        ('Change permissions', ('manage_access',)),
        ('Open/Close Connection', ('manage_connection',
                                   'manage_open', 'manage_close',),
         ('Manager',)),
        ('Browse Connection Entries', ('manage_browse',), ('Manager',),),
    )

    manage_browse = HTMLFile('browse', globals())
    manage_connection = HTMLFile('connection', globals())

    # dealing with browseability on the root.
    def canBrowse(self):
        """ Returns true if the connection is open *and* the '_canBrowse'
        property is set to true """
        return self.shouldBeOpen() and self.getBrowsable()

    # constructor
    def __init__(self, ob_id, title, host, port, basedn, bind_as, pw, openc,
                 transactional=1):
        "init method"
        self._v_conn = None
        self._v_delete = []
        self._v_openc = 0

        self.setId(ob_id)
        self.setTitle(title)
        self.setHost(host)
        self.setPort(port)
        self.setBindAs(bind_as)
        self.setPW(pw)
        self.setDN(basedn)
        self.setOpenConnection(openc)
        self.setTransactional(transactional)

        # if connection is specified to be open, open it up
        if openc:
            self._open()

    # upgrade path...
    def __setstate__(self, state):
        # Makes sure we have an Entry class now
        self._refreshEntryClass()
        Persistent.__setstate__(self, state)
        self._v_conn = None
        self._v_delete = []
        self._v_openc = 0

    # Entry Factory stuff
    def _refreshEntryClass(self):
        """ This class sets up the Entry class used to return results. """
        transactional = self.getTransactional()
        if transactional:
            EntryBase = TransactionalEntry
        else:
            EntryBase = GenericEntry

        class LdapEntry(EntryBase, ZopeEntry):
            """LdapEntry."""

            pass

        self._v_entryclass = LdapEntry
        return LdapEntry

    def _EntryFactory(self):
        """ Stamps out an Entry class to be used for every entry returned,
        taking into account transactional versus non-transactional """
        return getattr(self, '_v_entryclass', self._refreshEntryClass())

    # Tree stuff
    def __bobo_traverse__(self, REQUEST, key):
        """__bobo_traverse__.

        :param REQUEST:
        :param key:
        """
        key = six.moves.urllib.parse.unquote(key)
        if hasattr(self, key):
            return getattr(self, key)
        return self.getRoot()[key]

    def tpId(self):
        """tpId."""
        return self.id

    def tpURL(self):
        """tpURL."""
        return self.id

    def tpValues(self):
        """tpValues."""
        if self.canBrowse():
            return self.getRoot().tpValues()
        return []

    # TransactionalObjectManager stuff #####
    def tpc_begin(self, *ignored):
        """tpc_begin.

        :param ignored:
        """
        # make sure we're open!
        if not self.__ping():      # we're not open
            raise ConnectionError
        self._v_okobjects = []

    def commit(self, o, *ignored):
        ''' o = object to commit '''
        # check to see if object exists
        oko = []
        if self.hasEntry(o.dn):
            oko.append(o)
        elif o._isNew or o._isDeleted:
            oko.append(o)
        self._v_okobjects = oko

    def tpc_finish(self, *ignored):
        " really really commit and DON'T FAIL "
        oko = self._v_okobjects
        self._isCommitting = 1
        d = getattr(self, '_v_delete', [])

        for deldn in d:
            self._deleteEntry(deldn)
        self._v_delete = []

        for o in oko:
            try:
                if o._isDeleted:
                    pass
                    # we shouldn't need to do anything now that
                    # the mass delete has happened
                elif o._isNew:
                    self._addEntry(o.dn, list(o._data.items()))
                    o._isNew = 0
                    del self._v_add[o.dn]
                else:
                    o._modify()
                o._registered = 0
            except Exception:
                pass    # X X X We should log errors here

        del self._v_okobjects
        del self._isCommitting
        self.GetConnection().destroy_cache()

    def tpc_abort(self, *ignored):
        " really really rollback and DON'T FAIL "
        try:
            self._abort()
        except Exception:
            pass        # X X X We should also log errors here

    def abort(self, o, *ignored):
        """abort.

        :param o:
        :param ignored:
        """
        if o.dn in getattr(self, '_v_delete', ()):
            self._v_delete.remove(o.dn)
        if o._isDeleted:
            o.undelete()
        o._rollback()
        o._registered = 0
        if o._isNew:
            if o.dn in list(getattr(self, '_v_add', {}).keys()):
                del self._v_add[o.dn]
        self.GetConnection().destroy_cache()

    def _abort(self):
        """_abort."""
        oko = self._v_okobjects
        for o in oko:
            self.abort(o)
        self.GetConnection().destroy_cache()

    def tpc_vote(self, *ignored):
        """tpc_vote.

        :param ignored:
        """
        pass

    # getting entries and attributes
    def hasEntry(self, dn):
        """hasEntry.

        :param dn:
        """
        if dn in getattr(self, '_v_add', {}):
            # object is marked for adding
            return 1
        elif dn in getattr(self, '_v_delete', ()):
            # object is marked for deletion
            return 0

        try:
            e = self._connection().search_s(dn, ldap.SCOPE_BASE,
                                            'objectclass=*')
            if e:
                return 1
        except ldap.NO_SUCH_OBJECT:
            return 0
        return 0

    def getRawEntry(self, dn):
        " return raw entry from LDAP module "
        if dn in getattr(self, '_v_add', {}):
            return (dn, self._v_add[dn]._data)
        elif dn in getattr(self, '_v_delete', ()):
            raise ldap.NO_SUCH_OBJECT("Entry '%s' has been deleted" % dn)

        try:
            e = self._connection().search_s(
                dn, ldap.SCOPE_BASE, 'objectclass=*'
            )
            if e:
                return e[0]
        except Exception:
            raise ldap.NO_SUCH_OBJECT("Cannot retrieve entry '%s'" % dn)

    def getEntry(self, dn, o=None):
        " return **unwrapped** Entry object, unless o is specified "
        Entry = self._EntryFactory()

        if dn in getattr(self, '_v_add', {}):
            e = self._v_add[dn]
        else:
            e = self.getRawEntry(dn)
            e = Entry(e[0], e[1], self)

        if o is not None:
            return e.__of__(o)
        return e

    def getRoot(self):
        " return root entry object "
        return self.getEntry(self.dn, self)

    def getAttributes(self, dn):
        " get raw attributes from entry from LDAP module "
        return self.getRawEntry(dn)[1]

    # listing subentries

    def getRawSubEntries(self, dn):
        " get the raw entry objects of entry dn's immediate children "
        # X X X Do something soon to account for added but noncommited..?
        if dn in getattr(self, '_v_delete', ()):
            raise ldap.NO_SUCH_OBJECT
        results = self._connection().search_s(
            dn, ldap.SCOPE_ONELEVEL, 'objectclass=*')
        r = []
        for entry in results:
            # make sure that the subentry isn't marked for deletion
            if entry[0] not in getattr(self, '_v_delete', ()):
                r.append(entry)
        return r

    def getSubEntries(self, dn, o=None):
        """getSubEntries.

        :param dn:
        :param o:
        """
        Entry = self._EntryFactory()

        r = []
        se = self.getRawSubEntries(dn)

        for entry in se:
            e = Entry(entry[0], entry[1], self)
            if o is not None:
                e = e.__of__(o)
            r.append(e)

        return r

    # modifying entries
    def _modifyEntry(self, dn, modlist):
        """_modifyEntry.

        :param dn:
        :param modlist:
        """
        if not getattr(self, '_isCommitting', 0):
            raise AttributeError('Cannot modify unless in a commit')
            # someone's trying to be sneaky and modify an object
            # outside of a commit.  We're not going to allow that!
        c = self._connection()
        c.modify_s(dn, modlist)

    # deleting entries
    def _registerDelete(self, dn):
        " register DN for deletion "
        d = getattr(self, '_v_delete', [])
        if dn not in d:
            d.append(dn)
        self._v_delete = d

    def _unregisterDelete(self, dn):
        " unregister DN for deletion "
        d = getattr(self, '_v_delete', [])
        if dn in d:
            d.remove(dn)
        self._v_delete = d

        self._unregisterAdd(dn)

    def _deleteEntry(self, dn):
        """_deleteEntry.

        :param dn:
        """
        if not getattr(self, '_isCommitting', 0):
            raise AttributeError('Cannot delete unless in a commit')
        c = self._connection()
        c.delete_s(dn)

    # adding entries
    def _registerAdd(self, o):
        """_registerAdd.

        :param o:
        """
        a = getattr(self, '_v_add', {})
        if o.dn not in a:
            a[o.dn] = o
        self._v_add = a

    def _unregisterAdd(self, o=None, dn=None):
        """_unregisterAdd.

        :param o:
        :param dn:
        """
        a = getattr(self, '_v_add', {})
        if o and o in list(a.values()):
            del a[o.dn]
        elif dn and dn in a:
            del a[dn]
        self._v_add = a

    def _addEntry(self, dn, attrs):
        """_addEntry.

        :param dn:
        :param attrs:
        """
        if not getattr(self, '_isCommitting', 0):
            raise AttributeError('Cannot add unless in a commit')
        c = self._connection()
        c.add_s(dn, attrs)

    # other stuff
    def title_and_id(self):
        "title and id, with conn state"
        s = ZLDAPConnection.inheritedAttribute('title_and_id')(self)
        if self.shouldBeOpen():
            s = "%s (connected)" % s
        else:
            s = '%s (<font color="red"> not connected</font>)' % s
        return s

    # connection checking stuff
    def _connection(self):
        """_connection."""
        if self.openc:
            if not self.isOpen():
                self._open()
            return self._v_conn
        else:
            raise ConnectionError

    GetConnection = _connection

    def isOpen(self):
        """ quickly checks to see if the connection's open
            Reopen if connection older than 5 minutes
        """
        if not hasattr(self, '_v_conn'):
            self._v_conn = None
        now = int(time.time())
        if self._v_openc < now - 300:
            return 0
        if self._v_conn is None or not self.shouldBeOpen():
            return 0
        return 1

    def __ping(self):
        " more expensive check on the connection and validity of conn "
        try:
            self._connection().search_s(self.dn, ldap.SCOPE_BASE,
                                        'objectclass=*')
            return 1
        except Exception:
            self._close()
            return 0

    def _open(self):
        """ open a connection """
        try:
            self._close()
        except Exception:
            pass
        self._v_conn = ldap.initialize('ldaps://%s:%s' % (self.host,
                                                          self.port))
        try:
            self._v_conn.whoami_s()
        except ldap.SERVER_DOWN:
            self._v_conn = ldap.initialize(
                'ldap://%s:%s' % (self.host, self.port))
        try:
            self._v_conn.simple_bind_s(self.bind_as, self.pw)
        except ldap.NO_SUCH_OBJECT:
            return """
   Error: LDAP Server returned `no such object' for %s. Possibly
   the bind string or password are incorrect""" % (self.bind_as)
        self._v_openc = int(time.time())

    def manage_open(self, REQUEST=None):
        """ open a connection. """
        self.setOpenConnection(1)
        ret = self._open()
        if not getattr(self, '_v_openc', 0):
            return ret
        if REQUEST is not None:
            m = 'Connection has been opened.'
            return self.manage_connection(self, REQUEST, manage_tabs_message=m)

    def _close(self):
        """ close a connection """
        if self.getOpenConnection() == 0:
            # I'm already closed, but someone is still trying to close me
            self._v_conn = None
            self._v_openc = 0
        else:
            try:
                self._v_conn.unbind_s()
            except AttributeError:
                pass
            self._v_conn = None
            self._v_openc = 0

    def manage_close(self, REQUEST=None):
        """ close a connection. """
        self._close()
        if REQUEST is not None:
            m = 'Connection has been closed.'
            return self.manage_connection(self, REQUEST, manage_tabs_message=m)

    def manage_clearcache(self, REQUEST=None):
        """ clear the cache """
        self._connection().destroy_cache()
        if REQUEST is not None:
            m = 'Cache has been cleared.'
            return self.manage_connection(self, REQUEST, manage_tabs_message=m)

    manage_main = HTMLFile("edit", globals())

    def manage_edit(self, title, hostport, basedn, bind_as, pw, openc=0,
                    canBrowse=0, transactional=1, REQUEST=None):
        """ handle changes to a connection """
        self.title = title
        host, port = splitHostPort(hostport)
        if self.host != host:
            self._close()
            self.setHost(host)
        if self.port != port:
            self._close()
            self.setPort(port)
        if self.bind_as != bind_as:
            self._close()
            self.setBindAs(bind_as)
        if self.pw != pw:
            self._close()
            self.setPW(pw)
        if openc and not self.getOpenConnection():
            self.setOpenConnection(1)
            ret = self._open()
            if not self._v_openc:
                return ret
        if not openc and self.getOpenConnection():
            self.setOpenConnection(0)
            self._close()

        self.setBrowsable(canBrowse)
        self.setTransactional(transactional)
        self.setDN(basedn)

        if REQUEST is not None:
            return MessageDialog(
                title='Edited',
                message='<strong>%s</strong> has been edited.' % self.id,
                action='./manage_main',
            )

#    def GetConnection(self):
#      "return connection object"
#      if not self.openc:
#          raise "LDAPConnectionError", "LDAP connection not open"
#      else:
#          if not hasattr(self, '_v_conn'):
#              self._open()
#          return self._v_conn

    def _isAnLDAPConnection(self):
        """_isAnLDAPConnection."""
        return 1


def splitHostPort(hostport):
    """splitHostPort.

    :param hostport:
    """
    hp_list = str.split(hostport, ':')
    host = hp_list[0]
    if len(hp_list) == 1:
        port = 389
    else:
        port = int(hp_list[1])
    return host, port


def manage_addZLDAPConnection(self, c_id, title, hostport,
                              basedn, bind_as, pw, openc,
                              REQUEST=None):
    """create an LDAP connection and install it"""
    host, port = splitHostPort(hostport)
    conn = ZLDAPConnection(c_id, title, host, port, basedn, bind_as, pw, openc)
    self._setObject(c_id, conn)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)
