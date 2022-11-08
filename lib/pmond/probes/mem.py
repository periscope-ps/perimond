from pmond import utils

class MemProbe(object):
    @property
    def value(self):
        try:
            with open("/proc/meminfo", 'r') as f:
                lines = [l.split() for l in f]
        except OSError as e:
            log.error(f"Failed to read /proc/meminfo - {e}")
            raise ProbeFailure(f"Failed to read /proc/meminfo - {e}")

        total = 0
        result, m = {}, {"MemFree": "free", "Cached": "cache", "Buffers": "buffer", "Slab": "kernel"}
        for n, *_, v, unit in lines:
            n = n[:-1]
            if n == "MemTotal": total = int(v)
            if n in m:
                result[m[n]] = utils.normalizeBytes(int(v), unit)
        result["used"] = total - result["free"]
        return result
