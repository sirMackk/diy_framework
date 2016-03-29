import asyncio
import unittest as t

from http_connection import HTTPConnection


class TestHTTPConnection(t.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()

    def tearDown(self):
        tasks = asyncio.tasks.all_tasks(loop=self.loop)
        if tasks:
            for task in asyncio.tasks.all_tasks(loop=self.loop):
                task.cancel()
        if self.loop.is_running():
            self.loop.stop()


if __name__ == '__main__':
    t.main()
