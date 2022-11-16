DEFAULT_PROBES = [
    {
        "name": "host",
        "schedule": {"pmond.schedulers.Periodic": { "period": 10 }},
        "probes": {"pmond.probes.static.HostReader": {}}
    },
    {
        "name": "ports",
        "schedule": {"pmond.schedulers.Periodic": { "period": 10 }},
        "probes": {"pmond.probes.static.PortsReader": {}},
        "requires": "host"
    }
]

NODE       = "http://unis.open.sice.indiana.edu/schema/2.0.0/entities/topology/computenode"
PORT       = "http://unis.open.sice.indiana.edu/schema/2.0.0/entities/topology/port"
SERVICE    = "http://unis.open.sice.indiana.edu/schema/2.0.0/entities/topology/service"
MEAUREMENT = "http://unis.open.sice.indiana.edu/schema/2.0.0/entities/measurements/measurement"
METADATA   = "http://unis.open.sice.indiana.edu/schema/2.0.0/entities/measurements/metadata"

REL        = "http://unis.open.sice.indiana.edu/schema/2.0.0/relationship"
