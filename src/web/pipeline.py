from biothings.web.query import (
    AsyncESQueryBackend,
    AsyncESQueryPipeline,
    ESQueryBuilder,
    ESResultFormatter,
)
from biothings.web.query.engine import RawResultInterrupt


class MytaxonQueryBuilder(ESQueryBuilder):

    def apply_extras(self, search, options):
        if options.get('include_children') or options.get('expand_species'):
            search = search.source(
                include=["*", "children", "_has_gene_children"],
                exclude=["ancestors"]
            )
        else:
            search = search.source(
                exclude=["children", "_has_gene_children", "ancestors"]
            )

        return super().apply_extras(search, options)


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

        if path == '':
            if 'children' in doc or '_has_gene_children' in doc:
                if options.get('has_gene'):
                    doc['children'] = doc.get('_has_gene_children', [])
                doc.pop('_has_gene_children', None)


class MytaxonQueryPipeline(AsyncESQueryPipeline):

    async def fetch(self, id, **options):
        res = await super().fetch(id, **options)
        if options.get('expand_species') and isinstance(res, list):
            ids = set()
            for _res in res:
                ids.add(int(_res['_id']))
                ids.update(_res.get('children', []))
            return list(ids)
        return res
