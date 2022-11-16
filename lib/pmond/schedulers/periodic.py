import asyncio

from pmond import utils
from pmond.probes.abc import Reader

log = utils.baselog.getChild("sched.periodic")
class Periodic(object):
    def __init__(self, reader:Reader, *, period:float, limit:int=None):
        self.reader = reader
        self.period = period
        self.limit = limit

    def __aiter__(self):
        log.debug("Starting schedulee [periodic]")
        return self

    async def __anext__(self):
        log.debug("Running schedule [periodic]")
        if self.limit is not None:
            if self.limit == 0:
                raise StopAsyncIteration()
            self.limit -= 1
        await asyncio.sleep(self.period)
        return await self.reader.read()
