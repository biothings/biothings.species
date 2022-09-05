# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 11:09:56 2014

@author: Greg

Taxonomy Parser


Much faster than the version in taxonomy.py

Does everything in memory instead of through mongodb (~2-3 hrs > ~30 sec)

To import manually:
cat tax.json | parallel -j8 --pipe mongoimport -d taxonomy -c taxonomy
mongo taxonomy --eval "db.taxonomy.ensureIndex({'taxid': true})"
mongo taxonomy --eval "db.taxonomy.ensureIndex({'lineage': true})"
mongo taxonomy --eval "db.taxonomy.ensureIndex({'parent_taxid': true})"

"""

import tarfile
import os
import json
from collections import defaultdict
from itertools import groupby

## *** Download these files *****
'''
wget -N ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
wget -N ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/docs/speclist.txt
wget -N ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
'''
# ********Run this command! makes a file containing a unique list of tax_ids********
'''
gunzip -c gene_info.gz | tail -n+2 | cut -f1 | sort | uniq > gene_info_uniq
'''
## ****Change Me *****
FLAT_FILE_PATH = "flat_files"

def main():
    '''
    Build the taxonomy database from flatfiles downloaded from ncbi and uniprot

    Mandatory fields
    'taxid':            organism's taxonomy ID
    'parent_taxid':     organism's parent's tax ID (from refseq nodes file)
    'scientific_name':  organism's name from refseq names file
    'rank':             one of: ['superkingdom', 'kingdom', 'subkingdom', 'superphylum', 'phylum', 'subphylum',
                        'superclass', 'class', 'subclass', 'infraclass', 'superorder', 'order', 'suborder',
                        'infraorder', 'parvorder', 'superfamily', 'family', 'subfamily', 'tribe', 'subtribe', 'genus', 
                        'subgenus', 'species group', 'species subgroup', 'species', 'subspecies', 'varietas', 'forma', 'no rank']
    'rank#':            Rank in 'rank', starting with 'superkingdom': 0  to 'forma': 27. 'no rank': None

    Optional fields
    'other_names':          list of strings from following fields cat together (optional)
                            ["acronym","anamorph","blast name","equivalent name","genbank acronym","genbank anamorph",
                             "genbank synonym","includes","misnomer","misspelling","synonym","teleomorph"]
    'uniprot_name':         organism name from uniprot (optional)
    'common_name' :         organism's common name from refseq names file (optional)
    'genbank_common_name':  organism's genbank common name from refseq names file (optional)
    'authority':            reference to the taxonomic publication where the name was first described
    'type material':        http://www.ncbi.nlm.nih.gov/news/01-21-2014-sequence-by-type/
    'in-part':              useful as retrieval terms

    More information on fields here: http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3245000/

    List all fields:
    cat names.dmp | cut -f7 | sort | uniq

    List all ranks:
    cat nodes.dmp | cut -f5 | sort | uniq
    '''
    # Possible ranks
    ranks = ['superkingdom', 'kingdom', 'subkingdom', 'superphylum', 'phylum', 'subphylum', 'superclass', 'class', 'subclass', 'infraclass', 'superorder',
     'order', 'suborder', 'infraorder', 'parvorder', 'superfamily', 'family', 'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'species group',
     'species subgroup', 'species', 'subspecies', 'varietas', 'forma', 'no rank']

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

    # combines list of dictionaries into dictionary of dictionaries where key on outer dict is 'taxid'
    entries = combine_by_taxid(names, nodes, uniprot)

    # Some tax_ids in uniprot but not in ncbi nodes file, so make sure there's a parent_taxid for each entry
    entries = dict([(key, value) for (key,value) in entries.items() if 'parent_taxid' in value.keys()])

    # Set rank#
    for taxid in entries.keys():
        entries[taxid]['rank#'] = None if entries[taxid]['rank'] == 'no rank' else ranks.index(entries[taxid]['rank'])

    # Mark tax_ids that have a gene in ncbi
    in_file = os.path.join(FLAT_FILE_PATH, 'gene_info_uniq')
    with open(in_file) as f:
        has_gene_tax_set = set([int(line) for line in f])
    for taxid, entry in entries.items():
        entry['has_gene'] = taxid in has_gene_tax_set

    # Calculate lineage (from self back up to root node) for each entry
    for entry in entries.values():
        get_lineage(entry, entries)

    # Write everythig back out to a flatfile for loading into elastic search        
    # Each line is a json obj
    write_entries(entries, os.path.join(FLAT_FILE_PATH, 'tax.json'))

    # Or just insert them to mongodb. hardcoded, sorry. todo Add command-line args
    #mongo_import(entries)

    return entries

def parse_refseq_names(names_file):
    '''
    names_file is a file-like object yielding 'names.dmp' from taxdump.tar.gz
    '''
    names = []
    #Collapse all the following fields into "synonyms"
    other_names = ["acronym","anamorph","blast name","equivalent name","genbank acronym","genbank anamorph",
    "genbank synonym","includes","misnomer","misspelling","synonym","teleomorph"]
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
                d['scientific_name'] = value #only one per entry. Store as str (not in a list)
            elif field in other_names:
                d['other_names'].append(value) #always a list
            elif field == "common name":
                if d['common_name'] == []: #empty
                    d['common_name'] = value # set as string
                elif type(d['common_name']) == str: # has a single entry
                    d['common_name'] = [d['common_name']] #make it a list
                    d['common_name'].append(value)
                else:
                    d['common_name'].append(value)
            elif field == "genbank common name":
                if d['genbank_common_name'] == []: #empty
                    d['genbank_common_name'] = value # set as string
                elif type(d['genbank_common_name']) == str: # has a single entry
                    d['genbank_common_name'] = [d['genbank_common_name']] #make it a list
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
        if line.count('N='):
            organism_name = line.split('N=')[-1].strip().lower()
            taxonomy_id = int(line.split()[2][:-1])
            uniprot.append({'uniprot_name': organism_name, 'taxid': taxonomy_id})
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
    if entry['taxid'] == entry['parent_taxid']: #take care of node #1
        entry['lineage'] = [entry['taxid']]
        return entry
    lineage = [entry['taxid'], entry['parent_taxid']]
    while lineage[-1] != 1:
        parent = entries[lineage[-1]]
        if 'lineage' in parent: # caught up with already calculated lineage
            lineage.extend(parent['lineage'][1:]) # extend list, don't recalculate
            entry['lineage'] = lineage
            return entry
        lineage.append(parent['parent_taxid'])
    entry['lineage'] = lineage
    return entry

def get_all_children(taxid, entries, has_gene = True):
    if has_gene:
        return [taxid] + [value['taxid'] for (key,value) in entries.items() if taxid in value['lineage'] and value['has_gene'] == True]
    else:
        return [taxid] + [value['taxid'] for (key,value) in entries.items() if taxid in value['lineage']]

def write_entries(entries, filepath):
    f = open(filepath, 'w')
    for entry in entries.values():
        f.write(json.dumps(entry) + '\n')
    f.close()

def mongo_import(entries):
    from pymongo import MongoClient
    client = MongoClient()
    db = client.taxonomy.taxonomy
    entries_list = [d for d in entries.values()]
    db.insert(entries_list)
    db.create_index('lineage')
    db.create_index('taxid')
    db.create_index('parent_taxid')

if __name__ == "__main__":
    main()
    #pass
