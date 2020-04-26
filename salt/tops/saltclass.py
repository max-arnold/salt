# -*- coding: utf-8 -*-
"""
SaltClass Top Module
=======================

.. code-block:: yaml

    master_tops:
      saltclass:
        path: /srv/saltclass

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
    return (False, "Saltclass master_tops isn't configured")


def top(**kwargs):
    """
    Compile tops
    """
    # Node definitions path will be retrieved from args (or set to default),
    # then added to 'salt_data' dict that is passed to the 'get_tops'
    # function. The dictionary contains:
    #     - __opts__
    #     - __salt__
    #     - __grains__
    #     - __pillar__
    #     - path
    #
    # If successful, the function will return a top dict for minion_id.

    # If path has not been set, make a default
    _opts = __opts__["master_tops"]["saltclass"]
    if "path" not in _opts:
        path = "/srv/saltclass"
        log.info("path variable unset, using default: %s", path)
    else:
        path = _opts["path"]

    if "id" not in kwargs["opts"]:
        log.warning("Minion id not found - Returning empty dict")
        return {}
    else:
        minion_id = kwargs["opts"]["id"]

    # Create a dict that will contain our salt dicts to pass it to saltclass
    salt_data = {
        "__opts__": kwargs["opts"],
        "__salt__": {},
        "__grains__": kwargs["grains"],
        "__pillar__": {},
        "path": path,
    }

    return __utils__["saltclass.get_tops"](minion_id, salt_data)
