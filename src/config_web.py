# *****************************************************************************
# Elasticsearch variables
# *****************************************************************************
# elasticsearch server transport url
ES_HOST = 'localhost:9200'
# elasticsearch index name
ES_INDEX = 'mytaxonomy_current'
# elasticsearch document type
ES_DOC_TYPE = 'taxon'

# *****************************************************************************
# Query Pipeline
# *****************************************************************************
# ES_RESULT_TRANSFORMER = ESResultTransformer #TODO


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

# KWARGS for taxon API TODO
# DEFAULT_FALSE_BOOL_TYPEDEF = {'default': False, 'type': bool}
# ANNOTATION_GET_TRANSFORM_KWARGS.update({'include_children': DEFAULT_FALSE_BOOL_TYPEDEF, 
#                                         'has_gene': DEFAULT_FALSE_BOOL_TYPEDEF})
# ANNOTATION_POST_TRANSFORM_KWARGS.update({'include_children': DEFAULT_FALSE_BOOL_TYPEDEF,
#                                         'has_gene': DEFAULT_FALSE_BOOL_TYPEDEF,
#                                         'expand_species': DEFAULT_FALSE_BOOL_TYPEDEF})
# QUERY_GET_TRANSFORM_KWARGS.update({'include_children': DEFAULT_FALSE_BOOL_TYPEDEF,
#                                     'has_gene': DEFAULT_FALSE_BOOL_TYPEDEF})
# QUERY_POST_TRANSFORM_KWARGS.update({'include_children': DEFAULT_FALSE_BOOL_TYPEDEF,
#                                     'has_gene': DEFAULT_FALSE_BOOL_TYPEDEF})

