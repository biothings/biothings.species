
from biothings.utils.common import dotdict
from biothings.web.query import (
    AsyncESQueryPipeline,
    ESQueryBuilder,
    AsyncESQueryBackend,
    ESResultFormatter)
from biothings.web.query.engine import RawResultInterrupt
from elasticsearch_dsl import Search

"""
Potential Test Cases
/v1/query?q=207598&include_children
/v1/query?q=207598&include_children&has_gene
/v1/taxon/9592?fields=has_gene
POST /v1/taxon?expand_species 
ids=207598
POST /v1/taxon?expand_species
ids=207598
has_gene=1
"""


class MytaxonQueryBuilder(ESQueryBuilder):

    @staticmethod
    def build_lineage_query(_id, options):

        search = Search()
        search = search.query('match', lineage=_id)

        if options.get('has_gene'):
            # has_gene is always set, either to True or False
            search = search.query('match', has_gene=True)

        search = search.params(size=10000)
        search = search.params(_source='_id')

        return search


class MytaxonQueryBackend(AsyncESQueryBackend):

    async def execute(self, query, **options):

        raw = options.pop('raw', False)
        res = await super().execute(query, **options)

        # optionally add a children field
        if options.get('include_children') or \
                options.get('expand_species'):
            await self.include_children(res, options)

        if raw:  # relocated from previous execute()
            raise RawResultInterrupt(res)

        return res

    async def include_children(self, res, options):  # modify in-place
        """
        Make additional queries to get the children field content.
        """

        # msearch result
        if isinstance(res, list):
            for search in res:
                await self.include_children(search, options)
            return

        try:  # single query
            for hit in res['hits']['hits']:
                query = MytaxonQueryBuilder.build_lineage_query(hit['_id'], options)
                hit['children'] = await super().execute(query)
        except KeyError:
            pass


class MytaxonTransform(ESResultFormatter):

    def transform_hit(self, path, obj, doc, options):

        super().transform_hit(path, obj, doc, options)

        # children field in top level
        if path == '' and 'children' in doc:

            hits = doc['children']['hits']['hits']
            # transform to a list of lineage reverse query result ids
            children = (int(hit['_id']) for hit in hits if hit['_id'] != doc['_id'])
            doc['children'] = sorted(children)


class MytaxonQueryPipeline(AsyncESQueryPipeline):

    async def fetch(self, id, **options):
        res = await super().fetch(id, **options)
        if options.get('expand_species') and isinstance(res, list):
            ids = set()
            for _res in res:
                ids.add(int(_res['_id']))
                ids.update(_res['children'])
            return list(ids)
        return res
