import logging
from collections import defaultdict, deque

import biothings
import biothings.hub.databuild.mapper as mapper
import biothings.utils.mongo as mongo
import config
from biothings.utils.common import loadobj

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
        self.descendants_map = None
        self.logger = logging.getLogger(__name__)

    def load(self):
        if self.cache is None:
            col = mongo.get_src_db()[TaxonomyNodesUploader.name]
            self.cache = {}
            # Build cache: taxid -> parent_taxid
            for d in col.find({}, {"parent_taxid": 1, "taxid": 1}):
                self.cache[d["taxid"]] = d["parent_taxid"]

            # Build parent_to_children map
            self.parent_to_children = defaultdict(list)
            for taxid, parent_taxid in self.cache.items():
                if taxid != parent_taxid:  # exclude root which points to itself
                    self.parent_to_children[parent_taxid].append(taxid)

            # Precompute descendants for all taxids
            self.descendants_map = {}
            all_taxids = list(self.cache.keys())
            self.logger.info(
                "Precomputing descendants for %d nodes..." % len(all_taxids))
            for tid in all_taxids:
                self.descendants_map[tid] = self._get_all_descendants(tid)
            self.logger.info("Finished precomputing descendants.")

    def _get_all_descendants(self, taxid):
        # BFS to find all descendants
        descendants = []
        queue = deque(self.parent_to_children.get(taxid, []))
        while queue:
            child = queue.popleft()
            descendants.append(child)
            # add children of this child
            for c in self.parent_to_children.get(child, []):
                queue.append(c)
        return descendants

    def get_lineage(self, doc):
        if doc['taxid'] == doc['parent_taxid']:
            # We reached the top of the taxonomy tree
            doc['lineage'] = [doc['taxid']]
        else:
            # initiate lineage with current doc
            lineage = [doc['taxid'], doc['parent_taxid']]
            while lineage[-1] != 1:
                parent = self.cache[lineage[-1]]
                lineage.append(parent)
            doc['lineage'] = lineage

        # Once lineage is computed, we can set the other fields:
        # parents
        if doc['taxid'] != doc['parent_taxid']:
            doc['parents'] = [doc['parent_taxid']]
        else:
            doc['parents'] = []

        # children
        doc['children'] = self.parent_to_children.get(doc['taxid'], [])

        # ancestors (lineage except the node itself)
        doc['ancestors'] = doc['lineage'][1:]
        if len(doc['ancestors']) > 1000:
            self.logger.warning(
                "Ancestors for taxid %s is over 1000: %d. Capping to 1000." % (
                    doc['taxid'], len(doc['ancestors']))
            )
            doc['ancestors'] = doc['ancestors'][:1000]

        # descendants from precomputed map
        doc['descendants'] = self.descendants_map.get(doc['taxid'], [])
        if len(doc['descendants']) > 1000:
            self.logger.warning(
                "Descendants for taxid %s is over 1000: %d. Capping to 1000." % (doc['taxid'], len(doc['descendants'])))
            doc['descendants'] = doc['descendants'][:1000]

        return doc

    def process(self, docs):
        for doc in docs:
            doc = self.get_lineage(doc)
            yield doc
