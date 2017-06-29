import logging
import argparse
from argparse import RawTextHelpFormatter

import localgb




parser = argparse.ArgumentParser(
    description='Create or update a local mirror of GenBank flat files',
    formatter_class=RawTextHelpFormatter
)
parser.add_argument(
    "-v", "--verbosity", action="count", help="increase output verbosity"
)
parser.add_argument(
    "-d", "--divisions", nargs='*', required=True,
    help="""
space-separated list of the divisions you want to download. Valid divisions
are:

Organismal divisions

BCT Bacterial sequences
PRI Primate sequences
ROD Rodent sequences
MAM Other mammalian sequences
VRT Other vertebrate sequences
INV Invertebrate sequences
PLN Plant sequences
VRL Viral sequences
PHG Phage sequences
RNA Structural RNA sequences
SYN Synthetic and chimeric sequences
UNA Unannotated sequences
ENV Environmental samples

Functional Divisions

EST Expressed sequence tags
STS Sequence tagged sites
GSS Genome survey sequences
HTG High throughput genomic sequences
HTC High throughput cDNA
PAT Patent sequences
TSA Transcriptome shotgun data
    """
)
parser.add_argument(
    "--force",
    action="store_true",
    help="delete existing files and download the current release even if your\
    copy is up to date"
)
args = parser.parse_args()

args.divisions = [d.upper() for d in args.divisions]

if args.verbosity is None:
    logging.basicConfig(level=logging.INFO)
elif args.verbosity > 0:
    logging.basicConfig(level=logging.DEBUG)


ftp = FTP('ftp.ncbi.nlm.nih.gov')
ftp.login()
ftp.cwd('genbank')

if localgb.need_to_update_release() or args.force:
    localgb.delete_old_files()
    localgb.do_update_release()

localgb.get_daily_updates()
localgb.get_taxdump()
