from operator import contains
from biothings.tests.web import BiothingsDataTest

"""
Test Cases
/v1/taxon/9606
/v1/taxon/9606?fields=taxid,scientific_name,has_gene
/v1/taxon/9606?include_children=1
/v1/query?q=207598&include_children
/v1/query?q=207598&include_children&has_gene
/v1/query?q=lineage:9606
/v1/query?q=lineage:9606 AND has_gene:false
POST /v1/taxon
ids=9606
POST /v1/taxon?expand_species 
ids=9605,9606
POST /v1/taxon?expand_species
ids=9605,9606&fields=has_gene,scientific_name,lineage
"""

class TestAnnotationGET(BiothingsDataTest):
    host = 't.biothings.io'
    prefix = 'v1'

    def test_101(self):
        res = self.request('taxon/9606').json()
        taxon = {
                    "_id": "9606",
                    "authority": [
                    "homo sapiens linnaeus, 1758"
                    ],
                    "genbank_common_name": "human",
                    "has_gene": True,
                    "lineage": [
                        9606,9605,207598,9604,314295,9526,314293,
                        376913,9443,314146,1437010,9347,32525,
                        40674,32524,32523,1338369,8287,117571,
                        117570,7776,7742,89593,7711,33511,33213,
                        6072,33208,33154,2759,131567,1
                    ],
                    "parent_taxid": 9605,
                    "rank": "species",
                    "scientific_name": "homo sapiens",
                    "taxid": 9606,
                    "uniprot_name": "homo sapiens"
                }
        # Is taxon a subset of res?
        assert taxon.items() <= dict(res).items()

    def test_102(self):
        res = self.request('taxon/9606?fields=taxid,scientific_name,has_gene').json()
        taxon = {
            "_id": "9606",
            "has_gene": True,
            "scientific_name": "homo sapiens",
            "taxid": 9606,
        }

        # Is taxon a subset of res?
        assert taxon.items() <= dict(res).items()

    def test_103(self):

        res_children = self.request('taxon/9606?include_children=1').json()
        assert 'children' in res_children

        # should include a "children" field comparing to the first example
        taxon_id = res_children['children'][0]
        assert taxon_id == 63221

        res_taxon = self.request('taxon/' + str(taxon_id)).json()
        # Tuple is ordered, unchangeable, and allows duplicate members.
        assert tuple(res_taxon) == tuple(['_id', '_version', 'authority', 
                        'common_name', 'genbank_common_name', 'has_gene', 
                        'lineage', 'other_names', 'parent_taxid', 'rank',
                        'scientific_name', 'taxid', 'type material', 'uniprot_name'])

        assert res_taxon['_id'] == "63221"
        assert "homo sapiens neanderthalensis king, 1864" in res_taxon['authority']
        assert tuple(["neandertal man","neanderthal","neanderthal man"]) == tuple(res_taxon['common_name'])
        assert res_taxon['genbank_common_name'] == "neandertal"
        assert res_taxon['has_gene'] == True
        assert "homo neanderthalensis" in res_taxon['other_names']
        assert res_taxon['parent_taxid'] == 9606
        assert res_taxon['rank'] == "subspecies"
        assert res_taxon['scientific_name'] == "homo sapiens neanderthalensis"
        assert res_taxon['taxid'] == 63221
        assert tuple(['feldhofer 1','neanderthal 1']) == tuple(res_taxon['type material'])
        assert res_taxon['uniprot_name'] == "homo sapiens neanderthalensis"

        lineages = [
            63221, 9606, 9605, 207598, 9604, 314295, 9526, 314293,
            376913, 9443, 314146, 1437010, 9347, 32525, 40674, 32524,
            32523, 1338369, 8287, 117571, 117570, 7776, 7742, 89593,
            7711, 33511, 33213, 6072, 33208, 33154, 2759, 131567, 1
        ]

        for lineage in lineages:
            assert lineage in res_taxon['lineage']

    def test_104(self):
        res_without_has_gene = self.request('query?q=207598&include_children').json()
        res_with_has_gene = self.request('query?q=207598&include_children&has_gene').json()
        assert len(res_without_has_gene['hits'][0]['children']) > len(res_with_has_gene['hits'][0]['children'])

    def test_105(self):
        res = self.request('query?q=lineage:9606').json()
        assert 'hits' in res
        assert len(res['hits']) == 3

    def test_106(self):
        res = self.request('query?q=lineage:9606 AND has_gene:false').json()
        assert 'hits' in res
        assert len(res['hits']) == 0

    def test_107(self):
        """ GET /v1/taxon/
        {
            "code": 400,
            "success": false,
            "error": "Bad Request",
            "missing": "id"
        }
        """
        self.request('taxon', expect=400)

    def test_108(self):
        self.request('taxon/', expect=400)


class TestAnnotationPOST(BiothingsDataTest):
    host = 't.biothings.io'
    prefix = 'v1'

    def test_109(self):
        res = self.request('taxon', method='POST', data={'ids': '9606'}).json()
        assert len(res) == 1
        assert res[0]['taxid'] == 9606

        # check default fields returned
        default_fields = [
            'query', '_id', '_version', 'authority', 'genbank_common_name', 'has_gene',
            'lineage', 'parent_taxid', 'rank', 'scientific_name', 'taxid', 'uniprot_name']

        for field in default_fields:
            assert field in res[0]
        assert len(default_fields) <= len(res[0])

    def test_110(self):
        res = self.request('taxon', method='POST', data={'ids': '9605, 9606'}).json()
        assert len(res) == 2
        assert res[0]['_id'] == '9605'
        assert res[1]['_id'] == '9606'

    def test_111(self):
        data = {'ids': '9605,9606',
                'fields': 'has_gene,scientific_name,lineage'}
        res = self.request('taxon', method='POST', data=data).json()
        assert len(res) == 2
        for _g in res:
            assert set(_g) == set(['_id', '_version', 'query', 'has_gene', 'scientific_name', 'lineage'])
