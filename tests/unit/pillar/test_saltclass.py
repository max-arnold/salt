# -*- coding: utf-8 -*-

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals

import os

# Import Salt Libs
import salt.config
import salt.loader
import salt.pillar.saltclass as sc_pillar

# Import Salt Testing libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.runtests import RUNTIME_VARS
from tests.support.unit import TestCase

fake_args = {
    "path": os.path.abspath(os.path.join(RUNTIME_VARS.FILES, "saltclass", "examples"))
}


class SaltclassPillarTestCase(TestCase, LoaderModuleMockMixin):
    """
    Tests for salt.pillar.saltclass
    """

    def setup_loader_modules(self):
        opts = salt.config.DEFAULT_MINION_OPTS.copy()
        utils = salt.loader.utils(opts, whitelist=["saltclass"], context={})
        return {sc_pillar: {"__utils__": utils}}

    def _runner(self, expected_ret):
        try:
            full_ret = sc_pillar.ext_pillar("fake_id", {}, fake_args)
            parsed_ret = full_ret["__saltclass__"]["classes"]
        # Fail the test if we hit our NoneType error
        except TypeError as err:
            self.fail(err)
        # Else give the parsed content result
        self.assertListEqual(parsed_ret, expected_ret)

    def test_succeeds(self):
        ret = ["default.users", "default.motd", "default.empty", "default", "roles.app"]
        self._runner(ret)


class SaltclassPillarTestCaseListExpansion(TestCase, LoaderModuleMockMixin):
    """
    Tests for salt.pillar.saltclass variable expansion in list
    """

    def setup_loader_modules(self):
        opts = salt.config.DEFAULT_MINION_OPTS.copy()
        utils = salt.loader.utils(opts, whitelist=["saltclass"], context={})
        return {sc_pillar: {"__utils__": utils}}

    def _runner(self, expected_ret):
        try:
            full_ret = sc_pillar.ext_pillar("fake_id", {}, fake_args)
            parsed_ret = full_ret["test_list"]
        # Fail the test if we hit our NoneType error
        except TypeError as err:
            self.fail(err)
        # Else give the parsed content result
        self.assertListEqual(parsed_ret, expected_ret)

    def test_succeeds(self):
        ret = [{"a": "192.168.10.10"}, "192.168.10.20"]
        self._runner(ret)
