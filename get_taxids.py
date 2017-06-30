import pickle
import argparse





def get_children(taxon):
	# print('taxon is ~~' + taxon + '~~')
	taxon_taxid = name2taxid.get(taxon, 'none')
	# print(' taxon taxid is ' + str(taxon_taxid))
	children = parent2child.get(taxon_taxid, [])
	return [taxid2name[x] for x in children]

def get_children_multiple(taxon, count):
	current_list = [taxon]
	while count > 0:
		new_list = []
		for current_taxon in current_list:
			new_list.extend(get_children(current_taxon))
		current_list = new_list
		count += -1
	return new_list


def get_parent(taxon):
	taxon_taxid = name2taxid.get(taxon, 'none')
	taxon_parent_taxid = taxid2parent.get(taxon_taxid, 'none')
	return taxid2name.get(taxon_parent_taxid, 'none')

def get_parent_multiple(taxon, count):
	current_taxon = taxon
	while count > 0:
		current_taxon = get_parent(current_taxon)
		count += -1
	return current_taxon

def get_siblings(taxon):
	return filter( lambda x : x != taxon, get_children(get_parent(taxon)))

def get_siblings_multiple(taxon, count):
	parent = get_parent_multiple(taxon, count)
	return filter( lambda x : x != taxon, get_children_multiple(parent, count))

# recursive function to get all the children of a given taxid
def get_children_recursive(taxid):
    result = []
    # for all children of this taxid...
    for child in parent2child[taxid]:
        # first add the child itself
        result.append(child)
        # then if the child has children...
        if child in parent2child:
            # add the children of the child
            # note that we use extend() here rather than append()
            # extend() is the equivalent of concatenating two lists
            # if we use append() here then we get a set of nested list which is not what we want!
            result.extend(get_children_recursive(child))
    return result

def get_named_children(taxon, rank):
	print('getting all ' + rank)
	all_children = get_children_recursive(name2taxid[taxon])
	return list([taxid2name[child] for child in all_children if taxid2rank[child] == rank])

def get_all_parents(species):
    result = []
    current_taxid = species
    found = False
    while current_taxid != 1:
        result.append(current_taxid)
        parent_taxid = taxid2parent[current_taxid]
        current_taxid = parent_taxid
    result.append(1)
    return result


def find_lca(species1, species2):
    species1_parents = get_all_parents(species1)
    species2_parents = get_all_parents(species2)
    for parent in species1_parents:
        if parent in species2_parents:
            return parent


def find_lca_multiple(list_of_species):
    # the lca of a single species is itself
    # so we will set the lca to be the first species
    current_lca = name2taxid[list_of_species[0]]
    # now go through the list of species
    for species in list_of_species:
        #set the new lca to the the lca of the current species and the old lca
        current_lca = find_lca(name2taxid[species], current_lca)
    return taxid2name[current_lca]


parser = argparse.ArgumentParser(
    description='Get lists of taxids from the NCBI taxonomy'
    )

parser.add_argument('--output',  help='output file to write taxids to')

parser.add_argument(
    '--include',
    nargs='+',
    help="space-separated list of taxids who's descendents we want to include",
    type=int
    )

parser.add_argument(
    '--exclude',
        nargs='+',
        type=int,
    help="space-separated list of taxids who's descendents we want to exclude",
	default=[]
    )

parser.add_argument(
    '--lookup',
    help="a taxon name who's taxid you want to look up. If this option is used the program will just output the taxid(s)"
    )

args = parser.parse_args()


if args.lookup is not None:
    print('reading names....', end='\r')
    name2taxid = pickle.load( open( "name2taxid.p", "rb" ) )
    print('loading taxonomy....done!')
    taxids = name2taxid.get(args.lookup)
    if taxids is None:
        print("Couldn't find a taxid for {}".format(args.lookup))
    elif len(taxids) > 1:
        print("Found multiple taxids for that name:")
        print('\n'.join(taxids))
    else:
        print(taxids[0])

else:
    selected_taxids = set()
    print('reading nodes....', end='\r')
    parent2child = pickle.load( open( "parent2child.p", "rb" ) )
    print('reading nodes....done')

    for include_taxid in args.include:
        selected_taxids = selected_taxids.union(get_children_recursive(include_taxid))
        print('after adding children of {} we have {} taxids'.format(
            include_taxid, len(selected_taxids)
        ))

    for exclude_taxid in args.exclude:
        selected_taxids = selected_taxids.difference(get_children_recursive(exclude_taxid))
        print('after removing children of {} we have {} taxids'.format(
            exclude_taxid, len(selected_taxids)
        ))
    with open(args.output, 'wt') as output_file:
        for taxid in selected_taxids:
            output_file.write('{}\n'.format(taxid))
    print('wrote {} taxids to {}'.format(
        len(selected_taxids), args.output
    ))

# taxid2name = pickle.load( open( "taxid2name.p", "rb" ) )
# taxid2rank = pickle.load( open( "taxid2rank.p", "rb" ) )
# taxid2parent = pickle.load( open( "taxid2parent.p", "rb" ) )
# parent2child = pickle.load( open( "parent2child.p", "rb" ) )
