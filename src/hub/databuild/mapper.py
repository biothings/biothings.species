import logging
from collections import defaultdict

import biothings
import biothings.hub.databuild.mapper as mapper
import biothings.utils.mongo as mongo
import config

# just to get the collection name
from ..dataload.sources.geneinfo.uploader import GeneInfoUploader
from ..dataload.sources.taxonomy.uploader import TaxonomyNodesUploader

biothings.config_for_app(config)


class HasGeneMapper(mapper.BaseMapper):

    def __init__(self, *args, **kwargs):
        super(HasGeneMapper, self).__init__(*args, **kwargs)
        self.cache = None

    def load(self):
        if self.cache is None:
            # this is a whole dict containing all taxonomu _ids
            col = mongo.get_src_db()[GeneInfoUploader.name]
            self.cache = [d["_id"] for d in col.find({}, {"_id": 1})]

    def process(self, docs):
        for doc in docs:
            if doc["_id"] in self.cache:
                doc["has_gene"] = True
            else:
                doc["has_gene"] = False
            yield doc


class LineageMapper(mapper.BaseMapper):

    def __init__(self, *args, **kwargs):
        super(LineageMapper, self).__init__(*args, **kwargs)
        self.cache = None
        self.parent_to_children = None
        self.logger = logging.getLogger(__name__)
        self.has_gene_set = None

    def load(self):
        if self.cache is None:
            # Build self.cache: taxid -> parent_taxid
            col = mongo.get_src_db()[TaxonomyNodesUploader.name]
            self.cache = {}
            for d in col.find({}, {"parent_taxid": 1, "taxid": 1}):
                self.cache[d["taxid"]] = d["parent_taxid"]

            self.parent_to_children = defaultdict(list)
            for taxid, parent_taxid in self.cache.items():
                if taxid != parent_taxid:  # exclude root which points to itself
                    self.parent_to_children[parent_taxid].append(taxid)

        # Also build self.has_gene_set
        if self.has_gene_set is None:
            geneinfo_col = mongo.get_src_db()[GeneInfoUploader.name]
            self.has_gene_set = set(doc["_id"]
                                    for doc in geneinfo_col.find({}, {"_id": 1}))

    def get_lineage(self, doc):
        if doc["taxid"] == doc["parent_taxid"]:
            # We reached the top of the taxonomy tree
            doc["lineage"] = [doc["taxid"]]
        else:
            # initiate lineage with current doc
            lineage = [doc["taxid"], doc["parent_taxid"]]
            while lineage[-1] != 1:
                parent = self.cache[lineage[-1]]
                lineage.append(parent)
            doc["lineage"] = lineage

        # children
        children = self.parent_to_children.get(doc["taxid"], [])
        if children:
            doc["children"] = children

            # Build _has_gene_children as a filtered subset
            doc["_has_gene_children"] = [
                child for child in children if child in self.has_gene_set
            ]
        else:
            doc["children"] = []
            doc["_has_gene_children"] = []

        # ancestors (lineage except the node itself)
        ancestors = doc["lineage"][1:]
        if ancestors:
            doc["ancestors"] = ancestors

        return doc

    def process(self, docs):
        for doc in docs:
            doc = self.get_lineage(doc)
            yield doc
