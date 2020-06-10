''' LDC Accessors module '''
# pylint: disable=too-many-instance-attributes
__version__ = "$Revision: 1.1 $"[11:-2]


class LDAPConnectionAccessors(object):
    """ getters / setters for LDAP Properties """

    __ac_permissions__ = (
        ('Access contents information',
         ('getId', 'getTitle', 'getHost', 'getPort', 'getBindAs', 'getBoundAs',
          'getPW', 'getDN', 'getOpenConnection', 'getBrowsable',
          'shouldBeOpen', 'getTransactional',),),
        ('Manage properties',
         ('setID', 'setTitle', 'setHost', 'setPort', 'setBindAs', 'setPW',
          'setDN', 'setOpenConnection', 'setBrowsable', 'setBoundAs',
          'setTransactional',),),
    )

    def getId(self):
        """getId."""
        return self.id

    def setId(self, ob_id):
        """setId.

        :param id:
        """
        self.id = ob_id

    def getTitle(self):
        """getTitle."""
        return self.title

    def setTitle(self, title):
        """setTitle.

        :param title:
        """
        self.title = title

    def getHost(self):
        """ returns the host that this connection is connected to """
        return self.host

    def setHost(self, host):
        """setHost.

        :param host:
        """
        self.host = host

    def getPort(self):
        """ returns the port on the host that this connection connects to """
        return self.port

    def setPort(self, port):
        """setPort.

        :param port:
        """
        self.port = port

    def getBindAs(self):
        """ return the DN that this connection is bound as """
        return self.bind_as
    getBoundAs = getBindAs

    def setBindAs(self, bindAs):
        """setBindAs.

        :param bindAs:
        """
        self.bind_as = bindAs
    setBoundAs = setBindAs

    def getPW(self):
        """ return the password that this connection is connected with """
        return self.pw

    def setPW(self, pw):
        """setPW.

        :param pw:
        """
        self.pw = pw

    def getDN(self):
        """getDN."""
        return self.dn

    def setDN(self, dn):
        """setDN.

        :param dn:
        """
        self.dn = dn

    def getOpenConnection(self):
        """ self.openc means that the connection is open to Zope.  However,
        the connection to the LDAP server may or may not be opened.  If
        this returns false, we shouldn't even try connecting."""
        return self.openc

    def setOpenConnection(self, openc):
        """setOpenConnection.

        :param openc:
        """
        self.openc = openc

    shouldBeOpen = getOpenConnection

    def getBrowsable(self):
        """ if true, connection object is set to be browsable through the
        management interface """
        return getattr(self, '_canBrowse', 0)

    def setBrowsable(self, browsable):
        """setBrowsable.

        :param browsable:
        """
        self._canBrowse = browsable

    def getTransactional(self):
        """ If transactional returns TRUE, the TransactionManager stuff
        is used.  If FALSE, changes are sent to LDAP immediately. """
        # Default to '1', to emulate the original behavior
        return getattr(self, 'isTransactional', 1)

    def setTransactional(self, transactional=1):
        ''' We have a fair amount of transaction-sensitive methods that
        only want to run during a commit, and these are the ones that
        actually send the data to the LDAP server.  When in non-transactional
        mode, we want these things to run at any time.  In a sense, we're
        always committing.'''
        self.isTransactional = transactional
        self._refreshEntryClass()
        if not transactional:
            self._isCommitting = 1
