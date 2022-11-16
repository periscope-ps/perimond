import logging, netifaces, asyncio, socket
from uuid import uuid4

from mundus.models import get_class

from pmond import utils, settings
from pmond.probes.abc import FileProbe, ProbeResult, Reader
from pmond.exceptions import ProbeFailure

log = utils.baselog.getChild("probe.host")

#---------------------------  Host  ------------------------------------------
Node = get_class(settings.NODE)
class HostReader(Reader):
    async def read(self):
        log.debug("Reading [host]")
        host = await HostProbe().run()
        result = Node({"name": host['name'], "urn": host['id'],
                       "memory": {"size": host["memory"]["size"], "type": "ram"}})
        for s in host["persistentStorage"]:
            result.persistentStorage.append({"type": s["type"], "size": s["size"], "options": s["options"]})
        for i,c in enumerate(sorted(host["cpus"], key=lambda x: x["index"])):
            result.cpus.append({"model": c["model"], "speed": c["speed"], "features": c["features"]})
            result.cache.append({"level": 1, "size": c["cache"], "serves": i})
        return ProbeResult([result], [])

class HostProbe(FileProbe):
    async def mem(self):
        lines = await self.readfile("/proc/meminfo")
        if lines is None:
            raise ProbeFailure("Could not read file '/proc/meminfo'")
        unit, result, value = "B", None, None
        for l in lines.lower().split('\n'):
            if "memtotal" in l:
                result = l.split()
        if not result:
            raise ProbeFailure("No 'memtotal' field in meminfo")
        for v in result:
            if v.isdigit(): value = int(v)
            elif v in utils.UNITS: unit = v
        if not value:
            raise ProbeFailure("Unable to parse 'memtotal field in meminfo")
        return utils.normalizeBytes(value, unit)

    async def drives(self):
        def fn(x):
            if len(x) == 2:
                return x
            else:
                return [x[0], True]
        results = []
        parts, mounts = await asyncio.gather(self.readfile("/proc/partitions"),
                                             self.readfile("/proc/mounts"))
        if parts is None:
            raise ProbeFailure("Could not read file '/proc/partitions'")
        if mounts is None:
            raise ProbeFailure("Could not read file '/proc/mounts'")
        for size,n in [p.split()[-2:] for p in parts.lower().split('\n')[2:] if p]:
            for dev,_,ty,opts,*_ in [m.split() for m in mounts.lower().split('\n') if m]:
                if dev.endswith(n):
                    results.append({
                        "type": ty,
                        "size": int(size) * 1024,
                        "options": dict([fn(v.split('=')) for v in opts.split(',')]),
                        "name": n
                    })
        return results

    async def cpus(self):
        def toByte(v):
            for x in v.split():
                if x.isdigit(): val = int(x)
                elif x in utils.UNITS: unit = x
            return utils.normalizeBytes(val, unit)

        results, core = [], {}
        lines = await self.readfile("/proc/cpuinfo")
        if lines is None:
            raise ProbeFailure("Could not read file '/proc/cpuinfo")
        for l in [l.split() for l in lines.lower().split('\n')]:
            try:
                idx = l.index(":")
                k,v = " ".join(l[:idx]), " ".join(l[idx+1:])
            except ValueError:
                if core:
                    results.append(core)
                core = {}
            if "model name" in k: core["model"] = v
            elif "cpu mhz" in k: core["speed"] = float(v)
            elif "cache size" in k: core["cache"] = toByte(v)
            elif "core id" in k: core["index"] = int(v)
            elif "flags" in k: core["features"] = {v: True for v in v.split()}
        if core: results.append(core)
        return list(sorted(results, key=lambda x: int(x["index"])))

    async def run(self):
        results = await asyncio.gather(self.machineid(), self.mem(), self.drives(), self.cpus())
        name = socket.getfqdn()
        if name == "localhost":
            name = ''
        return {
            "name": socket.getfqdn(),
            "id": results[0],
            "memory": { "size": results[1] },
            "persistentStorage": results[2],
            "cpus": results[3]
        }

#--------------------------- Ports  ------------------------------------------
Port = get_class(settings.PORT)
Relationship = get_class(settings.REL)
class PortsReader(Reader):
    async def read(self):
        log.debug("Reading [ports]")
        results = []
        for k,v in (await PortsProbe().run()).items():
            l2s = []
            phy = Port({"urn": k,"addressType": "phy", "address": k.split(':')[-1]})
            for l2 in v:
                if l2["type"] == "eth":
                    p = Port({"addressType": l2["type"], "address": l2["addr"]})
                    results.append(Relationship({"subject": phy, "target": p}))
                    results.append(p)
                    l2s.append(p)
            for l3 in v:
                if l3["type"] in ["ipv4", "ipv6"]:
                    p = Port({"addressType": l3["type"], "address": l3["addr"]})
                    for l2 in l2s:
                        results.append(Relationship({"subject": l2, "target": p}))
                    results.append(p)
        return ProbeResult(results, [])

class PortsProbe(FileProbe):
    def _copy_props(self, iface, ty, vals, props):
        k = set(vals.keys())
        p = set(props)
        for n in k - p: # Values not in `props`
            log.debug(f"Unknown field in interface - {iface} {ty}.{n}")
        for n in p - k: # Values not in `vals`
            log.debug(f"Field not in interface - {iface} {ty}.{n}")

        return {**{k: vals.get(k, None) for k in props}, **{"type": ty}}

    def get_phys(self):
        return {n: [] for n in netifaces.interfaces()}

    def get_l2(self, ifaces):
        results = {n: [] for n in ifaces}
        for iface in ifaces:
            try: ports = netifaces.ifaddresses(iface)[netifaces.AF_LINK]
            except KeyError: continue

            for p in ports:
                results[iface].append(self._copy_props(iface, "eth", p, ("addr", "broadcast", "peer")))
        return results

    def get_l3(self, ifaces):
        results = {n: [] for n in ifaces}
        for iface in ifaces:
            try: ports = netifaces.ifaddresses(iface)[netifaces.AF_INET]
            except KeyError: continue

            for p in ports:
                results[iface].append(self._copy_props(iface, "ipv4", p, ("addr", "netmask",
                                                                          "broadcast", "peer")))

            try: ports = netifaces.ifaddresses(iface)[netifaces.AF_INET6]
            except KeyError: continue
            for p in ports:
                results[iface].append(self._copy_props(iface, "ipv6", p, ("addr", "netmask",
                                                                          "broadcast", "peer")))
        return results

    async def run(self):
        uid = await self.machineid()
        pid = f"uuid:port:{uid.split(':')[-1]}"
        ifaces = self.get_phys()
        for k,v in self.get_l2(ifaces.keys()).items(): ifaces[k].extend(v)
        for k,v in self.get_l3(ifaces.keys()).items(): ifaces[k].extend(v)
        return {f"{pid}:{k}": v for k,v in ifaces.items()}
