from biothings.web.handlers import BiothingHandler

class MytaxonHandler(BiothingHandler):

    def pre_query_hook(self, options, query):
        """
        Add implied conditions.
        """
        if options.es.expand_species:
            options.es.include_children = True
        return super().pre_query_hook(options, query)

    def pre_finish_hook(self, options, res):
        """
        Support expand_species parameter.
        Used in mygene to get species parameter.
        """
        res = super().pre_finish_hook(options, res)
        if options.es.expand_species and isinstance(res, list):
            ids = set()
            for _res in res:
                ids.add(int(_res['_id']))
                ids.update(_res['children'])
            return list(ids)
        return res