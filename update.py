from ftplib import FTP
from io import StringIO
from tqdm import tqdm
import os
import logging
import argparse
from argparse import RawTextHelpFormatter
import tarfile
import pickle

def need_to_update_release():
    """
    Check whether the user currently has the latest GB release (in which case
    we only need to download the daily updates) or whether they have an old
    release or no release, in which case we need to download everything)
    """
    try:
        current_release_number = int(open('GB_Release_Number').read())
        logging.info(
            'You currently have GB release number {}'
            .format(current_release_number)
            )

    except IOError:
        logging.info('No current release, downloading the files')
        return True

    latest_release_file = StringIO()
    ftp.retrlines('RETR GB_Release_Number', latest_release_file.write)
    latest_release_number = int(latest_release_file.getvalue())
    logging.info('Latest release number is {}'.format(latest_release_number))

    if current_release_number == latest_release_number:
        logging.info('You have the latest release, getting daily updates')
        return False
    else:
        logging.info('New release available, downloading the files')
        return True


def get_daily_updates():
    ftp.cwd('daily-nc')

    files_to_download = []
    for filename, file_info in ftp.mlsd():
        if filename.startswith('nc') and filename.endswith('.flat.gz'):
            logging.debug('checking ' + filename)
            if os.path.exists(filename):
                logging.debug("already got {}".format(filename))
            else:
                files_to_download.append((filename, file_info))
    total_size = sum([int(f[1]['size']) for f in files_to_download])
    if total_size > 0:
        logging.info(
            'about to download {} MB, hit enter to continue or Ctrl+C to cancel...'
            .format(round(total_size / 10 ** 6))
            )
        input()
        with tqdm(
            files_to_download,
            unit='files',
            desc='Downloading {} files'.format(len(files_to_download))
        ) as file_pbar:
            for f in file_pbar:
                download(f)

def build_ncbi_names_dicts():
    names = open("names.dmp")
    name2taxid = {}
    taxid2name = {}

    for line in names:
        taxid, name, other_name, type = line.rstrip('\t|\n').split("\t|\t")
        name2taxid[name] = int(taxid)
        if type == 'scientific name':
            taxid2name[int(taxid)] = name

    pickle.dump( name2taxid, open( "name2taxid.p", "wb" ) )
    pickle.dump( taxid2name, open( "taxid2name.p", "wb" ) )

def build_ncbi_nodes_dicts():
    taxid2rank = {}
    taxid2parent = {}

    #store parent to child relationships
    parent2child = {}

    processed = 0
    nodes = open("nodes.dmp")
    for line in nodes:
        taxid, parent, rank = line.rstrip('\t|\n').split("\t|\t")[0:3]
        taxid = int(taxid)
        parent = int(parent)
        taxid2rank[int(taxid)] = rank
        taxid2parent[int(taxid)] = int(parent)
        if parent not in parent2child:
            parent2child[parent] = []
        parent2child[parent].append(taxid)

    pickle.dump( taxid2rank, open( "taxid2rank.p", "wb" ) )
    pickle.dump( taxid2parent, open( "taxid2parent.p", "wb" ) )
    pickle.dump( parent2child, open( "parent2child.p", "wb" ) )


def get_taxdump():
    logging.debug('starting download taxdump')
    logging.info('downloading taxonomy dump...')
    ftp.cwd('/pub/taxonomy')

    for filename, file_info in ftp.mlsd():
        if filename == 'taxdump.tar.gz':
            download((filename, file_info))

    with tqdm(total=3, desc='extracting files from taxdump') as pbar:
        logging.debug('extracting files from taxdump')
        tar = tarfile.open('taxdump.tar.gz', 'r:gz')
        tar.extractall()
        tar.close()
        pbar.set_description('reading names from taxonomy')
        pbar.update(1)
        logging.debug('finishing download taxdump')
        logging.debug('building NCBI dicts')


        build_ncbi_names_dicts()
        pbar.set_description('reading nodes from taxonomy')
        pbar.update(1)


        build_ncbi_nodes_dicts()

        pbar.update(1)





def download(myfile):
    filename, file_info = myfile
    with tqdm(
                total=int(file_info['size']),
                desc=filename,
                unit='bytes',
                unit_scale=True,
                leave=False
              ) as pbar:
        with open(filename, 'wb') as output:
            def handle_block(block):
                pbar.update(len(block))
                output.write(block)
            ftp.retrbinary('RETR ' + filename, handle_block)


def do_update_release():
    logging.debug('looking for divisions: {}'.format(args.divisions))
    files_to_download = []
    for filename, file_info in ftp.mlsd():
        file_division = filename[2:5]
        if (
            filename.startswith('gb')
            and file_division.upper() in args.divisions
        ):
            files_to_download.append((filename, file_info))

    total_size = sum([int(f[1]['size']) for f in files_to_download])
    logging.info(
        'about to download {} MB, hit enter to continue or Ctrl+C to cancel...'
        .format(round(total_size / 10 ** 6))
        )
    input()
    with tqdm(
        files_to_download,
        unit='files',
        desc='Downloading {} files'.format(len(files_to_download))
    ) as file_pbar:
        for f in file_pbar:
            download(f)

    with open('GB_Release_Number', 'wb') as output:
        ftp.retrbinary('RETR GB_Release_Number', output.write)


def delete_old_files():
    logging.info('Warning, about to delete files from your old release')
    logging.info('Hit enter to continue or Ctrl+C to cancel...')
    input()
    for filename in os.listdir('.'):
        if filename.endswith('.gz'):
            os.remove(filename)


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

if need_to_update_release() or args.force:
    delete_old_files()
    do_update_release()

get_daily_updates()
get_taxdump()
