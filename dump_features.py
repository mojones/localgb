import sys
import collections
import re
import gzip
import tqdm

numbers = set('0123456789 ')


feature_re = re.compile('^     ([a-zA-Z]+)\s+')
qualifier_re = re.compile('^                     /(.+)=.+')

types = collections.Counter()
qualifiers = collections.defaultdict(collections.Counter)

last_type = None
filenames = tqdm.tqdm(sys.argv[1:], unit='files')
for filename in filenames:
    if filename.endswith('.gz'):
        genbank_file = gzip.open(filename, mode="rt", encoding='latin-1')
    else:
        genbank_file = open(filename, encoding='latin-1')

    for line in genbank_file:
        if line.startswith('     ') and line[5] not in numbers: # hacky way to avoid running regex on all lines
            #print('checking ~~~' + line + '~~~')
            type_match =re.search(feature_re, line)
            if type_match:
                types[type_match.group(1)] += 1
                last_type = type_match.group(1)
        if line.startswith('                     '):
            qualifier_match = re.search(qualifier_re, line)
            if qualifier_match:
                qualifiers[last_type][qualifier_match.group(1)] += 1

for type, count in types.most_common(100):
    print('{} : {}'.format(type, count))
    for qualifier, count in qualifiers[type].most_common(100):
        print('\t{} : {}'.format(qualifier, count))
