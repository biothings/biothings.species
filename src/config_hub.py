#############
# HUB VARS  #
#############

# Refer to biothings.hub.default_config for all configurable settings

DATA_SRC_SERVER = 'localhost'
DATA_SRC_PORT = 27017
DATA_SRC_DATABASE = 'mytaxon_src'

DATA_TARGET_SERVER = 'localhost'
DATA_TARGET_PORT = 27017
DATA_TARGET_DATABASE = 'mytaxon'

HUB_DB_BACKEND = {
    "module": "biothings.utils.mongo",
    "uri": "mongodb://localhost:27017",
}
DATA_HUB_DB_DATABASE = "mytaxon_hubdb"


HUB_NAME = "MyTaxonomy Data Hub"
HUB_ICON = "https://raw.githubusercontent.com/biothings/biothings_sites/master/biothings-theme/static/img/biothings-logo-md.png"

LOGGER_NAME = "mytaxon.hub"

### Pre-prod/test ES definitions
INDEX_CONFIG = {
    "indexer_select": {
        # default
        None: "hub.dataindex.indexer.TaxonomyIndexer",
    },
    "env": {
        "prod": {
            "host": "localhost:9200",   # replace with the actual ES host for production hub
            "indexer": {
                "args": {
                    "timeout": 300,
                    "retry_on_timeout": True,
                    "max_retries": 10,
                },
            },
            "index": [{"index": "mytaxon_current", "doc_type": "taxonomy"}]
        },
        "test": {
            "host": "localhost:9200",
            "indexer": {
                "args": {
                    "timeout": 300,
                    "retry_on_timeout": True,
                    "max_retries": 10,
                },
            },
            "index": [{"index": "mytaxon_current", "doc_type": "gene"}]
        },
    },
}


# Release configuration
# Each root keys define a release environment (test, prod, ...)
RELEASE_CONFIG = {}


########################################
# APP-SPECIFIC CONFIGURATION VARIABLES #
########################################
# The following variables should or must be defined in your
# own application. Create a config.py file, import that config_common
# file as:
#
#   from config_hub import *
#
# then define the following variables to fit your needs. You can also override any
# any other variables in this file as required. Variables defined as ValueError() exceptions
# *must* be defined

