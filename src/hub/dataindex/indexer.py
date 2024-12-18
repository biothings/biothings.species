import biothings.hub.dataindex.indexer as indexer


class TaxonomyIndexer(indexer.Indexer):
    def __init__(self, build_doc, indexer_env, index_name):
        super().__init__(build_doc, indexer_env, index_name)
        self.es_index_mappings['properties'].update({
            'lineage': {'type': 'integer'},
            'children': {'type': 'integer'},
            'ancestors': {'type': 'integer'}
        })
