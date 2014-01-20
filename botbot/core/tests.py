"""
Testing InfinitePaginator
"""
from .paginator import InfinitePaginator
from django.test import TestCase


class TestInfinitePaginator(TestCase):

    def setUp(self):
        self.p = InfinitePaginator(range(20), 2,
                                   link_template='/bacon/page/%d')

    def test_validate_number(self):
        self.assertEqual(self.p.validate_number(2), 2)

    def test_orphans(self):
        self.assertEqual(self.p.orphans, 0)

    def test_page(self):
        p3 = self.p.page(3)
        self.assertEqual(str(p3), "<Page 3>")
        self.assertEqual(p3.end_index(), 6)
        self.assertEqual(p3.has_next(), True)
        self.assertEqual(p3.has_previous(), True)
        self.assertEqual(self.p.page(10).has_next(), False)
        self.assertEqual(self.p.page(1).has_previous(), False)
        self.assertEqual(p3.next_link(), '/bacon/page/4')
        self.assertEqual(p3.previous_link(), '/bacon/page/2')
