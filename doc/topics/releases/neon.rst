:orphan:

==================================
Salt Release Notes - Codename Neon
==================================

Unless and onlyif Enhancements
==============================

The ``unless`` and ``onlyif`` requisites can now be operated with salt modules.
The dictionary must contain an argument ``fun`` which is the module that is
being run, and everything else must be passed in under the args key or will be
passed as individual kwargs to the module function.

.. code-block:: yaml

  install apache on debian based distros:
    cmd.run:
      - name: make install
      - cwd: /path/to/dir/whatever-2.1.5/
      - unless:
        - fun: file.file_exists
          path: /usr/local/bin/whatever

.. code-block:: yaml

  set mysql root password:
    debconf.set:
      - name: mysql-server-5.7
      - data:
          'mysql-server/root_password': {'type': 'password', 'value': {{pillar['mysql.pass']}} }
      - unless:
        - fun: pkg.version
          args:
            - mysql-server-5.7

Keystore State and Module
=========================

A new :py:func:`state <salt.states.keystore>` and
:py:func:`execution module <salt.modules.keystore>` for manaing Java
Keystore files is now included. It allows for adding/removing/listing
as well as managing keystore files.

.. code-block:: bash

  # salt-call keystore.list /path/to/keystore.jks changeit
  local:
    |_
      ----------
      alias:
          hostname1
      expired:
          True
      sha1:
          CB:5E:DE:50:57:99:51:87:8E:2E:67:13:C5:3B:E9:38:EB:23:7E:40
      type:
          TrustedCertEntry
      valid_start:
          August 22 2012
      valid_until:
          August 21 2017

.. code-block:: yaml

  define_keystore:
    keystore.managed:
      - name: /tmp/statestore.jks
      - passphrase: changeit
      - force_remove: True
      - entries:
        - alias: hostname1
          certificate: /tmp/testcert.crt
        - alias: remotehost
          certificate: /tmp/512.cert
          private_key: /tmp/512.key
        - alias: stringhost
          certificate: |
            -----BEGIN CERTIFICATE-----
            MIICEjCCAX
            Hn+GmxZA
            -----END CERTIFICATE-----

Slot Syntax Updates
===================

The slot syntax has been updated to support parsing dictionary responses and to append text.

.. code-block:: yaml

  demo dict parsing and append:
    test.configurable_test_state:
      - name: slot example
      - changes: False
      - comment: __slot__:salt:test.arg(shell="/bin/bash").kwargs.shell ~ /appended

.. code-block:: none

  local:
    ----------
          ID: demo dict parsing and append
    Function: test.configurable_test_state
        Name: slot example
      Result: True
     Comment: /bin/bash/appended
     Started: 09:59:58.623575
    Duration: 1.229 ms
     Changes:

Also, slot parsing is now supported inside of nested state data structures (dicts, lists, unless/onlyif args):

.. code-block:: yaml

  demo slot parsing for nested elements:
    file.managed:
      - name: /tmp/slot.txt
      - source: salt://template.j2
      - template: jinja
      - context:
          # Slot inside of the nested context dictionary
          variable: __slot__:salt:test.echo(a_value)
      - unless:
        - fun: file.search
          args:
            # Slot as unless argument
            - __slot__:salt:test.echo(/tmp/slot.txt)
            - "DO NOT OVERRIDE"
          ignore_if_missing: True


State Changes
=============

- Added new :py:func:`ssh_auth.manage <salt.states.ssh_auth.manage>` state to
  ensure only the specified ssh keys are present for the specified user.


Deprecations
============

Module Deprecations
-------------------

- The hipchat module has been removed due to the service being retired.
  :py:func:`Google Chat <salt.modules.google_chat>`,
  :py:func:`MS Teams <salt.modules.msteams>`, or
  :py:func:`Slack <salt.modules.slack_notify>` may be suitable replacements.


State Deprecations
------------------

- The hipchat state has been removed due to the service being retired.
  :py:func:`MS Teams <salt.states.msteams>` or
  :py:func:`Slack <salt.states.slack>` may be suitable replacements.

Engine Removal
--------------

- The hipchat engine has been removed due to the service being retired. For users migrating
  to Slack, the :py:func:`slack <salt.engines.slack>` engine may be a suitable replacement.

Returner Removal
----------------

- The hipchat returner has been removed due to the service being retired. For users migrating
  to Slack, the :py:func:`slack <salt.returners.slack_returner>` returner may be a suitable
  replacement.

Grain Deprecations
------------------

For ``smartos`` some grains have been deprecated. These grains have been removed.

  - The ``hypervisor_uuid`` has been replaced with ``mdata:sdc:server_uuid`` grain.
  - The ``datacenter`` has been replaced with ``mdata:sdc:datacenter_name`` grain.

salt.auth.Authorize Class Removal
---------------------------------
- The salt.auth.Authorize Class inside of the `salt/auth/__init__.py` file has been removed and
  the `any_auth` method inside of the file `salt/utils/minions.py`. These method and classes were
  not being used inside of the salt code base.

