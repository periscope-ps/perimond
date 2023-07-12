from pmond.utils import args
from pmond.utils.args import Argument
from pmond.version import __version__

template = (
    Argument("-p", "--probes", "", str, "Path to a probe configuration file"),
    Argument("-D", "--dryrun", False, bool, "Print results of measurements to stdout"),
    Argument("-o", "--oneoff", False, bool, "Execute probes once, then terminate"),
    Argument("-r", "--db.remotes", "", str, "Comma delimited list of remote urls"),
    Argument("-l", "--db.ttl", 600, int, "Record TTL (seconds) for generated instances"),
    Argument("-m", "--midfile", "/etc/permond/.mid", str, "Path to a file uniquely identifying this host (file generated automatically as needed)")
)

args = args.from_template(template, desc="System registration and monitoring suite",
                          filevar="$PMOND_CONFPATH",
                          version=__version__)
