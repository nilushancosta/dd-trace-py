import requests

from wrapt import wrap_function_wrapper as _w

from ddtrace import config
from ddtrace.pin import Pin

from ...util import asbool, get_env, unwrap as _u
from .legacy import _distributed_tracing, _distributed_tracing_setter
from .constants import DEFAULT_SERVICE
from .connection import _wrap_request


# requests default settings
config._add('requests',{
    'service_name': get_env('requests', 'service_name', DEFAULT_SERVICE),
    'distributed_tracing': asbool(get_env('requests', 'distributed_tracing', False)),
})


def patch():
    """Activate http calls tracing"""
    if getattr(requests, '__datadog_patch', False):
        return
    setattr(requests, '__datadog_patch', True)

    _w('requests', 'Session.request', _wrap_request)
    Pin(
        service=config.requests['service_name'],
        _config=config.requests,
    ).onto(requests.Session)

    # [Backward compatibility]: `session.distributed_tracing` should point and
    # update the `Pin` configuration instead. This block adds a property so that
    # old implementations work as expected
    fn = property(_distributed_tracing)
    fn = fn.setter(_distributed_tracing_setter)
    requests.Session.distributed_tracing = fn


def unpatch():
    """Disable traced sessions"""
    if not getattr(requests, '__datadog_patch', False):
        return
    setattr(requests, '__datadog_patch', False)

    _u(requests.Session, 'request')
