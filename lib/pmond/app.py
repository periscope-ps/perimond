import logging, pprint, time
from uuid import uuid4
from pmond import dblayer, probes#, config
from pmond.probes import static

log = logging.getLogger("pmod")
def run_forever(db, sys, interval):
    while True:
        db.register(sys.get_stats(), sys.get_ports())
        time.sleep(interval)

def main():
    #conf = config.MultiConfig()
    uid = static.UidProbe().value
    ps = {
        "host": static.HostProbe(),
        "ports": static.PortsProbe()
    }
    #db = dblayer.load(conf["db"]["client"])(uid, conf)
    log.info(f"Registering node [{uid}] at")# {dst}")

    #if conf["general"]["dryrun"]:
    pprint.pprint(ps["host"].value)
    print()
    pprint.pprint(ps["ports"].value)
    #elif conf["general"]["oneoff"]:
    #    db.register(sys.get_stats(), sys.get_ports())
    #else:
    #    run_forever(db, sys, conf["general"]["interval"])

if __name__ == "__main__":
    main()
