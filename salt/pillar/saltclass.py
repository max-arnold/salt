# -*- coding: utf-8 -*-
"""
SaltClass Pillar Module
=======================

.. code-block:: yaml

    ext_pillar:
      - saltclass:
        - path: /srv/saltclass
    # Optionally pass through GPG decryption
    # - gpg: {}

For additional configuration instructions, see the :ref:`saltclass <saltclass>` node classifier
"""

# import python libs
from __future__ import absolute_import, print_function, unicode_literals

import logging

log = logging.getLogger(__name__)


__virtualname__ = "saltclass"


def __virtual__():
    """
    Only run if properly configured
    """
    if __opts__["master_tops"].get("saltclass"):
        return __virtualname__
    return (False, "Saltclass ext_pillar isn't configured")


def ext_pillar(minion_id, pillar, *args, **kwargs):
    """
    Compile pillar data
    """
    # Node definitions path will be retrieved from args (or set to default),
    # then added to 'salt_data' dict that is passed to the 'get_pillars'
    # function. The dictionary contains:
    #     - __opts__
    #     - __salt__
    #     - __grains__
    #     - __pillar__
    #     - path
    #
    # If successful, the function will return a pillar dict for minion_id.

    # If path has not been set, make a default
    for i in args:
        if "path" not in i:
            path = "/srv/saltclass"
            args[i]["path"] = path
            log.info("path variable unset, using default: %s", path)
        else:
            path = i["path"]

    # Create a dict that will contain our salt dicts to pass it to saltclass
    salt_data = {
        "__opts__": __opts__,
        "__salt__": __salt__,
        "__grains__": __grains__,
        "__pillar__": pillar,
        "path": path,
    }
    return __utils__["saltclass.get_pillars"](minion_id, salt_data)
