from pmond import utils
from pmond.exceptions import ProbeFailure

class NetProbe(object):
    @property
    def value(self):
        try:
            with open("/proc/net/dev", 'r') as f:
                devs = [l.split() for l in f][2:]
        except OSError as e:
            log.error(f"Failed to read /proc/net/dev - {e}")
            raise ProbeFailure(f"Failed to read /proc/net/dev - {e}")
        try:
            with open("/proc/net/snmp", 'r') as f:
                snmp = [l.split() for l in f]
        except OSError as e:
            log.error(f"Failed to read /proc/net/snmp - {e}")
            raise ProbeFailure(f"Failed to read /proc/net/snmp - {e}")

        result = {}
        for l in devs:
            for idx,n in enumerate(["bytes", "packets", "errs", "drop"]):
                for d,offset in [("in",1), ("out",9)]:
                    result[f"{l[0]}{n}:{d}"] = int(l[idx+offset])

        keys = {}
        rows = {}
        for i,l in enumerate(snmp):
            if not l[1].isdigit():
                keys[l[0]] = {k.lower(): i+1 for i,k in enumerate(l[1:])}
            else:
                rows[l[0][:-1].lower()] = i
        for ty,m,a in [("tcp","insegs","segments:in"), ("tcp","outsegs","segments:out"),
                       ("tcp","retranssegs","retrans"),
                       ("udp", "indatagrams", "datagrams:in"), ("udp", "outdatagrams", "datagrams:out")]:
            result[f"{ty}:{a}"] = snmp[rows[ty]][keys[m]]
        return result
