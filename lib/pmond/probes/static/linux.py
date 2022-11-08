import logging, netifaces

from pmond import utils
from pmond.exceptions import ProbeFailure

log = logging.getLogger("pmond.sys")

#---------------------------  UUID  ------------------------------------------
class UidProbe(object):
    @property
    def value(self):
        try:
            with open("/etc/machine-id", 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            log.warn("machine-id not found, creating new id")
        uid = str(uuid4()).replace('-', '')
        try:
            with open("/etc/machine-id", 'w') as f:
                f.write(uid)
        except OSError:
            log.error("Insufficent permissions to create machine-id")
            raise ProbeFailure("Insufficent permissions to create machine-id")
        return {"value": uid}
        

#---------------------------  Host  ------------------------------------------
class HostProbe(object):
    def mem(self):
        try:
            with open("/proc/meminfo", 'r') as f:
                lines = [l.lower().split() for l in f]
        except OSError as e:
            log.error(f"Failed to read meminfo - {e}")
            return -1
        unit = "B"
        l = [l for l in lines if any(["memtotal" in x for x in l])]
        if not l:
            log.error("No memtotal value in meminfo")
            return -1
        for v in l[0]:
            if v.isdigit():
                value = int(v)
            elif v in utils.UNITS:
                unit = v
        return utils.normalizeBytes(value, unit)

    def drives(self):
        results = []
        try:
            with open("/proc/partitions", 'r') as f:
                parts = [l.lower().split()[-2:] for l in f][2:]
        except OSError as e:
            log.error(f"Failed to read partitions - {e}")
            return []
        try:
            with open("/proc/mounts", 'r') as f:
                mounts = [l.lower().split() for l in f]
        except OSError as e:
            log.error(f"Failed to read mounts - {e}")
            return []

        for size,n in parts:
            for dev,_,ty,opts,*_ in mounts:
                if dev.endswith(n):
                    opts = [(lambda x: x if len(x)==2 else [x[0], True])(v.split('=')) for v in opts.split(',')]
                    results.append({
                        "type": ty,
                        "size": int(size) * 1024,
                        "options": dict(opts)
                    })

        return results
        
    def cpus(self):
        results, core = [], {}
        try:
            with open("/proc/cpuinfo", 'r') as f:
                lines = [l.lower().split() for l in f]
        except OSError as e:
            log.error(f"Failed to read cpuinfo - {e}")
            return []
        while lines:
            l = lines.pop()
            if not l:
                if core: results.append(core)
                core = {}
            if "model name" in " ".join(l):
                idx = l.index(":") + 1
                core["model"] = " ".join(l[idx:])
            if "cpu mhz" in " ".join(l):
                core["speed"] = float(l[-1])
            if "cache size" in " ".join(l):
                for v in l:
                    if v.isdigit():
                        value = int(v)
                    elif v in utils.UNITS:
                        unit = v
                core["cache"] = utils.normalizeBytes(value, unit)
            if "core id" in " ".join(l):
                core["index"] = l[-1]
            if "flags" in " ".join(l):
                idx = l.index(":") + 1
                core["features"] = {v: True for v in l[idx:]}
        if core: results.append(core)
        return list(sorted(results, key=lambda x: int(x["index"])))

    @property
    def value(self):
        return {
            "memory": {
                "size": self.mem()
            },
            "persistentStorage": self.drives(),
            "cpus": self.cpus()
        }

#--------------------------- Ports  ------------------------------------------
class PortsProbe(object):
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
                results[iface].append(self._copy_props(iface, "ipv4", p, ("addr", "netmask", "broadcast", "peer")))

            try: ports = netifaces.ifaddresses(iface)[netifaces.AF_INET6]
            except KeyError: continue
            for p in ports:
                results[iface].append(self._copy_props(iface, "ipv6", p, ("addr", "netmask", "broadcast", "peer")))
        return results

    @property
    def value(self):
        ifaces = self.get_phys()
        for k,v in self.get_l2(ifaces.keys()).items(): ifaces[k].extend(v)
        for k,v in self.get_l3(ifaces.keys()).items(): ifaces[k].extend(v)
        return ifaces
