from ftplib import FTP
from io import StringIO
from tqdm import tqdm
import time
from multiprocessing import Pool
import os



def need_to_update_release():
    """
    Check whether the user currently has the latest GB release (in which case
    we only need to download the daily updates) or whether they have an old
    release or no release, in which case we need to download everything)
    """
    try:
        current_release_number = int(open('GB_Release_Number').read())
        print(
            'You currently have GB release number {}'
            .format(current_release_number)
            )

    except IOError:
        print('No current release, downloading the files')
        return True

    latest_release_file = StringIO()
    ftp.retrlines('RETR GB_Release_Number', latest_release_file.write)
    latest_release_number = int(latest_release_file.getvalue())
    print('Latest release number is {}'.format(latest_release_number))

    if current_release_number == latest_release_number:
        print('You have the latest release, getting daily updates')
        return False
    else:
        print('New release available, downloading the files')
        return True


def get_daily_updates():
    ftp.cwd('daily-nc')

    files_to_download = []
    for filename, file_info in ftp.mlsd():
        if filename.startswith('nc') and filename.endswith('.flat.gz'):
            print('checking ' + filename)
            if os.path.exists(filename):
                print("already got {}".format(filename))
            else:
                files_to_download.append((filename, file_info))
    with tqdm(
        files_to_download,
        unit='files',
        desc='Downloading {} files'.format(len(files_to_download))
    ) as file_pbar:
        for f in file_pbar:
            download(f)


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
    files_to_download = []
    for filename, file_info in ftp.mlsd():
        file_division = filename[2:5]
        if filename.startswith('gb') and file_division in divisions:
            files_to_download.append((filename, file_info))
    # pool = Pool(4)
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
    print('Warning, about to delete files from your old release')
    print('Hit Ctrl+C to prevent this from happening...')

    for filename in os.listdir('.'):
        if filename.endswith('.gz'):
            os.remove(filename)


divisions = ['phg', 'syn']

ftp = FTP('ftp.ncbi.nlm.nih.gov')
ftp.login()
ftp.cwd('genbank')

if need_to_update_release():
    delete_old_files()
    do_update_release()

get_daily_updates()
