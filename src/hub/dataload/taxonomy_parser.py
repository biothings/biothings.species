# -*- coding: utf-8 -*-
import json
import os
import tarfile
from collections import defaultdict
from itertools import groupby

# *** Download these files *****
'''
wget -N ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
wget -N ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/docs/speclist.txt
wget -N ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
'''
# ********Run this command! makes a file containing a unique list of tax_ids********
'''
gunzip -c gene_info.gz | tail -n+2 | cut -f1 | sort | uniq > gene_info_uniq
'''
# ****Change Me *****
FLAT_FILE_PATH = "flat_files"


def main():
    '''
    Build the taxonomy database from flatfiles downloaded from ncbi and uniprot
    '''
    # Possible ranks
    ranks = ['superkingdom', 'kingdom', 'subkingdom', 'superphylum', 'phylum', 'subphylum', 'superclass', 'class',
             'subclass', 'infraclass', 'superorder', 'order', 'suborder', 'infraorder', 'parvorder', 'superfamily',
             'family', 'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'species group', 'species subgroup',
             'species', 'subspecies', 'varietas', 'forma', 'strain', 'no rank']

    # Parse NCBI Files
    in_file = os.path.join(FLAT_FILE_PATH, 'taxdump.tar.gz')
    t = tarfile.open(in_file, mode='r:gz')
    names_file = t.extractfile('names.dmp')
    names = parse_refseq_names(names_file)
    nodes_file = t.extractfile('nodes.dmp')
    nodes = parse_refseq_nodes(nodes_file)
    t.close()

    # Parse uniprot file
    in_file = os.path.join(FLAT_FILE_PATH, 'speclist.txt')
    with open(in_file) as uniprot_speclist:
        uniprot = parse_uniprot_speclist(uniprot_speclist)

    # Combine entries by taxid
    entries = combine_by_taxid(names, nodes, uniprot)

    # Some tax_ids in uniprot but not in ncbi nodes file, so make sure there's a parent_taxid for each entry
    entries = dict([(key, value) for (key, value)
                   in entries.items() if 'parent_taxid' in value.keys()])

    # Set rank#
    for taxid in entries.keys():
        rank = entries[taxid]['rank']
        if rank == 'no rank':
            entries[taxid]['rank#'] = None
        elif rank in ranks:
            entries[taxid]['rank#'] = ranks.index(rank)
        else:
            entries[taxid]['rank#'] = None
            print(f"Warning: Rank '{rank}' for taxid {
                  taxid} is not in the ranks list.")

    # Mark tax_ids that have a gene in ncbi
    in_file = os.path.join(FLAT_FILE_PATH, 'gene_info_uniq')
    with open(in_file) as f:
        has_gene_tax_set = set([int(line) for line in f])
    for taxid, entry in entries.items():
        entry['has_gene'] = taxid in has_gene_tax_set

    # Calculate lineage (from self back up to root node) for each entry
    for entry in entries.values():
        get_lineage(entry, entries)

    # Build parent-to-children mapping
    parent_to_children = defaultdict(list)
    for entry in entries.values():
        parent_id = entry['parent_taxid']
        if parent_id != entry['taxid']:  # Exclude root node
            parent_to_children[parent_id].append(entry['taxid'])

    # Set 'children' field
    for entry in entries.values():
        entry['children'] = parent_to_children.get(entry['taxid'], [])

    # Write everything back out to a flatfile for loading into elastic search
    # Each line is a json obj
    write_entries(entries, os.path.join(FLAT_FILE_PATH, 'tax.json'))

    return entries


def parse_refseq_names(names_file):
    '''
    names_file is a file-like object yielding 'names.dmp' from taxdump.tar.gz
    '''
    names = []
    # Collapse all the following fields into "synonyms"
    other_names = ["acronym", "anamorph", "blast name", "equivalent name", "genbank acronym", "genbank anamorph",
                   "genbank synonym", "includes", "misnomer", "misspelling", "synonym", "teleomorph"]
    # keep separate: "common name", "genbank common name"
    names_gb = groupby(names_file, lambda x: x[:x.index(b'\t')])
    for taxid, entry in names_gb:
        d = defaultdict(list)
        d['taxid'] = int(taxid)
        for line in entry:
            split_line = line.decode('utf-8').split('\t')
            field = split_line[6]
            value = split_line[2].lower()
            if field == 'scientific name':
                # only one per entry. Store as str (not in a list)
                d['scientific_name'] = value
            elif field in other_names:
                d['other_names'].append(value)  # always a list
            elif field == "common name":
                if d['common_name'] == []:  # empty
                    d['common_name'] = value  # set as string
                elif isinstance(d['common_name'], str):  # has a single entry
                    d['common_name'] = [d['common_name']]  # make it a list
                    d['common_name'].append(value)
                else:
                    d['common_name'].append(value)
            elif field == "genbank common name":
                if d['genbank_common_name'] == []:  # empty
                    d['genbank_common_name'] = value  # set as string
                elif isinstance(d['genbank_common_name'], str):  # has a single entry
                    d['genbank_common_name'] = [
                        d['genbank_common_name']]  # make it a list
                    d['genbank_common_name'].append(value)
                else:
                    d['genbank_common_name'].append(value)
            else:
                d[field].append(value)
        names.append(dict(d))
    return names


def parse_refseq_nodes(nodes_file):
    '''
    nodes_file is a file-like object yielding 'nodes.dmp' from taxdump.tar.gz
    '''
    nodes = []
    for line in nodes_file:
        d = dict()
        split_line = line.decode('utf-8').split('\t')
        d['taxid'] = int(split_line[0])
        d['parent_taxid'] = int(split_line[2])
        d['rank'] = split_line[4]
        nodes.append(d)
    return nodes


def parse_uniprot_speclist(uniprot_speclist):
    '''
    uniprot_speclist is a file-like object yielding 'speclist.txt'
    '''
    uniprot = []
    while True:
        line = next(uniprot_speclist)
        if line.startswith('_____'):
            break
    for line in uniprot_speclist:
        if 'N=' in line:
            organism_name = line.split('N=')[-1].strip().lower()
            taxonomy_id = int(line.split()[2][:-1])
            uniprot.append(
                {'uniprot_name': organism_name, 'taxid': taxonomy_id})
    return uniprot


def combine_by_taxid(*args):
    # Accepts multiple lists of dictionaries
    # Combines into one dictionary of dictionary where the key is the 'taxid'
    # of all input list of dictionaries
    d = defaultdict(dict)
    for l in args:
        for elem in l:
            d[elem['taxid']].update(elem)
    entries = dict()
    for entry in d.values():
        entries[entry['taxid']] = entry
    return entries


def get_lineage(entry, entries):
    if entry['taxid'] == entry['parent_taxid']:  # take care of node #1
        entry['lineage'] = [entry['taxid']]
        return entry
    lineage = [entry['taxid'], entry['parent_taxid']]
    while lineage[-1] != 1:
        parent = entries.get(lineage[-1])
        if parent is None:
            # Handle missing parent
            break
        if 'lineage' in parent:  # caught up with already calculated lineage
            # extend list, don't recalculate
            lineage.extend(parent['lineage'][1:])
            break
        lineage.append(parent['parent_taxid'])
    entry['lineage'] = lineage
    return entry


def write_entries(entries, filepath):
    f = open(filepath, 'w')
    for entry in entries.values():
        f.write(json.dumps(entry) + '\n')
    f.close()


if __name__ == "__main__":
    main()
