
from .loader import Loader
from .exceptions import LoaderError, DocumentNotFoundError
import codecs, os.path

PATHS = []

class FileTextLoader(Loader):
    """
    ARIA file text loader.
    
    Extracts a document from a file. The default encoding is UTF-8, but other supported
    encoding can be specified instead.
    
    Supports a list of base paths that are tried in order if the file cannot be found.
    """

    def __init__(self, source, path, paths=[], encoding='utf-8'):
        self.source = source
        self.location = path
        self.paths = PATHS + paths
        self.encoding = encoding
        self.file = None
    
    def open(self):
        try:
            self.file = codecs.open(self.location, mode='r', encoding=self.encoding, buffering=1)
        except IOError as e:
            if e.errno == 2:
                # Not found, so try in paths
                for p in self.paths:
                    path = os.path.join(p, self.location)
                    try:
                        self.file = codecs.open(path, mode='r', encoding=self.encoding, buffering=1)
                        self.location = path
                        return
                    except IOError as e:
                        if e.errno != 2:
                            raise LoaderError('file I/O error: "%s"' % path, cause=e)
                raise DocumentNotFoundError('file not found: "%s"' % self.location, cause=e)
            else:
                raise LoaderError('file I/O error: "%s"' % self.location, cause=e)
        except Exception as e:
            raise LoaderError('file error: "%s"' % self.location, cause=e)

    def close(self):
        if self.file is not None:
            try:
                self.file.close()
            except IOError as e:
                raise LoaderError('file I/O error: "%s"' % self.location, cause=e)
            except Exception as e:
                raise LoaderError('file error: "%s"' % self.location, cause=e)

    def load(self):
        if self.file is not None:
            try:
                return self.file.read()
            except IOError as e:
                raise LoaderError('file I/O error: "%s"' % self.location, cause=e)
            except Exception as e:
                raise LoaderError('file error %s' % self.location, cause=e)
        return None