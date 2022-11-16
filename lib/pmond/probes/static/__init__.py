import logging, platform
from uuid import uuid4
from pmond.probes.static import linux

if platform.uname()[0].lower() == "linux":
    HostReader = linux.HostReader
    PortsReader = linux.PortsReader
