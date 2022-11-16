from datetime import datetime, timedelta

from pmond import utils
from pmond.probes.abc import Reader

log = utils.baselog.getChild("sched.scheduled")
class Scheduled(object):
    def __init__(self, reader:Reader, *, time:str, format:str=None, limit:int=None):
        if format is None:
            format = "%H:%M:%S"
        self.partial = datetime.strptime(time, format)
        self.limit = limit
        self.reader = reader

    def __aiter__(self):
        log.debug("Starting schedule [scheduled]")
        return self

    async def __anext__(self):
        log.debug("Running schedule [scheduled]")
        if self.limit is not None:
            if self.limit == 0:
                raise StopAsyncIteration()
            self.limit -= 1
        now = datetime.now()
        adj = self.partial(now.year, now.month, now.day)
        if adj < now:
            adj = adj + timedelta(days=1)
        await asyncio.sleep((adj - now).total_seconds())
        return await self.reader.read()
