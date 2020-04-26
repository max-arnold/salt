# -*- coding: utf-8 -*-
# Import python libs
from __future__ import absolute_import, print_function, unicode_literals

import os

# Import Salt Libs
import salt.utils.saltclass as sc_utils

# Import Salt Testing libs
from tests.support.mock import MagicMock, patch
from tests.support.runtests import RUNTIME_VARS
from tests.support.unit import TestCase


class SaltclassUtilsTestCase(TestCase):
    def setUp(self):
        self.sc_path = os.path.abspath(
            os.path.join(RUNTIME_VARS.TESTS_DIR, "unit", "files", "saltclass")
        )
        self.context = {
            "__opts__": {"opt": "opt"},
            "__salt__": {"salt": "salt"},
            "__grains__": {"grain": "grain"},
            "__pillar__": {"pillar": "pillar"},
        }

    def test_yaml_renderer_catches_errors(self):
        mock_log = MagicMock()
        with patch.object(sc_utils.log, "error", mock_log):
            sc_utils._render_yaml(os.path.join(self.sc_path, "error.yml"), self.context)
            mock_log.assert_called_once()
            self.assertIn(
                "YAML rendering exception for file", mock_log.mock_calls[0][1][0]
            )

    def test_empty(self):
        mock_log = MagicMock()
        with patch.object(sc_utils.log, "warning", mock_log):
            res = sc_utils._render_yaml(
                os.path.join(self.sc_path, "empty.yml"), self.context
            )
            mock_log.assert_called_once()
            self.assertIn("Unable to render yaml", mock_log.mock_calls[0][1][0])
            self.assertEqual(res, {})

    def test_context(self):
        res = sc_utils._render_yaml(
            os.path.join(self.sc_path, "context.yml"), self.context
        )
        self.assertEqual(
            res, {"grain": "grain", "opt": "opt", "pillar": "pillar", "salt": "salt"}
        )
