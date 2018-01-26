#!/usr/bin/env python

import asyncio, asyncssh, sys
from functools import partial
from collections import OrderedDict

import config, biothings
biothings.config_for_app(config)

import logging
# shut some mouths...
logging.getLogger("elasticsearch").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

logging.info("Hub DB backend: %s" % biothings.config.HUB_DB_BACKEND)
logging.info("Hub database: %s" % biothings.config.DATA_HUB_DB_DATABASE)

from biothings.utils.hub import start_server, HubShell
shell = HubShell()

from biothings.utils.manager import JobManager
loop = asyncio.get_event_loop()
jmanager = JobManager(loop,num_workers=config.HUB_MAX_WORKERS,
                      max_memory_usage=config.HUB_MAX_MEM_USAGE)

import hub.dataload
import biothings.hub.dataload.uploader as uploader
import biothings.hub.dataload.dumper as dumper
import biothings.hub.databuild.builder as builder
import biothings.hub.databuild.differ as differ
import biothings.hub.databuild.syncer as syncer
import biothings.hub.dataindex.indexer as indexer
from hub.databuild.mapper import HasGeneMapper
from hub.databuild.builder import TaxonomyDataBuilder
from hub.dataindex.indexer import TaxonomyIndexer 

differ_manager = differ.DifferManager(job_manager=jmanager,
        poll_schedule="* * * * * */10")
differ_manager.configure()
differ_manager.poll("diff",lambda doc:
        shell.launch(partial(differ_manager.diff,"jsondiff-selfcontained",old=None,new=doc["_id"])))
differ_manager.poll("release_note",lambda doc:
        shell.launch(partial(differ_manager.release_note,old=None,new=doc["_id"])))

syncer_manager = syncer.SyncerManager(job_manager=jmanager)
syncer_manager.configure()

dmanager = dumper.DumperManager(job_manager=jmanager)
dmanager.register_sources(hub.dataload.__sources__)
dmanager.schedule_all()

# will check every 10 seconds for sources to upload
umanager = uploader.UploaderManager(poll_schedule = '* * * * * */10', job_manager=jmanager)
umanager.register_sources(hub.dataload.__sources__)
umanager.poll('upload',lambda doc: shell.launch(partial(umanager.upload_src,doc["_id"])))

hasgene = HasGeneMapper(name="has_gene")
pbuilder = partial(TaxonomyDataBuilder,mappers=[hasgene])
bmanager = builder.BuilderManager(
        job_manager=jmanager,
        builder_class=pbuilder,
        poll_schedule="* * * * * */10")
bmanager.configure()
bmanager.poll("build",lambda conf: shell.launch(partial(bmanager.merge,conf["_id"])))

pindexer = partial(TaxonomyIndexer,es_host=config.ES_HOST)
index_manager = indexer.IndexerManager(job_manager=jmanager)
index_manager.configure([{"default":pindexer}])

from biothings.utils.hub import schedule, pending, done

COMMANDS = OrderedDict()
# dump commands
COMMANDS["dump"] = dmanager.dump_src
# upload commands
COMMANDS["upload"] = umanager.upload_src
COMMANDS["upload_all"] = umanager.upload_all
# building/merging
COMMANDS["lsmerge"] = bmanager.list_merge 
COMMANDS["merge"] = partial(bmanager.merge,"taxonomy")
COMMANDS["mongo_sync"] = partial(syncer_manager.sync,"mongo")
COMMANDS["es_sync"] = partial(syncer_manager.sync,"es")
# diff
COMMANDS["publish_diff"] = partial(differ_manager.publish_diff,config.S3_APP_FOLDER)
COMMANDS["diff"] = partial(differ_manager.diff,"jsondiff-selfcontained")
COMMANDS["report"] = differ_manager.diff_report
COMMANDS["release_note"] = differ_manager.release_note
# indexing commands
COMMANDS["index"] = partial(index_manager.index,"default")
COMMANDS["snapshot"] = index_manager.snapshot
COMMANDS["publish_snapshot"] = partial(index_manager.publish_snapshot,config.S3_APP_FOLDER)

EXTRA_NS = {
        "dm" : dmanager,
        "um" : umanager,
        "bm" : bmanager,
        "sm" : syncer_manager,
        "dim" : differ_manager,
        "im" : index_manager,
        ## admin/advanced
        #"loop" : loop,
        "q" : jmanager.process_queue,
        "t" : jmanager.thread_queue,
        "g": globals(),
        "l":loop,
        "j":jmanager,
        "sch" : partial(schedule,loop),
        "top" : jmanager.top,
        "pending" : pending,
        "done" : done,
        }

shell.set_commands(COMMANDS,EXTRA_NS)

from biothings.utils.hub import start_server
ssh_server = start_server(loop, "Species hub",passwords=config.HUB_PASSWD,
        port=config.HUB_SSH_PORT,shell=shell)

try:
    loop.run_until_complete(asyncio.wait([ssh_server]))
except (OSError, asyncssh.Error) as exc:
    sys.exit('Error starting SSH server: ' + str(exc))

loop.run_forever()

