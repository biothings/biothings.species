''' Taxonomy Local Test '''

from nose.core import run

from biothings.tests import TornadoTestServerMixin
from tests.remote import MySpeciesTest
from web.settings import MySpeciesWebSettings


class MySpeciesLocalTest(TornadoTestServerMixin, MySpeciesTest):
    '''
        Starts a Tornado server on its own and perform tests against this server.
        Requires config.py under src folder.
    '''

    __test__ = True

    # Override default setting loader
    settings = MySpeciesWebSettings(config='config')


if __name__ == '__main__':
    print()
    print('MyGene Local Test')
    print('-'*70)
    print()
    run(argv=['', '--logging-level=INFO', '-v', '--logging-clear-handlers'],
        defaultTest='__main__.MySpeciesLocalTest')
