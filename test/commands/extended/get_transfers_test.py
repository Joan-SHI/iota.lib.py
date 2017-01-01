# coding=utf-8
from __future__ import absolute_import, division, print_function, \
  unicode_literals

from unittest import TestCase

import filters as f
from filters.test import BaseFilterTestCase
from mock import Mock, patch
from six import binary_type, text_type

from iota import Address, Iota, Bundle, Tag, Transaction
from iota.commands.extended.get_transfers import GetTransfersCommand, \
  GetTransfersRequestFilter
from iota.crypto.types import Seed
from iota.filters import Trytes
from test import MockAdapter


class GetTransfersRequestFilterTestCase(BaseFilterTestCase):
  filter_type = GetTransfersCommand(MockAdapter()).get_request_filter
  skip_value_check = True

  # noinspection SpellCheckingInspection
  def setUp(self):
    super(GetTransfersRequestFilterTestCase, self).setUp()

    # Define a few tryte sequences that we can re-use between tests.
    self.seed = b'HELLOIOTA'

  def test_pass_happy_path(self):
    """
    Request is valid.
    """
    request = {
      'seed':             Seed(self.seed),
      'start':            0,
      'end':              10,
      'inclusion_states': True,
    }

    filter_ = self._filter(request)

    self.assertFilterPasses(filter_)
    self.assertDictEqual(filter_.cleaned_data, request)

  def test_pass_compatible_types(self):
    """
    The request contains values that can be converted to the expected
    types.
    """
    filter_ = self._filter({
      # ``seed`` can be any value that is convertible into a
      # TryteString.
      'seed': binary_type(self.seed),

      # These values must still be integers/bools, however.
      'start':            42,
      'end':              86,
      'inclusion_states': True,
    })

    self.assertFilterPasses(filter_)
    self.assertDictEqual(
      filter_.cleaned_data,

      {
        'seed':             Seed(self.seed),
        'start':            42,
        'end':              86,
        'inclusion_states': True,
      },
    )

  def test_pass_optional_parameters_excluded(self):
    """
    The request contains only required parameters.
    """
    filter_ = self._filter({
      'seed': Seed(self.seed),
    })

    self.assertFilterPasses(filter_)
    self.assertDictEqual(
      filter_.cleaned_data,

      {
        'seed':             Seed(self.seed),
        'start':            0,
        'end':              None,
        'inclusion_states': False,
      }
    )

  def test_fail_empty_request(self):
    """
    The request is empty.
    """
    self.assertFilterErrors(
      {},

      {
        'seed': [f.FilterMapper.CODE_MISSING_KEY],
      },
    )

  def test_fail_unexpected_parameters(self):
    """
    The request contains unexpected parameters.
    """
    self.assertFilterErrors(
      {
        'seed': Seed(self.seed),

        # Your rules are really beginning to annoy me.
        'foo': 'bar',
      },

      {
        'foo': [f.FilterMapper.CODE_EXTRA_KEY],
      },
    )

  def test_fail_seed_null(self):
    """
    ``seed`` is null.
    """
    self.assertFilterErrors(
      {
        'seed': None,
      },

      {
        'seed': [f.Required.CODE_EMPTY],
      },
    )

  def test_fail_seed_wrong_type(self):
    """
    ``seed`` cannot be converted into a TryteString.
    """
    self.assertFilterErrors(
      {
        'seed': text_type(self.seed, 'ascii'),
      },

      {
        'seed': [f.Type.CODE_WRONG_TYPE],
      },
    )

  def test_fail_seed_malformed(self):
    """
    ``seed`` has the correct type, but it contains invalid characters.
    """
    self.assertFilterErrors(
      {
        'seed': b'not valid; seeds can only contain uppercase and "9".',
      },

      {
        'seed': [Trytes.CODE_NOT_TRYTES],
      },
    )

  def test_fail_start_string(self):
    """
    ``start`` is a string.
    """
    self.assertFilterErrors(
      {
        # Not valid; it must be an int.
        'start': '0',

        'seed': Seed(self.seed),
      },

      {
        'start': [f.Type.CODE_WRONG_TYPE],
      },
    )

  def test_fail_start_float(self):
    """
    ``start`` is a float.
    """
    self.assertFilterErrors(
      {
        # Even with an empty fpart, floats are not valid.
        # It's gotta be an int.
        'start': 8.0,

        'seed': Seed(self.seed),
      },

      {
        'start': [f.Type.CODE_WRONG_TYPE],
      },
    )

  def test_fail_start_too_small(self):
    """
    ``start`` is less than 0.
    """
    self.assertFilterErrors(
      {
        'start': -1,

        'seed': Seed(self.seed),
      },

      {
        'start': [f.Min.CODE_TOO_SMALL],
      },
    )

  def test_fail_end_string(self):
    """
    ``end`` is a string.
    """
    self.assertFilterErrors(
      {
        # Not valid; it must be an int.
        'end': '0',

        'seed': Seed(self.seed),
      },

      {
        'end': [f.Type.CODE_WRONG_TYPE],
      },
    )

  def test_fail_end_float(self):
    """
    ``end`` is a float.
    """
    self.assertFilterErrors(
      {
        # Even with an empty fpart, floats are not valid.
        # It's gotta be an int.
        'end': 8.0,

        'seed': Seed(self.seed),
      },

      {
        'end': [f.Type.CODE_WRONG_TYPE],
      },
    )

  def test_fail_end_too_small(self):
    """
    ``end`` is less than 0.
    """
    self.assertFilterErrors(
      {
        'end': -1,

        'seed': Seed(self.seed),
      },

      {
        'end': [f.Min.CODE_TOO_SMALL],
      },
    )

  def test_fail_end_occurs_before_start(self):
    """
    ``end`` is less than ``start``.
    """
    self.assertFilterErrors(
      {
        'start':  1,
        'end':    0,

        'seed': Seed(self.seed),
      },

      {
        'start': [GetTransfersRequestFilter.CODE_INTERVAL_INVALID],
      },
    )

  def test_fail_interval_too_large(self):
    """
    ``end`` is way more than ``start``.
    """
    self.assertFilterErrors(
      {
        'start':  0,
        'end':    GetTransfersRequestFilter.MAX_INTERVAL + 1,

        'seed': Seed(self.seed),
      },

      {
        'end':  [GetTransfersRequestFilter.CODE_INTERVAL_TOO_BIG],
      },
    )

  def test_fail_inclusion_states_wrong_type(self):
    """
    ``inclusion_states`` is not a boolean.
    """
    self.assertFilterErrors(
      {
        'inclusion_states': '1',

        'seed': Seed(self.seed),
      },

      {
        'inclusion_states': [f.Type.CODE_WRONG_TYPE],
      },
    )


# noinspection SpellCheckingInspection
class GetTransfersCommandTestCase(TestCase):
  def setUp(self):
    super(GetTransfersCommandTestCase, self).setUp()

    self.adapter = MockAdapter()
    self.command = GetTransfersCommand(self.adapter)

  def test_wireup(self):
    """
    Verify that the command is wired up correctly.
    """
    self.assertIsInstance(
      Iota(self.adapter).getTransfers,
      GetTransfersCommand,
    )

  def test_full_scan(self):
    """
    Scanning the Tangle for all transfers.
    """
    addy1 =\
      Address(
        b'TESTVALUEONE9DONTUSEINPRODUCTION99999YDZ'
        b'E9TAFAJGJA9CECKDAEPHBICDR9LHFCOFRBQDHC9IG'
      )

    addy2 =\
      Address(
        b'TESTVALUETWO9DONTUSEINPRODUCTION99999TES'
        b'GINEIDLEEHRAOGEBMDLENFDAFCHEIHZ9EBZDD9YHL'
      )

    # To speed up the test, we will mock the address generator.
    # :py:class:`iota.crypto.addresses.AddressGenerator` already has
    # its own test case, so this does not impact the stability of the
    # codebase.
    # noinspection PyUnusedLocal
    def create_generator(ag, start, step=1):
      for addy in [addy1, addy2][start::step]:
        yield addy

    # The first address received IOTA.
    self.adapter.seed_response(
      'findTransactions',

      {
        'duration': 42,

        'hashes': [
          'TESTVALUEFIVE9DONTUSEINPRODUCTION99999VH'
          'YHRHJETGYCAFZGABTEUBWCWAS9WF99UHBHRHLIOFJ',
        ],
      },
    )

    # The second address is unused.
    self.adapter.seed_response(
      'findTransactions',

      {
        'duration': 1,
        'hashes':   [],
      },
    )

    self.adapter.seed_response(
      'getTrytes',

      {
        'duration': 99,

        # Thankfully, we do not have to seed a realistic response for
        # ``getTrytes``, as we will be mocking the ``getBundles``
        # command that uses on it.
        'trytes': [''],
      },
    )

    bundle = Bundle([
      Transaction(
        address = addy1,
        timestamp = 1483033814,

        # These values are not relevant to the test.
        hash_ = None,
        signature_message_fragment = None,
        value = 42,
        tag = Tag(b''),
        current_index = 0,
        last_index = 0,
        bundle_hash = None,
        trunk_transaction_hash = None,
        branch_transaction_hash = None,
        nonce = None,
      )
    ])

    mock_get_bundles = Mock(return_value={
      'bundles': [bundle],
    })

    with patch(
        'iota.crypto.addresses.AddressGenerator.create_generator',
        create_generator,
    ):
      with patch(
          'iota.commands.extended.get_bundles.GetBundlesCommand._execute',
          mock_get_bundles,
      ):
        response = self.command(seed=Seed.random())

    self.assertDictEqual(
      response,

      {
        'bundles': [bundle],
      },
    )

  def test_start(self):
    """
    Scanning the Tangle for all transfers, with start index.
    """
    # :todo: Implement test.
    self.skipTest('Not implemented yet.')

  def test_end(self):
    """
    Scanning the Tangle for all transfers, with end index.
    """
    # :todo: Implement test.
    self.skipTest('Not implemented yet.')

  def test_start_and_end(self):
    """
    Scanning the Tangle for all transfers, with start and end indices.
    """
    # :todo: Implement test.
    self.skipTest('Not implemented yet.')

  def test_get_inclusion_states(self):
    """
    Fetching inclusion states with transactions.
    """
    # :todo: Implement test.
    self.skipTest('Not implemented yet.')
