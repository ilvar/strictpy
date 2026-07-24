import unittest

from hypothesis import given, strategies as st

from {{MODULE_NAME}}.main import reverse


class ReverseProperties(unittest.TestCase):
    @given(st.lists(st.integers(min_value=-1_000, max_value=1_000), max_size=64))
    def test_reversing_twice_preserves_values(self, values: list[int]) -> None:
        transformed = reverse(reverse(values))
        self.assertEqual(transformed, values)
