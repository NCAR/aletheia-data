from urllib.parse import urlsplit


def infer_protocol_options(urlpath):
    parsed_path = urlsplit(urlpath)
    protocol = parsed_path.scheme or 'file'
    return {'protocol': protocol, 'path': urlpath}
