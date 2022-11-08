import mundus, logging, json

from collections import defaultdict
from mundus.models import get_class

ComputeNode = get_class("http://unis.open.sice.indiana.edu/schema/2.0.0/entities/topology/computenode")
Port = get_class("http://unis.open.sice.indiana.edu/schema/2.0.0/entities/topology/port")
def get_node(uid, ttl):
    return ComputeNode({
        "status": "ON",
        "expires": int(ttl),
        ":id": uid
    })

log = logging.getLogger("pmond.mundus")
class Client(object):
    def __init__(self, uid, conf):
        for remote in conf["general"]["remotes"].split(","):
            mundus.connect(remote)
        self._n = (mundus.Q().id == uid).first()
        if not self._n:
            self._n = mundus.add(get_node(uid, conf["db"]["ttl"]))
        self.local = bool(conf["general"]["remotes"])

    def _unify_node(self, sys):
        # Adust memory
        if self._n.memory.size != sys["memory"]["size"]: self._n.memory.size = sys["memory"]["size"]

        # Adjust cpus
        i = 0
        while len(sys["cpus"]) < len(self._n.cpus):
            self._n.cpus.pop()

        for i,d in enumerate(sys["cpus"]):
            try:
                c = self._n.cpus[i]
                c.speed, c.model, c.features = d["speed"], d["model"], d["features"]
            except IndexError:
                self._n.cpus.append({"speed": d["speed"], "model": d["model"], "features": d["features"]})

            try:
                c = self._n.cache[i]
                c.level, c.size, c.serves = 1, d["cache"], i
            except IndexError:
                self._n.cache.append({"level": 1, "size": d["cache"], "serves": i})
        
        # Adjust disks
        for i,d in enumerate(sys["persistentStorage"]):
            try:
                s = self._n.persistentStorage[i]
                s.type, s.size, s.options = d["type"], d["size"], d["options"]
            except IndexError:
                self._n.persistentStorage.append({"type": d["type"], "size": d["size"], "options": d["options"]})

        log.debug(json.dumps(dict(self._n), indent=2))

    def _unify_ports(self, ports):
        objs, contains = [], defaultdict(list)
        def from_name(v):
            for v in objs:
                if obj.addr == v: return v
            n,vlan = v.split('.')
            conts = contains[n]
            for obj in conts:
                if obj.addr == v: return v
                
        for n,ls in ports.items():
            isvlan = n.split('.')
            if len(isvlan) == 1:
                objs.append(Port({"address": n, "addressType": "iface"}))
            else:
                vlan = objs.append(Port({"address": isvlan[1], "addressType": "vlan"}))
                contains[isvlan[0]].append(vlan)

            for d in ls:
                addr = objs.append(Port({"address": d["addr"], "addressType": d["type"]}))
                contains[n].append(addr)

        if not self.local:
            # TODO
            pass
        contains = {from_name(k): v for k,v in contains.items()}
        log.debug(json.dumps([dict(v) for v in objs], indent=2))
        log.debug(json.dumps([{"subject": getattr(k, ":id"),
                               "target": getattr(v, ":id")} for k,ls in contains.items() for v in ls])

    def register(self, sys, ports):
        self._unify_node(sys)
        self._unify_ports(ports)
        mundus.publish()

