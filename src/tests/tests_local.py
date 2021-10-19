import pytest
from biothings.tests.web import BiothingsWebAppTest


class MyTaxonTests(BiothingsWebAppTest):
    TEST_DATA_DIR_NAME = 'MyTaxonTestData'

    def test_include_children_post(self):
        res = self.request(
            'taxon', method='POST',
            data={
                'ids': ['1280'],
                'include_children': True
            }
        ).json()
        assert self.value_in_result(282459, res, 'children')
        assert self.value_in_result(1346071, res, 'children')

    def test_include_children_get(self):
        res = self.request(
            'taxon/1280', method='GET',
            params={
                'include_children': 1
            }
        ).json()
        assert self.value_in_result(282459, res, 'children')
        assert self.value_in_result(1346071, res, 'children')

    def test_include_children_has_gene(self):
        res = self.request(
            'taxon', method='POST',
            data={
                'ids': ['1280'],
                'include_children': True,
                'has_gene': True,
            }
        ).json()
        for child in res[0]['children']:
            ch_res = self.request(f'taxon/{child}').json()
            assert ch_res['has_gene']

    def test_expand(self):
        test_id = '1280'
        r1 = self.request(
            'taxon', method='POST',
            data={
                'ids': [test_id],
                'include_children': True,
            }
        ).json()
        r2 = self.request(
            'taxon', method='POST',
            data={
                'ids': [test_id],
                'include_children': True,
                'expand_species': True,
            }
        ).json()
        # sometimes it is an integer, sometimes a str
        r1l = [str(r1[0]['_id'])]
        r1l.extend(str(i) for i in r1[0]['children'])
        r1s = set(r1l)
        r2s = set(str(i) for i in r2)
        assert r1s == r2s
