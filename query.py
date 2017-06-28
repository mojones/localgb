from Bio import SeqIO
import os
from io import StringIO
from tqdm import tqdm
import argparse

# hide gb file warnings, don't do this in production
import warnings
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(
    description='Query genbank files based on features.'
    )
parser.add_argument('--output',  help='output file', required=True)

parser.add_argument(
    '--type',
    required=True,
    help="""
The feature type to look for. Interesting types include:

    source

    gene
    CDS
    intron
    exon

    repeat_region
    variation
    mobile_element
    regulatory

    5'UTR
    3'UTR
    polyA_site

    rRNA
    tRNA
    mRNA
    ncRNA

but there are many more. Run dump_features.py to see them all
"""
    )

parser.add_argument(
    '--qualifier',
    help="""
The qualifier who's value you want to check. Tip: to see what qualifiers
a given feature type most commonly has, run dump_features.
"""
    )

parser.add_argument(
        '--terms',
        nargs='+',
        help="""
Space-separated list of the values you want to find in your feature qualifiers.
If there are spaces in the values you'll need to surround the whole thing
with quotes.
"""
    )

# all the different things we can do wtih the records/features we find
action_group = parser.add_mutually_exclusive_group(required=True)
action_group.add_argument(
    '--fasta-features',
    action='store_true',
    help='output features as FASTA sequences to stdout'
    )
action_group.add_argument(
    '--count-features',
    action='store_true',
    help='count the number of features/records that match the query'
    )
action_group.add_argument(
    '--dump-genbank',
    action='store_true',
    help='write genbank records with matching features to stdout'
    )

parser.add_argument(
    '--files', nargs='+', help='genbank files to process', required=True
    )
args = parser.parse_args()
args.terms = [t.lower() for t in args.terms]


def myreadlines(f, newline):
  buf = ""
  while True:
    while newline in buf:
      pos = buf.index(newline)
      yield buf[:pos] + newline
      buf = buf[pos + len(newline):]
    chunk = f.read(4096)
    if not chunk:
      yield buf + newline
      break
    buf += chunk


def long_substr(data):
    if len(data) == 1:
        return data[0]
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                    substr = data[0][i:i+j]
    return substr

def process_record(record, output_file):
    global matching_record_count
    global matching_feature_count
    keep = False
    if longest_substring in record.lower():
        real_record = SeqIO.read(StringIO(record), format='gb')
        for f in real_record.features:
            if f.type == args.type:
                if (
                    (
                    args.qualifier in f.qualifiers and
                    f.qualifiers[args.qualifier][0].lower() in args.terms
                    )
                    or args.qualifier is None
                 # note only looking at the first value, there can
                 # technically be a list but unlikely to be somethin
                 # we're interested in
                 ):
                    matching_feature_count += 1
                    keep = True

    if keep:
        matching_record_count += 1
        if args.dump_genbank:
            output_file.write(record)

if args.terms is None:
    longest_substring = args.type.lower()
else:
    longest_substring = long_substr(args.terms).lower()

print('looking for "{}"'.format(longest_substring))

matching_record_count = 0
matching_feature_count = 0

filenames = tqdm(args.files, unit='files')
with open(args.output, 'w') as output_file:
    for filename in filenames:
        filenames.set_description(
            'processing {}'.format(os.path.basename(filename))
        )
        for record in myreadlines(open(filename), '\n//\n'):
            process_record(record, output_file)


print('found {} matching features in {} records'.format(
    matching_feature_count, matching_record_count)
    )
