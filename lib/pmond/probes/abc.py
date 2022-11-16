import asyncio

from typing import NamedTuple

from pmond import utils

class Reader(object): pass

log = utils.baselog.getChild("probe")
class FileProbe(object):
    def __init__(self, *, machinefile=None):
        if machinefile is None:
            self._idfile = "/etc/machine-id"
        else:
            self._idfile = machinefile

    async def machineid(self):
        uid = ((await self.readfile(self._idfile)) or str(uuid4()).replace('-', '')).strip()
        await self.writefile(self._idfile, uid)
        return f"uuid:node:{uid}"

    async def readfile(self, path):
        return await asyncio.to_thread(self._readfile, path)
    def _readfile(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            log.warn("machine-id not found, creating new id")
        return None

    async def writefile(self, path, data):
        return await asyncio.to_thread(self._writefile, path, data)
    def _writefile(self, path, data):
        try:
            with open(path, 'w') as f:
                f.write(data)
                return True
        except OSError:
            log.error(f"Insufficent permissions to create {path}")
            return False


class Measurement(NamedTuple):
    subject: str
    name: str
    data: list
class ProbeResult(NamedTuple):
    subjects: list[dict]
    measurements: list[Measurement]
