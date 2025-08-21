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
                child for child in children if str(child) in self.has_gene_set
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


class ScientificNameAbbreviationMapper(mapper.BaseMapper):
    """
    Mapper to create abbreviations for scientific names in other_names.

    Creates abbreviations based on taxonomic rank:
    - species: Genus species -> G. species
    - subspecies: Genus species ssp./subsp. -> G. species ssp./subsp.
    - strain: Genus species str. -> G. species str.
    """

    def __init__(self, *args, **kwargs):
        super(ScientificNameAbbreviationMapper, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def _is_target_rank(self, rank):
        """Check if rank is one we want to abbreviate"""
        target_ranks = {'species', 'subspecies', 'strain'}
        return rank in target_ranks if rank else False

    def _abbreviate_scientific_name(self, name, rank):
        """
        Abbreviate scientific name based on taxonomic rank.

        Args:
            name: Scientific name to abbreviate
            rank: Taxonomic rank (species, subspecies, strain)

        Returns:
            List of abbreviated names
        """
        if not name or not isinstance(name, str):
            return []

        # Clean and split the name
        name = name.strip()
        parts = name.split()

        # Need at least genus and species for abbreviation
        if len(parts) < 2:
            return []

        # Abbreviate first part (genus) to first letter + dot
        genus = parts[0]
        if len(genus) == 0:
            return []

        abbreviated_genus = genus[0].upper() + '.'
        abbreviated_names = []

        if rank == 'species':
            # For species: G. species
            if len(parts) >= 2:
                abbreviated = abbreviated_genus + ' ' + ' '.join(parts[1:])
                abbreviated_names.append(abbreviated)

        elif rank == 'subspecies':
            # For subspecies: G. species ssp. {rest} and
            # G. species subsp. {rest}
            if len(parts) >= 3:
                # Find where subspecies designation starts
                species_part = parts[1]
                rest_parts = parts[2:]

                # Create both ssp. and subsp. variants
                rest_joined = ' '.join(rest_parts)
                ssp_abbrev = (f"{abbreviated_genus} {species_part} "
                              f"ssp. {rest_joined}")
                subsp_abbrev = (f"{abbreviated_genus} {species_part} "
                                f"subsp. {rest_joined}")

                abbreviated_names.extend([ssp_abbrev, subsp_abbrev])

        elif rank == 'strain':
            # For strain: G. species str. {rest}
            if len(parts) >= 3:
                species_part = parts[1]
                rest_parts = parts[2:]

                rest_joined = ' '.join(rest_parts)
                str_abbrev = (f"{abbreviated_genus} {species_part} "
                              f"str. {rest_joined}")
                abbreviated_names.append(str_abbrev)

        return abbreviated_names

    def process(self, docs):
        processed_count = 0
        abbreviation_count = 0

        for doc in docs:
            processed_count += 1
            rank = doc.get("rank", "")

            if self._is_target_rank(rank):
                # Get existing other_names or empty list if doesn't exist
                original_names = doc.get("other_names", [])
                all_abbreviated_names = []

                # Always try to abbreviate the scientific_name
                scientific_name = doc.get("scientific_name", "")
                if scientific_name:
                    abbreviated_list = self._abbreviate_scientific_name(
                        scientific_name, rank)

                    for abbreviated in abbreviated_list:
                        # Only add if it's different from scientific_name
                        # and not already present in original_names
                        if (abbreviated != scientific_name and
                                abbreviated not in original_names and
                                abbreviated not in all_abbreviated_names):
                            all_abbreviated_names.append(abbreviated)

                # Add abbreviated names to other_names if any were created
                if all_abbreviated_names:
                    # Only update other_names if we have new abbreviations
                    if original_names:
                        # Preserve existing other_names and add abbreviations
                        doc["other_names"] = (original_names +
                                              all_abbreviated_names)
                    else:
                        # Create new other_names with just the abbreviations
                        doc["other_names"] = all_abbreviated_names

                    taxid = doc.get('taxid')
                    abbreviation_count += 1
                    self.logger.info(f"Added abbreviations for taxid "
                                     f"{taxid} (rank: {rank}): "
                                     f"{all_abbreviated_names}")

            yield doc

        self.logger.info(f"ScientificNameAbbreviationMapper processed "
                         f"{processed_count} docs, added abbreviations to "
                         f"{abbreviation_count} docs")
