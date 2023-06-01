# pylint: disable=C0103
# pylint: disable=C0111
# pylint: disable=R0921
# pylint: disable=W0212


import abc
import os
import shutil
import tempfile
from contextlib import closing, contextmanager

import requests

import gutenberg.acquire.text
from gutenberg.acquire.metadata import (BerkeleyDBMetadataCache,
                                        set_metadata_cache)

INTEGRATION_TESTS_ENABLED = bool(os.getenv('GUTENBERG_RUN_INTEGRATION_TESTS'))


# noinspection PyPep8Naming,PyAttributeOutsideInit
class MockTextMixin:
    def setUp(self):
        self.mock_text_cache = tempfile.mkdtemp()
        set_text_cache(self.mock_text_cache)

    def tearDown(self):
        shutil.rmtree(self.mock_text_cache)


# noinspection PyPep8Naming,PyAttributeOutsideInit
class MockMetadataMixin(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def sample_data(self):
        raise NotImplementedError  # pragma: no cover

    def setUp(self):
        self.cache = _BerkeleyDBMetadataCacheForTesting(self.sample_data, 'nt')
        self.cache.populate()
        set_metadata_cache(self.cache)

    def tearDown(self):
        set_metadata_cache(None)
        self.cache.delete()


class _BerkeleyDBMetadataCacheForTesting(BerkeleyDBMetadataCache):
    def __init__(self, sample_data_factory, data_format):
        BerkeleyDBMetadataCache.__init__(self, tempfile.mktemp())
        self.sample_data_factory = sample_data_factory
        self.data_format = data_format

    def populate(self):
        BerkeleyDBMetadataCache.populate(self)

        data = '\n'.join(item.rdf() for item in self.sample_data_factory())

        self.graph.open(self.cache_uri, create=True)
        with closing(self.graph):
            self.graph.parse(data=data, format=self.data_format)

    @contextmanager
    def _download_metadata_archive(self):
        yield None

    @classmethod
    def _iter_metadata_triples(cls, metadata_archive_path):
        return []


def set_text_cache(cache):
    gutenberg.acquire.text._TEXT_CACHE = cache


def always_throw(exception_type):
    """Factory to create methods that throw exceptions.

    Args:
        exception_type: The type of exception to throw

    Returns:
        function: A function that always throws an exception when called.

    """
    # noinspection PyUnusedLocal
    def wrapped(*args, **kwargs):
        raise exception_type
    return wrapped


def detect_mirror():
    """Detects working mirrors of Project Gutenberg.

    Returns:
       string: First working mirror found
    """

    mirrors = (
        "http://www.mirrorservice.org/sites/ftp.ibiblio.org/pub/docs/books/gutenberg/", "http://eremita.di.uminho.pt/gutenberg/", 
        "http://mirror.csclub.uwaterloo.ca/gutenberg/", "https://gutenberg.nabasny.com/", 
        "https://www.gute1nberg.org/dirs/", "https://mirror2.sandyriver.net/pub/gutenberg", "http://mirrors.xmission.com/gutenberg/", 
        "https://aleph.gutenberg.org/", "https://gutenberg.pglaf.org/")
    
    for mirror in mirrors:
        if requests.head(mirror).status_code == 200:
            return mirror
            break 
