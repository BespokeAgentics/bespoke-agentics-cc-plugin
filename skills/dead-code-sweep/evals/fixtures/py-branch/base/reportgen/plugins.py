import json


def emit_json(report):
    return json.dumps({"report": report})


def emit_text(report):
    return str(report)
