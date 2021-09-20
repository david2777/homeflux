import unittest

from homeflux.agents.gwp_opower import Meter


class TestMeterAgent(unittest.IsolatedAsyncioTestCase):
    async def test_init(self):
        m = Meter('test@email.com', 'password', 'uuid')
        self.assertIsInstance(m, Meter)

    async def test_login(self):
        m = Meter('test@email.com', 'password', 'uuid')
        self.assertIsNone(m.session)
        await m.login()
        self.assertIsNotNone(m.session)
        await m.logout()
        self.assertIsNone(m.session)

    async def test_context_manager(self):
        m = Meter('test@email.com', 'password', 'uuid')
        self.assertIsNone(m.session)
        async with m:
            self.assertIsNotNone(m.session)
        self.assertIsNone(m.session)


if __name__ == '__main__':
    unittest.main()
