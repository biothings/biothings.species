from collections import defaultdict
from itertools import groupby


def parse_refseq_names(names_file):
    '''
    names_file is a file-like object yielding 'names.dmp' from taxdump.tar.gz
    '''
    # Collapse all the following fields into "synonyms"
    other_names = ["acronym", "anamorph", "blast name", "equivalent name", "genbank acronym", "genbank anamorph",
                   "genbank synonym", "includes", "misnomer", "misspelling", "synonym", "teleomorph"]
    # keep separate: "common name", "genbank common name"
    names_gb = groupby(names_file, lambda x: x[:x.index('\t')])
    for taxid, entry in names_gb:
        d = defaultdict(list)
        d['taxid'] = int(taxid)
        d['_id'] = taxid
        for line in entry:
            split_line = line.split('\t')
            field = split_line[6]
            value = split_line[2].strip()
            if field == 'scientific name':
                # only one per entry. Store as str (not in a list)
                d['scientific_name'] = value
            elif field in other_names:
                d['other_names'].append(value)  # always a list
            elif field == "common name":
                if d['common_name'] == []:  # empty
                    d['common_name'] = value  # set as string
                elif type(d['common_name']) == str:  # has a single entry
                    d['common_name'] = [d['common_name']]  # make it a list
                    d['common_name'].append(value)
                else:
                    d['common_name'].append(value)
            elif field == "genbank common name":
                if d['genbank_common_name'] == []:  # empty
                    d['genbank_common_name'] = value  # set as string
                elif type(d['genbank_common_name']) == str:  # has a single entry
                    d['genbank_common_name'] = [
                        d['genbank_common_name']]  # make it a list
                    d['genbank_common_name'].append(value)
                else:
                    d['genbank_common_name'].append(value)
            else:
                d[field].append(value)
        yield dict(d)


def parse_refseq_nodes(nodes_file):
    '''
    nodes_file is a file-like object yielding 'nodes.dmp' from taxdump.tar.gz
    '''
    for line in nodes_file:
        d = dict()
        split_line = line.split('\t')
        taxid = split_line[0]
        d["_id"] = taxid
        d['taxid'] = int(taxid)
        d['parent_taxid'] = int(split_line[2])
        d['rank'] = split_line[4]
        yield d
