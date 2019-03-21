# -*- coding: utf-8 -*-

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import os

# Import Salt Testing libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.unit import TestCase, skipIf
from tests.support.mock import NO_MOCK, NO_MOCK_REASON

# Import Salt Libs
import salt.pillar.saltclass as saltclass


base_path = os.path.dirname(os.path.realpath(__file__))
fake_minion_id1 = 'fake_id1'
fake_minion_id2 = 'fake_id2'

fake_pillar = {}
fake_args = ({'path': os.path.abspath(
                        os.path.join(base_path, '..', '..', 'integration',
                                     'files', 'saltclass', 'examples-new'))})
fake_opts = {}
fake_salt = {}
fake_grains = {}


@skipIf(NO_MOCK, NO_MOCK_REASON)
class SaltclassPillarNewTestCase(TestCase, LoaderModuleMockMixin):
    '''
    New tests for salt.pillar.saltclass
    '''
    rets = {}

    def setup_loader_modules(self):
        return {saltclass: {'__opts__': fake_opts,
                            '__salt__': fake_salt,
                            '__grains__': fake_grains}}

    def _get_ret(self, minion_id):
        if minion_id not in self.rets:
            self.rets[minion_id] = saltclass.ext_pillar(minion_id, fake_pillar, fake_args)
        return self.rets[minion_id]

    def test_000_pprint(self):
        from pprint import pprint
        for m in (fake_minion_id1, fake_minion_id2):
            print(m + ":")
            pprint(self._get_ret(m))

    def test_simple_case_pillars(self):
        expected_result = {
            'L0A':
                {
                    'dict':
                        {'k1': 'L0A-1', 'k2': 'L0A-2'},
                    'list': ['L0A-1', 'L0A-2'],
                    'plaintext': u'plaintext_from_L0A'
                },
            'L0B':
                {
                    'list': ['L0B-1', 'L0B-2'],
                    'plaintext': 'plaintext_from_L0B'
                }
        }
        result = self._get_ret(fake_minion_id1)
        filtered_result = {k: result[k] for k in ('L0A', 'L0B') if k in result}
        self.assertDictEqual(filtered_result, expected_result)

    def test_simple_case_saltclass(self):
        expected_result = {
            '__saltclass__':
                {
                    'classes': ['L0.A',
                                'L0.B.otherclass',
                                'L0.B',
                                'L1.A',
                                'L1.B',
                                'L2.A'],
                    'environment': 'base',
                    'nodename': 'fake_id1',
                    'states': ['state_A', 'state_B']
                }
        }
        result = self._get_ret(fake_minion_id1)
        filtered_result = {'__saltclass__': result.get('__saltclass__')}
        self.assertDictEqual(filtered_result, expected_result)

    def test_plaintext_pillar_overwrite(self):
        expected_result = {
            'same_plaintext_pillar': 'from_L0B'
        }
        result = self._get_ret(fake_minion_id1)
        filtered_result = {'same_plaintext_pillar': result.get('same_plaintext_pillar')}
        self.assertDictEqual(filtered_result, expected_result)

    def test_list_pillar_extension(self):
        expected_result = {
            'same_list_pillar': ['L0A-1', 'L0A-2', 'L0B-1', 'L0B-2']
        }
        result = self._get_ret(fake_minion_id1)
        filtered_result = {'same_list_pillar': result.get('same_list_pillar')}
        self.assertDictEqual(filtered_result, expected_result)

    def test_list_override(self):
        expected_result = {
            'same_list_pillar': ['L0C-1', 'L0C-2']
        }
        result = self._get_ret(fake_minion_id2)
        filtered_result = {'same_list_pillar': result.get('same_list_pillar')}
        self.assertDictEqual(filtered_result, expected_result)

    def test_list_override_with_no_ancestor(self):
        expected_result = {
            'single-list-override': [1, 2]
        }
        result = self._get_ret(fake_minion_id1)
        filtered_result = {'single-list-override': result.get('single-list-override')}
        self.assertDictEqual(filtered_result, expected_result)

    def test_pillar_expansion(self):
        expected_result = {
            'expansion':
                {
                    'dict': {'k1': 'L0C-1', 'k2': 'L0C-2'},
                    'list': ['L0C-1', 'L0C-2'],
                    'plaintext': 'plaintext_from_L0C'
                }
        }
        result = self._get_ret(fake_minion_id2)
        filtered_result = {'expansion': result.get('expansion')}
        self.assertDictEqual(filtered_result, expected_result)

    def test_pillars_in_jinja(self):
        expected_states = ['state_B', 'state_C.1', 'state_C.9999']
        result = self._get_ret(fake_minion_id2)
        filtered_result = result['__saltclass__']['states']
        for v in expected_states:
            self.assertIn(v, filtered_result)
