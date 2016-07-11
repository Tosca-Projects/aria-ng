
from .. import install_aria_extensions, print_exception
from ..loading import PATHS, LiteralLocation
from ..consumption import Implementer
from .utils import CommonArgumentParser, create_parser_ns
from rest_server import start_server
import urllib

def parse(uri):
    parser = create_parser_ns(args, uri=uri)
    return parser.validate()

def validate_get(handler):
    path = urllib.unquote(handler.path[10:])
    _, issues = parse(path)
    return issues or ['No issues']

def implement_get(handler):
    path = urllib.unquote(handler.path[11:])
    presentation, issues = parse(path)
    if not issues:
        Implementer(presentation).consume()
    return issues or ['No issues']

def validate_post(handler):
    payload = handler.get_payload()
    _, issues = parse(LiteralLocation(payload))
    return issues or ['No issues']

def implement_post(handler):
    payload = handler.get_payload()
    presentation, issues = parse(LiteralLocation(payload))
    if not issues:
        Implementer(presentation).consume()
    return issues or ['No issues']

ROUTES = {
    r'^/$': {'file': 'index.html', 'media_type': 'text/html'},
    r'^/validate/': {'GET': validate_get, 'POST': validate_post, 'media_type': 'application/json'},
    r'^/implement/': {'GET': implement_get, 'POST': implement_post, 'media_type': 'application/json'}}

class ArgumentParser(CommonArgumentParser):
    def __init__(self):
        super(ArgumentParser, self).__init__(description='REST Server', prog='aria-rest')
        self.add_argument('--port', type=int, default=8080, help='HTTP port')
        self.add_argument('--root', default='.', help='web root directory')
        self.add_argument('--path', help='path for imports')

def main():
    try:
        install_aria_extensions()
        
        global args
        args, _ = ArgumentParser().parse_known_args()
        if args.path:
            PATHS.append(args.path)
        start_server(ROUTES, args.port, args.root)

    except Exception as e:
        print_exception(e)

if __name__ == '__main__':
    main()
