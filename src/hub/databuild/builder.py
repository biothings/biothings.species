import logging

import config
from biothings.hub.databuild.builder import DataBuilder
from biothings.hub.dataload.storage import UpsertStorage
from biothings.utils.mongo import doc_feeder, get_target_db

from .mapper import BacterialAbbreviationMapper, LineageMapper


class TaxonomyDataBuilder(DataBuilder):

    def post_merge(self, source_names, batch_size, job_manager):
        # get the lineage mapper
        lineage_mapper = LineageMapper(name="lineage")
        # load cache (it's being loaded automatically
        # as it's not part of an upload process
        lineage_mapper.load()

        # get the bacterial abbreviation mapper
        bacterial_mapper = BacterialAbbreviationMapper(
            name="bacterial_abbreviation")

        # create a storage to save docs back to merged collection
        db = get_target_db()
        col_name = self.target_backend.target_collection.name
        storage = UpsertStorage(db, col_name)

        for docs in doc_feeder(self.target_backend.target_collection,
                               step=batch_size, inbatch=True):
            # Apply lineage mapper first (adds lineage field)
            docs = lineage_mapper.process(docs)
            # Then apply bacterial abbreviation mapper
            # (depends on lineage field)
            docs = bacterial_mapper.process(docs)
            storage.process(docs, batch_size)

        # add indices used to create metadata stats
        keys = ["rank", "taxid"]
        self.logger.info("Creating indices on %s" % repr(keys))
        for k in keys:
            self.target_backend.target_collection.create_index(k)

    def get_stats(self, sources, job_manager):
        self.logger.info("Computing metadata...")
        # we want to compute it from scratch
        meta = {"__REPLACE__": True}
        col = self.target_backend.target_collection
        # disctint count of taxid
        cur = col.aggregate([{"$group": {"_id": "distinct_taxid", "count": {"$addToSet": "$taxid"}}},
                             {"$project": {"count": {"$size": "$count"}}}])
        res = list(cur)
        assert len(res) == 1
        distinct_taxid = res[0]["count"]
        meta["unique taxonomy ids"] = distinct_taxid
        # count per rank
        cur = col.aggregate(
            pipeline=[{"$group": {"_id": "$rank", "count": {"$sum": 1}}}])
        res = list(cur)
        meta["distribution of taxonomy ids by rank"] = {}
        for rank_info in res:
            meta["distribution of taxonomy ids by rank"].update(
                {rank_info["_id"]: rank_info["count"]})
        self.logger.info("Metadata: %s" % meta)
        return meta
