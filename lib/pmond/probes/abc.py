import asyncio

from uuid import uuid4
from typing import NamedTuple

from pmond import utils, config

class Reader(object):
    def __init__(self, **kwargs):
        self._probe_args = kwargs

log = utils.baselog.getChild("probe")
class Probe(object):
    """
    Abstract Base Class for "Probes".  Probes interact with external agents or files
    to generate data.  The 'run' function executes the probe and returns a dictionary
    containing data from the external entity.
    """
    async def subject(self): pass
    async def run(self): pass

class FileProbe(Probe):
    """
    Abstract Base Class for Probes that reads data from files and/or writes data to files.
    """
    async def readfile(self, path):
        return await asyncio.to_thread(self._readfile, path)
    def _readfile(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            log.warn(f"'{path}' not found")
        return None

    async def writefile(self, path, data):
        return await asyncio.to_thread(self._writefile, path, data)
    def _writefile(self, path, data):
        try:
            with open(path, 'w') as f:
                f.write(data)
                return True
        except OSError:
            log.error(f"Insufficent permissions to write to '{path}'")
            return False

class NodeProbe(FileProbe):
    """
    Abstract Base Class for Probes that measure values on a single node, generally
    a host or switch.
    """
    async def subject(self):
        idfile = config.args["midfile"]
        uid = ((await self.readfile(idfile)) or str(uuid4()).replace('-', '')).strip()
        if not await self.writefile(idfile, uid):
            exit(-1)
        return f"uuid:node:{uid}"

class Measurement(NamedTuple):
    subject: str
    name: str
    data: list
class ProbeResult(NamedTuple):
    subjects: dict[list]
    measurements: list[Measurement]
