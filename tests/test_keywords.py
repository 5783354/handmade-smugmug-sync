# coding=utf-8
import unittest

from settings import PHOTOS_PATH
from utils.keywords import get_keywords


class KeywordsTests(unittest.TestCase):
    def test_lower_case(self):
        path = PHOTOS_PATH[0] + '/ABC/abc.jpg'
        expected_keywords = ['abc']

        keywords = get_keywords(path)
        self.assertEqual(keywords, expected_keywords)

    def test_unicode(self):
        path = PHOTOS_PATH[0] + u'/ABC/ƒ©-тэг/123.jpg'
        expected_keywords = ['abc', 'f(c)-teg']

        keywords = get_keywords(path)
        self.assertEqual(keywords, expected_keywords)

    def test_keywords_count(self):
        path = PHOTOS_PATH[0] + '/A1/b1/c1/d2/e3/f4/g/h/i/j/k/last teg/123.jpg'
        expected_keywords = ["a1", "b1", "c1", "d2", "e3", "f4", "g", "h", "i", "j", "k",
                             "last teg"]

        keywords = get_keywords(path)
        self.assertEqual(keywords, expected_keywords)
