import asyncio

from pmond import utils
from pmond.probes.abc import FileProbe, ProbeResult, Measurement, Reader
from pmond.exceptions import ProbeFailure

log = utils.baselog.getChild("probe.mem")
class MemReader(Reader):
    async def read(self):
        log.debug("Reading [mem]")
        probe = MemProbe()
        uid, results = await asyncio.gather(probe.machineid(), probe.run())
        return ProbeResult([], [Measurement(uid, f"blipp:mem:{n}", v) for n,v in results.items()])

class MemProbe(FileProbe):
    async def run(self):
        lines = await self.readfile("/proc/meminfo")
        if lines is None:
            raise ProbeFailure("Could not read file '/proc/meminfo'")

        total = 0
        result, m = {}, {"MemFree": "free", "Cached": "cache", "Buffers": "buffer", "Slab": "kernel"}
        for n, *_, v, unit in lines.split('\n'):
            n = n[:-1]
            if n == "MemTotal": total = int(v)
            if n in m:
                result[m[n]] = utils.normalizeBytes(int(v), unit)
        result["used"] = total - result["free"]
        return result
