"""Rate limiting via slowapi, keyed by client IP address.

If the demo happens on one venue Wi-Fi network,
multiple attendees can share a single public IP (NAT), so this limiter
throttles everyone behind that IP together, not just one person. The
default limits in config.py (15/min submit, 60/min list) are set generously
to tolerate a room full of people on shared Wi-Fi -- raise them further in
.env if real testing shows legitimate submissions getting 429'd.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
