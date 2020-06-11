
from biothings.utils.common import dotdict
from biothings.utils.web.es_dsl import AsyncSearch
from biothings.web.pipeline import (ESQueryBackend, ESQueryBuilder,
                                    ESResultTransform)


class MytaxonQueryBuilder(ESQueryBuilder):
    
    @staticmethod
    def build_lineage_query(_id, options):

        search = AsyncSearch()
        search = search.query('match', lineage=_id)
        if options.has_gene:
            search = search.query('match', has_gene=options.has_gene)

        max_taxid_count = 10000
        search = search.params(size=max_taxid_count)
        search = search.params(_source='_id')
        
        return search


class MytaxonQueryBackend(ESQueryBackend):

    async def execute(self, query, options):

        res = await super().execute(query, options)

        # optionally add a children field
        if options.include_children:
            await self.include_children(res, options)

        return res

    async def include_children(self, res, options): # modify in-place
        """
        Make additional queries to get the children field content.
        """

        # msearch result
        if isinstance(res, list):
            for search in res:
                await self.include_children(search, options)
            return
                
        try: # single query
            for hit in res['hits']['hits']:
                query = MytaxonQueryBuilder.build_lineage_query(hit['_id'], options)
                hit['children'] = await super().execute(query, dotdict())
        except KeyError:
            pass


class MytaxonTransform(ESResultTransform):

    def transform_hit(self, path, doc, options):

        super().transform_hit(path, doc, options)
        
        # children field in top level
        if path == '' and 'children' in doc:

            hits = doc['children']['hits']['hits']
            # transform to a list of lineage reverse query result ids
            children = (int(hit['_id']) for hit in hits if hit['_id'] != doc['_id'])
            doc['children'] = sorted(children)

        return
        
    @staticmethod
    def option_sorted(path, obj):
        """
        Sort a container in-place.
        """
        if path == 'lineage':
            return # do not sort this field

        # delegate to super class for normal cases
        ESResultTransform.option_sorted(path, obj)
