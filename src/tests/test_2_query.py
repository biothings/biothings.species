from operator import contains
from biothings.tests.web import BiothingsDataTest

"""
Test Cases
/v1/query?q=rat
/v1/query?q=scientific_name:homo sapiens
/v1/query?q=parent_taxid:9605
POST /v1/query
q=9606&scopes=taxid
POST /v1/query
q=homo sapiens&scopes=scientific_name
"""

class TestQueryGET(BiothingsDataTest):
    # host = 't.biothings.io'
    host = '34.221.9.181'
    prefix = 'v1'

    def test_201(self):

        res = self.request('query?q=rat').json()

        assert res['total'] >= 214

    def test_202(self):
        
        res = self.request('query?q=scientific_name:homo sapiens').json()
        
        assert 'hits' in res
        assert len(res['hits']) >= 10

    def test_203(self):
        
        res = self.request('query?q=parent_taxid:9605').json()
        
        assert 'hits' in res
        assert len(res['hits']) >= 4

class TestQueryPOST(BiothingsDataTest):
    host = 't.biothings.io'
    # host = '34.221.9.181'
    prefix = 'v1'

    def test_201_post(self):

        data = {'q': '9606', 'scopes': 'taxid'}
        res = self.request('query', method='POST', data=data).json()

        assert len(res) == 1
        assert set(res[0].keys()) == set(['query', '_id', '_score', 'authority', 'genbank_common_name', 'has_gene', 'lineage', 'parent_taxid', 'rank', 'scientific_name', 'taxid', 'uniprot_name'])
        assert res[0]['_id'] == '9606'

    def test_202_post(self):

        data = {'q': 'homo sapiens', 'scopes': 'scientific_name'}
        res = self.request('query', method='POST', data=data).json()
        
        assert len(res) >= 20
        assert set(res[0].keys()) == set(['query', '_id', '_score', 'authority', 'common_name', 'has_gene', 'lineage', 'parent_taxid', 'rank', 'scientific_name', 'taxid'])
        assert res[0]['_id'] == '9605'
        assert res[1]['_id'] == '1425170'
