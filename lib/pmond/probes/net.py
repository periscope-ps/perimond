import asyncio
from pmond import utils
from pmond.exceptions import ProbeFailure
from pmond.probes.abc import NodeProbe, ProbeResult, Measurement, Reader

log = utils.baselog.getChild("probe.mem")
class NetReader(Reader):
    async def read(self):
        log.debug("Reading [net]")
        probe = NetProbe()
        uid, results = await asyncio.gather(probe.subject(), probe.run())
        pid = f"uuid:port:{uid.split(':')[-1]}"
        meas = []
        for n,v in results.items():
            prefix,n = n.split(":", 1)
            if prefix == "snmp":
                meas.append(Measurement(uid, f"blipp:net:{n}", v))
            else:
                meas.append(Measurement(f"{pid}:{n.split(':')[0]}", f"blipp:net:{n}", v))
        return ProbeResult([], meas)

class NodeProbe(FileProbe):
    async def run(self):
        devs, snmp = await asyncio.gather(self.readfile("/proc/net/dev"),
                                          self.readfile("/proc/net/snmp"))
        if devs is None:
            raise ProbeFailure("Could not read file '/proc/net/dev'")
        if snmp is None:
            raise ProbeFailure("Could not read file '/proc/net/snmp'")

        result, keys, rows = {}, {}, {}
        for l in [d.split() for d in devs.split('\n')[2:]]:
            for idx,n in enumerate(["bytes", "packets", "errs", "drop"]):
                for d,offset in [("in",1), ("out",9)]:
                    result[f"dev:{l[0]}{n}:{d}"] = int(l[idx+offset])

        for i,l in enumerate([v.split() for v in snmp.split('\n')]):
            if not l[1].isdigit():
                keys[l[0]] = {k.lower(): i+1 for i,k in enumerate(l[1:])}
            else:
                rows[l[0][:-1].lower()] = i
        for ty,m,a in [("tcp","insegs","segments:in"), ("tcp","outsegs","segments:out"),
                       ("tcp","retranssegs","retrans"), ("udp", "indatagrams", "datagrams:in"),
                       ("udp", "outdatagrams", "datagrams:out")]:
            result[f"snmp:{ty}:{a}"] = snmp[rows[ty]][keys[m]]
        return result
