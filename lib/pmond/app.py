import logging, pprint, time, asyncio, json, importlib, signal

from collections import defaultdict
from uuid import uuid4
from pmond import dblayer, probes, settings, config, utils
from pmond.probes import static

log = utils.baselog
class Manager(object):
    def __init__(self, conf):
        self.runners = []
        self._c = conf
        self._dryrun = defaultdict(list)

    @property
    def record(self):
        return self._dryrun

    async def _apply(self, name, sched, deps):
        loop = asyncio.get_event_loop()
        first = True
        async for v in sched:
            for s in sum([x for k,x in v[0].items()], []) + v[1]:
                if hasattr(s, "ttl"):
                    s.expires = int(self._c["db"]["ttl"]) * 1_000_000
            if self._c["dryrun"]:
                for k,ls in v[0].items():
                    for s in ls:
                        s = dict(s)
                        s[":ts"] = int(time.time() * 1_000_000)
                        self._dryrun[k].append(s)
                for p in v[1]:
                    s = dict(s)
                    s[":ts"] = int(time.time() * 1_000_00)
                    self._dryrun["meas"].append(s)
            else:
                # TMP
                pprint.pprint({"static": v[0], "meas": v[1]})
                # TODO: DBLayer [send results to the mundus database]
            if first:
                first = False
                for n,task in deps.get(name, []):
                    log.info(f"Starting probe runner {'- ' + n if n else ''}")
                    self.runners.append(loop.create_task(self._apply(n, task, deps)))

    def load(self):
        if self._c["probes"]:
            try:
                with open(self._c["probes"], 'r') as f:
                    log.info(f"Reading probefile - '{self._c['probes']}'")
                    pconfig = json.load(f)
            except OSError:
                log.error("Cannot load probes file")
                exit(-1)
        else:
            log.info("Loading default probes")
            pconfig = settings.DEFAULT_PROBES
        tasks, deps = [], defaultdict(list)
        for event in pconfig:
            readers = []
            for k,v in event["probes"].items():
                path = k.split('.')
                try:
                    if "midfile" in v:
                        v["midfile"] = self._c["midfile"]
                    cls = getattr(importlib.import_module(".".join(path[:-1])), path[-1])
                    readers.append(cls(**v))
                except ImportError:
                    log.error(f"Failed to load probe module - '{k}'")
            for k,v in event["schedule"].items():
                if self._c["dryrun"] or self._c["oneoff"]:
                    k,v = "pmond.schedulers.once.Once", {}
                path = k.split('.')
                try:
                    Schedule = getattr(importlib.import_module(".".join(path[:-1])), path[-1])
                except ImportError:
                    log.error(f"Failed to load schedule module - '{k}'")
                for reader in readers:
                    probe = Schedule(reader, **v)
                    if "requires" in event:
                        deps[event["requires"]].append((event.get("name", None), probe))
                    else:
                        tasks.append((event.get("name", None), probe))

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
    manager = Manager(config.args)
    signal.signal(signal.SIGHUP, lambda signum, frame: manager.restart())
    manager.load()
    asyncio.get_event_loop().run_until_complete(manager.start())
    if config.args["dryrun"]:
        print(json.dumps(manager.record, indent=2))

if __name__ == "__main__":
    main()
