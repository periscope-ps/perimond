import logging, pprint, time, asyncio, json, importlib, signal

from collections import defaultdict
from uuid import uuid4
from pmond import dblayer, probes, config, settings, utils
from pmond.config import Argument
from pmond.probes import static
from pmond.version import __version__

args = (
    Argument("-p", "--probes", "", str, "Path to a probe configuration file"),
    Argument("-D", "--dryrun", False, bool, "Print results of measurements to stdout"),
    Argument("-o", "--oneoff", False, bool, "Execute probes once, then terminate"),
    Argument("-r", "--db.remotes", "", str, "Comma delimited list of remote urls"),
    Argument("-l", "--db.ttl", 600, int, "Record TTL (seconds) for generated instances")
)

"""
[
  {
    "name": "host",
    "schedule": {"pmond.schedulers.Periodic": { "period": 10 }},
    "probes": {"pmond.probes.static.HostReader": {}},
  },
  {
    "schedule": {"pmond.schedulers.Periodic": { "period": 10 }},
    "probes": {"pmond.probes.static.PortsReader": {}},
  },
  {
    "schedule": {"pmond.schedulers.Periodic": {}},
    "probes": {"pmond.probes.CpuReader": {}},
    "requires": "host"
  }
]
"""


log = utils.baselog
class Manager(object):
    def __init__(self, conf):
        self.runners = []
        self._c = conf
        self._dryrun = []

    @property
    def record(self):
        return self._dryrun
    async def _apply(self, name, sched, deps):
        loop = asyncio.get_event_loop()
        first = True
        async for v in sched:
            for s in v[0] + v[1]:
                if hasattr(s, "expires"):
                    s.expires = int((time.time() + self._c["db"]["ttl"]) * 1_000_000)
            if self._c["dryrun"]:
                for s in v[0]:
                    s = dict(s)
                    s[":ts"] = int(time.time() * 1_000_000)
                    self._dryrun.append(s)
                for p in v[1]:
                    s = dict(s)
                    s[":ts"] = int(time.time() * 1_000_000)
                    self._dryrun.append(s)
            else:
                # TMP
                pprint.pprint({"static": v[0], "meas": v[1]})
                # TODO: DBLayer
                pass
            if first:
                first = False
                for n,task in deps.get(name, []):
                    log.info(f"Starting probe runner {'- ' + name if name else ''}")
                    self.runners.append(loop.create_task(self._apply(name, task, deps)))

    def load(self):
        if self._c["probes"]:
            try:
                with open(self._c["probes"], 'r') as f:
                    log.info(f"Reading probefile - '{self._c['probes']}'")
                    probes = json.load(f)
            except OSError:
                log.error("Cannot load probes")
                exit(-1)
        else:
            log.info("Loading default probes")
            probes = settings.DEFAULT_PROBES
        tasks, deps = [], defaultdict(list)
        for p in probes:
            readers = []
            for k,v in p["probes"].items():
                path = k.split('.')
                readers.append(getattr(importlib.import_module(".".join(path[:-1])), path[-1])(**v))
            for k,v in p["schedule"].items():
                if self._c["dryrun"] or self._c["oneoff"]:
                    k,v = "pmond.schedulers.once.Once", {}
                path = k.split('.')
                Sched = getattr(importlib.import_module(".".join(path[:-1])), path[-1])
                for reader in readers:
                    sched = Sched(reader, **v)
                    if "requires" in p:
                        deps[p["requires"]].append((p.get("name", None), sched))
                    else:
                        tasks.append((p.get("name", None), sched))

        loop = asyncio.get_event_loop()
        for name,task in tasks:
            log.info(f"Starting probe runner {'- ' + name if name else ''}")
            self.runners.append(loop.create_task(self._apply(name, task, deps)))

    async def start(self):
        while self.runners:
            try:
                await asyncio.gather(*self.runners)
            except asyncio.exceptions.CancelledError: pass
            self.runners = [r for r in self.runners if not r.done()]

    def restart(self):
        for r in self.runners: r.cancel()
        self.load()

def main():
    conf = config.from_template(args, desc="System registration and monitoring suite",
                                filevar="$PMOND_CONFPATH",
                                version=__version__)
    manager = Manager(conf)
    signal.signal(signal.SIGHUP, lambda signum, frame: manager.restart())
    manager.load()
    asyncio.get_event_loop().run_until_complete(manager.start())
    if conf["dryrun"]:
        print(json.dumps(manager.record, indent=2))

if __name__ == "__main__":
    main()
