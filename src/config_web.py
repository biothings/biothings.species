"""
    MyTaxon
    http://t.biothings.io/
"""

from copy import deepcopy

from biothings.web.settings.default import ANNOTATION_KWARGS, QUERY_KWARGS

# *****************************************************************************
# Elasticsearch variables
# *****************************************************************************
ES_HOST = 'es7.biothings.io:443'
ES_ARGS = dict(aws=True)
ES_INDICES = dict(taxon='mytaxon_current')

# *****************************************************************************
# Web Application
# *****************************************************************************
ES_QUERY_PIPELINE = 'web.pipeline.MytaxonQueryPipeline'
ES_QUERY_BUILDER = 'web.pipeline.MytaxonQueryBuilder'
ES_QUERY_BACKEND = 'web.pipeline.MytaxonQueryBackend'
ES_RESULT_TRANSFORM = "web.pipeline.MytaxonTransform"

ALLOW_RANDOM_QUERY = True

ANNOTATION_KWARGS['*']['include_children'] = {
    'type': bool, 'default': False}
ANNOTATION_KWARGS['POST']['expand_species'] = {
    'type': bool, 'default': False, 'alias': ['expand_taxon']}
ANNOTATION_KWARGS['*']['has_gene'] = {
    'type': bool, 'default': False, 'alias': ['children_has_gene']}

QUERY_KWARGS = deepcopy(QUERY_KWARGS)
QUERY_KWARGS['*']['include_children'] = {
    'type': bool, 'default': False}
QUERY_KWARGS['*']['has_gene'] = {
    'type': bool, 'default': False, 'alias': ['children_has_gene']}

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
    'index': 'mytaxon_current'
}
