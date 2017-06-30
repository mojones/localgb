import os
from io import StringIO
from tqdm import tqdm
import argparse
import re
import logging
import gzip
import time
import localgb


# hide gb file warnings, don't do this in production
import warnings
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(
    description='Query genbank files based on features.'
    )
parser.add_argument('--output',  help='output file', required=True)

parser.add_argument(
    "-v", "--verbosity", action="count", help="show lots of debugging output", default=0
)

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

parser.add_argument(
    '--taxid-file',
    help="file with taxids that we want to allow. Probably created using get_taxids.py."
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
action_group.add_argument(
    '--fasta-protein-features',
    action='store_true',
    help='attempt to get a translation from the matching features andw write in FASTA format to the output file. Note: this is unlikely to work on anything other than CDS type features.'
    )

parser.add_argument(
    '--files', nargs='+', help='genbank files to process', required=True
    )
args = parser.parse_args()

if args.verbosity is None:
    logging.basicConfig(level=logging.INFO)
elif args.verbosity > 0:
    logging.basicConfig(level=logging.DEBUG)







localgb.do_search(process_record_function=localgb.process_record, args=args)
