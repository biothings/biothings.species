"""
    MyTaxon
    http://t.biothings.io/
"""

from copy import deepcopy

from biothings.web.settings.default import ANNOTATION_KWARGS, QUERY_KWARGS, APP_LIST

# *****************************************************************************
# Elasticsearch variables
# *****************************************************************************
# elasticsearch server transport url
ES_HOST = 'es6.biothings.io:9200'
# elasticsearch index name
ES_INDEX = 'mytaxonomy_current'
# elasticsearch document type
ES_DOC_TYPE = 'taxon'

# *****************************************************************************
# Web Application
# *****************************************************************************
APP_LIST = list(APP_LIST)
APP_LIST.append((r"/{pre}/{ver}/{typ}/?", 'web.handlers.MytaxonHandler'))

ES_QUERY_BUILDER = 'web.pipeline.MytaxonQueryBuilder'
ES_QUERY_BACKEND = 'web.pipeline.MytaxonQueryBackend'
ES_RESULT_TRANSFORM = "web.pipeline.MytaxonTransform"

TYPEDEF = {'type': bool, 'default': False, 'group': ['es']}

ANNOTATION_KWARGS['*']['include_children'] = {
    'type': bool, 'default': False, 'group': ['es']}
ANNOTATION_KWARGS['POST']['expand_species'] = {
    'type': bool, 'default': False, 'group': ['es'], 'alias': ['expand_taxon']}
ANNOTATION_KWARGS['*']['has_gene'] = {
    'type': bool, 'default': False, 'group': ['es'], 'alias': ['children_has_gene']}

QUERY_KWARGS = deepcopy(QUERY_KWARGS)
QUERY_KWARGS['*']['include_children'] = {
    'type': bool, 'default': False, 'group': ['es']}
QUERY_KWARGS['*']['has_gene'] = {
    'type': bool, 'default': False, 'group': ['es'], 'alias': ['children_has_gene']}

# *****************************************************************************
# Analytics
# *****************************************************************************
GA_ACTION_QUERY_GET = 'query_get'
GA_ACTION_QUERY_POST = 'query_post'
GA_ACTION_ANNOTATION_GET = 'species_get'
GA_ACTION_ANNOTATION_POST = 'species_post'
GA_TRACKER_URL = 't.biothings.io'

STATUS_CHECK = {
    'id': '9606',
    'index': 'taxonomy',
    'doc_type': 'taxon'
}

