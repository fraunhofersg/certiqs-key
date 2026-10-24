"""Re-export of the route names, kept so a golden test stays byte-identical.

A golden test imports ``ROUTES`` from here;
the routes themselves are the template's ``route`` domain and
:data:`instances.common.passive_device.ROUTES` (one of the two shims the
golden tests need).
"""

from instances.common.passive_device import ROUTES as ROUTES
