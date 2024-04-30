import asyncio
import os


class CollabFilteringDaemon:
    """A daemon that executes a task every x seconds"""

    def __init__(self, delay: int) -> None:
        self._delay = delay
        self.first_run = True

    async def _execute_task(self) -> None:
        await self._task()

    async def start_daemon(self) -> None:
        while True:
            if self.first_run:
                await asyncio.sleep(120)  # Wait for other services to start
                await self._execute_task()
                self.first_run = False

            await asyncio.sleep(self._delay)
            await self._execute_task()

    # TODO: Aditya
    async def _task(self) -> None:
        print("Running task")