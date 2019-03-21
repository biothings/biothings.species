import biothings, config
biothings.config_for_app(config)
from biothings.utils.common import loadobj
import biothings.utils.mongo as mongo
import biothings.hub.databuild.mapper as mapper
# just to get the collection name
from ..dataload.sources.geneinfo.uploader import GeneInfoUploader
from ..dataload.sources.taxonomy.uploader import TaxonomyNodesUploader


class HasGeneMapper(mapper.BaseMapper):

    def __init__(self, *args, **kwargs):
        super(HasGeneMapper,self).__init__(*args,**kwargs)
        self.cache = None

    def load(self):
        if self.cache is None:
            # this is a whole dict containing all taxonomu _ids
            col = mongo.get_src_db()[GeneInfoUploader.name]
            self.cache = [d["_id"] for d in col.find({},{"_id":1})]

    def process(self,docs):
        for doc in docs:
            if doc["_id"] in self.cache:
                doc["has_gene"] = True
            else:
                doc["has_gene"] = False
            yield doc


class LineageMapper(mapper.BaseMapper):

    def __init__(self, *args, **kwargs):
        super(LineageMapper,self).__init__(*args,**kwargs)
        self.cache = None

    def load(self):
        if self.cache is None:
            col = mongo.get_src_db()[TaxonomyNodesUploader.name]
            self.cache = {}
            [self.cache.setdefault(d["taxid"],d["parent_taxid"]) for d in col.find({},{"parent_taxid":1,"taxid":1})]

    def get_lineage(self,doc):
        if doc['taxid'] == doc['parent_taxid']: #take care of node #1
            # we reached the top of the taxonomy tree
            doc['lineage'] = [doc['taxid']]
            return doc
        # initiate lineage with information we have in the current doc
        lineage = [doc['taxid'], doc['parent_taxid']]
        while lineage[-1] != 1:
            parent = self.cache[lineage[-1]]
            lineage.append(parent)
        doc['lineage'] = lineage
        return doc

    def process(self,docs):
        for doc in docs:
            doc = self.get_lineage(doc)
            yield doc

