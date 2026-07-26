from . import plugins

FORMATS = {"json": "emit_json", "text": "emit_text"}


def export(report, fmt):
    return getattr(plugins, FORMATS[fmt])(report)
