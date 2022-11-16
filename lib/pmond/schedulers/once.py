from pmond.probes.abc import Reader
from pmond import utils

log = utils.baselog.getChild("sched.once")
class Once(object):
    def __init__(self, reader:Reader, *, delay=0):
        self.reader, self.complete = reader, False

    def __aiter__(self):
        log.debug("Starting schedule [once]")
        return self

    async def __anext__(self):
        log.debug("Running schedule [once]")
        if not self.complete:
            self.complete = True
            return await self.reader.read()
        raise StopAsyncIteration()
