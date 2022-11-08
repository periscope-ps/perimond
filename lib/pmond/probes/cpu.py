from collections import defaultdict
from pmond.exceptions import ProbeFailure

class CpuProbe(object):
    def __init__(self):
        self.hz = 0
        self.vals = defaultdict(lambda: 0)
    
    @property
    def value(self):
        try:
            with open("/proc/stat", 'r') as f:
                cores = [l.split() for l in f]
        except OSError as e:
            log.error(f"Failed to read /proc/stat - {e}")
            raise ProbeFailure(f"Failed to read /proc/stat - {e}")
        keys = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal", "guest", "guest_nice")
        result = {}

        hz = sum([int(v) for v in cores[0][1:]])
        self.prev, hz = hz, hz - self.prev
        for i,v in enumerate(l[1:]):
            v, self.vals[keys[i]] = float(v) - self.vals[keys[i]], float(v)
            result[keys[i]] = v / hz
        return result
