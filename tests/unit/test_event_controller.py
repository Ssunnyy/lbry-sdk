from lbry.testcase import AsyncioTestCase
from lbry.event import EventController
from lbry.tasks import TaskGroup


class StreamControllerTestCase(AsyncioTestCase):

    async def test_non_unique_events(self):
        events = []
        controller = EventController()
        controller.stream.listen(events.append)
        await controller.add("yo")
        await controller.add("yo")
        self.assertListEqual(events, ["yo", "yo"])

    async def test_unique_events(self):
        events = []
        controller = EventController(merge_repeated_events=True)
        controller.stream.listen(events.append)
        await controller.add("yo")
        await controller.add("yo")
        self.assertListEqual(events, ["yo"])

    async def test_sync_listener_errors(self):
        def bad_listener(e):
            raise ValueError('bad')
        controller = EventController()
        controller.stream.listen(bad_listener)
        with self.assertRaises(ValueError):
            await controller.add("yo")

    async def test_async_listener_errors(self):
        async def bad_listener(e):
            raise ValueError('bad')
        controller = EventController()
        controller.stream.listen(bad_listener)
        with self.assertRaises(ValueError):
            await controller.add("yo")


class TaskGroupTestCase(AsyncioTestCase):

    async def test_cancel_sets_it_done(self):
        group = TaskGroup()
        group.cancel()
        self.assertTrue(group.done.is_set())
