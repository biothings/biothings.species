#!/usr/bin/env python

import os
import logging
from functools import partial

import biothings
from biothings.utils.version import set_versions

app_folder, _src = os.path.split(os.path.split(os.path.split(os.path.abspath(__file__))[0])[0])
del _src
import config
set_versions(config, app_folder)

from biothings.hub import HubServer
import biothings.hub.databuild.builder as builder
from biothings.hub.databuild.syncer import SyncerManager, \
                                           ThrottledESJsonDiffSyncer, ThrottledESJsonDiffSelfContainedSyncer

from hub.databuild.mapper import HasGeneMapper
from hub.databuild.builder import TaxonomyDataBuilder


class MyTaxonomyHubServer(HubServer):

    def configure_build_manager(self):
        hasgene = HasGeneMapper(name="has_gene")
        pbuilder = partial(TaxonomyDataBuilder,mappers=[hasgene])
        build_manager = builder.BuilderManager(
                job_manager=self.managers["job_manager"],
                builder_class=pbuilder,
                poll_schedule="* * * * * */10")
        build_manager.configure()
        build_manager.configure()
        # TODO: figure out why method configure is called twice
        build_manager.poll()
        self.managers["build_manager"] = build_manager
        self.logger.info("Using custom builder %s" % TaxonomyDataBuilder)

    def configure_sync_manager(self):
        # prod
        sync_manager_prod = SyncerManager(job_manager=self.managers["job_manager"])
        sync_manager_prod.configure(klasses=[partial(ThrottledESJsonDiffSyncer,config.MAX_SYNC_WORKERS),
                                               partial(ThrottledESJsonDiffSelfContainedSyncer,config.MAX_SYNC_WORKERS)])
        self.managers["sync_manager"] = sync_manager_prod
        # test will access localhost ES, no need to throttle
        sync_manager_test = SyncerManager(job_manager=self.managers["job_manager"])
        sync_manager_test.configure()
        self.managers["sync_manager_test"] = sync_manager_test
        self.logger.info("Using custom syncer, prod(throttled): %s, test: %s" % (sync_manager_prod,sync_manager_test))

    def configure_commands(self):
        super().configure_commands() # keep all originals...
        self.commands["es_sync_test"] = partial(self.managers["sync_manager_test"].sync,"es",
                                           target_backend=(config.INDEX_CONFIG["env"]["hub_es"]["host"],
                                                           config.INDEX_CONFIG["env"]["hub_es"]["index"][0]["index"],
                                                           config.INDEX_CONFIG["env"]["hub_es"]["index"][0]["doc_type"]))
        self.commands["es_sync_prod"] = partial(self.managers["sync_manager"].sync,"es",
                                           target_backend=(config.INDEX_CONFIG["env"]["prod"]["host"],
                                                           config.INDEX_CONFIG["env"]["prod"]["index"][0]["index"],
                                                           config.INDEX_CONFIG["env"]["prod"]["index"][0]["doc_type"]))
        # self.commands["publish_diff_demo"] = partial(self.managers["diff_manager"].publish_diff,config.S3_APP_FOLDER + "-demo",
        #                                         s3_bucket=config.S3_DIFF_BUCKET + "-demo")
        # self.commands["snapshot_demo"] = partial(self.managers["index_manager"].snapshot,repository=config.SNAPSHOT_REPOSITORY + "-demo")
        # self.commands["publish_snapshot_demo"] = partial(self.managers["index_manager"].publish_snapshot,s3_folder=config.S3_APP_FOLDER + "-demo",
        #                                     repository=config.READONLY_SNAPSHOT_REPOSITORY)
        # # replace default
        # self.commands["publish_diff"] = partial(self.managers["diff_manager"].publish_diff,config.S3_APP_FOLDER)
        # self.commands["publish_snapshot"] = partial(self.managers["index_manager"].publish_snapshot,s3_folder=config.S3_APP_FOLDER)


import hub.dataload
# pass explicit list of datasources (no auto-discovery)
server = MyTaxonomyHubServer(hub.dataload.__sources__, name=config.HUB_NAME)

if __name__ == "__main__":
    server.start()
