''' Taxonomy RemoteTest '''

from nose.core import runmodule

from biothings.tests.tests import BiothingGenericTests


class MySpeciesTest(BiothingGenericTests):

    __test__ = True  # explicitly set this to be a test class

    # Add extra nosetests here


if __name__ == '__main__':
    print()
    print('MyVariant Remote Test:', MySpeciesTest.host)
    print('-'*70)
    runmodule(argv=['', '--logging-level=INFO', '-v'])
