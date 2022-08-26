from biothings.tests.web import BiothingsDataTest

class TestTaxonWeb(BiothingsDataTest):
    host = 't.biothings.io'
    prefix = 'v1'

    def test_301_status(self):
        self.request('/status')

    def test_302_status(self):
        self.request('/status', method='HEAD')

    def test_303_static(self):
        self.request('/favicon.ico')

    def test_304_static(self):
        self.request('/robots.txt')

    def test_305_metadata(self):
        res = self.request("metadata").json()
        assert res['biothing_type'] == "taxon"
        assert "uniprot_species" in res['src'].keys()
        assert "geneinfo" in res['src'].keys()
        assert "taxonomy" in res['src'].keys()
        assert res['stats']['unique taxonomy ids'] >= 2370690
        assert len(res['stats']['distribution of taxonomy ids by rank']) >= 44
        assert res['stats']['distribution of taxonomy ids by rank']['kingdom'] == 13
        
    def test_306_fields(self):
        res = self.request('metadata/fields').json()
        assert len(res) > 8
        # Check some specific keys
        assert 'common_name' in res
        assert 'genbank_common_name' in res
        assert 'has_gene' in res
        assert 'lineage' in res
        assert 'parent_taxid' in res
        assert 'rank' in res
        assert 'scientific_name' in res
        assert 'taxid' in res
        assert 'uniprot_name' in res
