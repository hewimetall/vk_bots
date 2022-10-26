import unittest
from main import App

class TestApp(unittest.TestCase):

    def test_init(self):
        app = App()

    def test_state(self):
        app = App()
        self.assertEqual(len(app.setting.state.defaults().items()), len(app.fsm._state))
        self.assertTrue(0 < len(app.fsm._state))

if __name__ == '__main__':
    unittest.main()
