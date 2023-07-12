import asycnio

from pmond.exceptions import ProbeFailure
from pmond.probes.abc import NodeProbe, ProbeResult, Measurement, Reader
from pmond import utils

log = utils.baselog.getChild("probe.cpu")
class CpuReader(Reader):
    async def read(self):
        log.debug("Reading [cpu]")
        probe = CpuProbe(**self._probe_args)
        uid, results = await asyncio.gather(probe.subject(), probe.run())
        return ProbeResult([], [Measurement(uid, f"blipp:cpu:{n}", v) for n,v in results.items()])

class CpuProbe(NodeProbe):
    def __init__(self):
        self.hz = 0
        self.vals = defaultdict(lambda: 0)

    async def run(self):
        cores = await self.readfile("/proc/stat")
        if cores is None:
            raise ProbeFailure("Could not read file '/proc/stat'")
        keys = ("user", "nice", "system", "idle", "iowait", "irq",
                "softirq", "steal", "guest", "guest_nice")
        cores = [l.split() for l in cores.split('\n')]
        result = {}

        hz = sum([int(v) for v in cores[0][1:]])
        self.prev, hz = hz, hz - self.prev
        for i,v in enumerate(l[1:]):
            v, self.vals[keys[i]] = float(v) - self.vals[keys[i]], float(v)
            result[keys[i]] = v / hz
        return result
