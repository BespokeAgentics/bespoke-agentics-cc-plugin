from .utils import wrap_text


def render_html_legacy(title, body, width=72):
    wrapped = wrap_text(body, width)
    return "<html><h1>%s</h1><pre>%s</pre></html>" % (title, wrapped)
