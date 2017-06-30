from ftplib import FTP
from io import StringIO
from tqdm import tqdm
import os
import logging
import tarfile
import pickle
import collections
import time
from Bio import SeqIO


def need_to_update_release():
    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login()
    ftp.cwd('genbank')

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
    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login()
    ftp.cwd('genbank')

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
                download(f, ftp)

def build_ncbi_names_dicts():
    names = open("names.dmp")
    name2taxid = collections.defaultdict(list)
    taxid2name = {}

    for line in names:
        taxid, name, other_name, type = line.rstrip('\t|\n').split("\t|\t")
        name2taxid[name].append(taxid)
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
    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login()
    ftp.cwd('/pub/taxonomy')

    for filename, file_info in ftp.mlsd():
        if filename == 'taxdump.tar.gz':
            download((filename, file_info), ftp)

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





def download(myfile, ftp):
    """
    Download myfile from the given ftp connection and draw a progress bar while
    doing it. myfile is a tuple of (filename, file_info) as returned by
    ftp.mlsd().
    """
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


def do_update_release(divisions):
    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login()
    ftp.cwd('genbank')

    logging.debug('looking for divisions: {}'.format(divisions))
    files_to_download = []
    for filename, file_info in ftp.mlsd():
        file_division = filename[2:5]
        if (
            filename.startswith('gb')
            and file_division.upper() in divisions
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
            download(f, ftp)

    with open('GB_Release_Number', 'wb') as output:
        ftp.retrbinary('RETR GB_Release_Number', output.write)


def delete_old_files():
    logging.info('Warning, about to delete files from your old release')
    logging.info('Hit enter to continue or Ctrl+C to cancel...')
    input()
    for filename in os.listdir('.'):
        if filename.endswith('.gz'):
            os.remove(filename)

def delimited(file, delimiter='\n', bufsize=4096):
    buf = ''
    while True:
        newbuf = file.read(bufsize)
        if not newbuf:
            yield buf
            return
        buf += newbuf
        lines = buf.split(delimiter)
        for line in lines[:-1]:
            yield line
        buf = lines[-1]

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

def process_record(record, args):
    global matching_record_count
    global matching_feature_count



    keep_record = False

    # if the quick test fails, we don't want this record
    if longest_substring not in record.lower():
        return None

    if taxid_set is not None:
        # check if we want to allow this taxid
        taxid_match = re.search('/db_xref="taxon:(\d+)"', record)
        taxid = taxid_match.group(1)
        if taxid not in taxid_set:
            logging.debug('taxid {} not in taxids file'.format(taxid))
            return None

    # if we get this far, we want to parse the record properly
    real_record = SeqIO.read(StringIO(record), format='gb')
    for f in real_record.features:
        keep_feature = False
        if f.type == args.type:
            if args.qualifier is None:
                keep_feature = True

            elif args.qualifier in f.qualifiers and args.terms is None:
                keep_feature=True

            elif args.qualifier in f.qualifiers and f.qualifiers[args.qualifier][0].lower() in args.terms:
                keep_feature = True

        if keep_feature:
            matching_feature_count += 1
            keep_record = True
            try:
                if args.fasta_features:
                    output_file.write('>{}\n{}\n'.format(
                        real_record.id,
                        str(f.extract(real_record).seq)
                    ))
            except ValueError:
                logging.debug("Couldn't extract feature from record {}".format(real_record.id))


            if args.fasta_protein_features:
                try:
                    output_file.write('>{}\n{}\n'.format(
                        real_record.id,
                        f.qualifiers['translation'][0]
                    ))
                except KeyError:
                    print('could not find a translation for feature:\n')
                    print(f)



    if keep_record:
        matching_record_count += 1
        if args.dump_genbank:
            output_file.write(record + '\n//\n')

longest_substring = None
taxid_set = None

matching_record_count = 0
matching_feature_count = 0

output_file = None

def do_search(args):

    global longest_substring
    global taxid_set
    global output_file


    # figure out what the cheap check is
    if args.terms is None and args.qualifier is None:
        longest_substring = args.type.lower()
    elif args.terms is None:
        longest_substring = args.qualifier.lower()
    else:
        if len(args.terms) == 1:
            longest_term_substring = args.terms[0]
        else:
            longest_term_substring = long_substr(args.terms).lower()

        if len(longest_term_substring) > 2:
            longest_substring = longest_term_substring
        else:
            longest_substring = args.qualifier.lower()
        args.terms = [t.lower() for t in args.terms]


    print('looking for "{}"'.format(longest_substring))

    taxid_set = None
    if args.taxid_file is not None:
        taxid_set = set([line.rstrip('\n') for line in open(args.taxid_file)])




    output_file = open(args.output, 'w')

    filenames_pbar = tqdm(args.files, unit='files')
    for filename in filenames_pbar:
        start = time.time()
        filenames_pbar.set_description(
            'processing {}, found {} ({}) matching features (records)'
            .format(os.path.basename(filename), matching_feature_count, matching_record_count)
        )
        if filename.endswith('.gz'):
            genbank_file = gzip.open(filename, mode="rt", encoding='latin-1')
        else:
            genbank_file = open(filename, encoding='latin-1')

        for record in delimited(genbank_file, '\n//\n', bufsize=4096*256):
            process_record(record, args)
        if args.verbosity > 0:
            logging.debug("{} took {} seconds".format(
            filename, time.time() - start
            ))
        output_file.close()

    print('found {} matching features in {} records'.format(
        matching_feature_count, matching_record_count)
        )

def do_search_generic(process_record_function, filenames):


    filenames_pbar = tqdm(filenames, unit='files')
    for filename in filenames_pbar:
        filenames_pbar.set_description(
            'processing {}'
            .format(os.path.basename(filename))
        )
        if filename.endswith('.gz'):
            genbank_file = gzip.open(filename, mode="rt", encoding='latin-1')
        else:
            genbank_file = open(filename, encoding='latin-1')

        for record in delimited(genbank_file, '\n//\n', bufsize=4096*256):
            if record != '': # sometimes we get empty records
                process_record_function(record)
