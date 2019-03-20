import biothings.hub.dataindex.indexer as indexer


class TaxonomyIndexer(indexer.Indexer):

    def get_mapping(self):
        mapping = super(TaxonomyIndexer,self).get_mapping()
        mapping["properties"]["lineage"] = { 
                "type": "long"
                }

        return mapping
