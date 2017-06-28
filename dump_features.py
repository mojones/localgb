from Bio import SeqIO
import sys
import collections
import re

feature_re = re.compile('^     ([a-zA-Z]+)\s+')
qualifier_re = re.compile('^                     /(.+)=.+')

types = collections.Counter()
qualifiers = collections.defaultdict(collections.Counter)

last_type = None
for filename in sys.argv[1:]:
    for line in open(filename):
        type_match =re.search(feature_re, line)
        if type_match:
            types[type_match.group(1)] += 1
            last_type = type_match.group(1)
        qualifier_match = re.search(qualifier_re, line)
        if qualifier_match:
            qualifiers[last_type][qualifier_match.group(1)] += 1

for type, count in types.most_common(100):
    print('{} : {}'.format(type, count))
    for qualifier, count in qualifiers[type].most_common(100):
        print('\t{} : {}'.format(qualifier, count))
