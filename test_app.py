import unittest
from streamlit.testing.v1 import AppTest
class AppTests(unittest.TestCase):
    def test_airfoil_validation(self):
        a=AppTest.from_file('app.py').run(timeout=30)
        self.assertFalse(a.exception)
        a.sidebar.text_input[0].set_value('2012').run(timeout=30)
        self.assertFalse(a.exception); self.assertTrue(a.error)
