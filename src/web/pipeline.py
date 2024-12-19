
from biothings.web.query import (
    AsyncESQueryBackend,
    AsyncESQueryPipeline,
    ESResultFormatter,
)
from biothings.web.query.engine import RawResultInterrupt

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


class MytaxonQueryBackend(AsyncESQueryBackend):

    async def execute(self, query, **options):
        raw = options.pop('raw', False)
        res = await super().execute(query, **options)

        if raw:
            raise RawResultInterrupt(res)

        return res


class MytaxonTransform(ESResultFormatter):

    def transform_hit(self, path, obj, doc, options):
        super().transform_hit(path, obj, doc, options)

        if not options.get('include_children', False) and 'children' in doc:
            del doc['children']
        else:
            if 'children' in doc and isinstance(doc['children'], list):
                doc['children'] = sorted(doc['children'])


class MytaxonQueryPipeline(AsyncESQueryPipeline):

    async def fetch(self, id, **options):
        res = await super().fetch(id, **options)
        if options.get('expand_species') and isinstance(res, list):
            ids = set()
            for _res in res:
                ids.add(int(_res['_id']))
                if 'children' in _res:
                    ids.update(_res['children'])
            return list(ids)
        return res
