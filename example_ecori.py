import localgb
import sys
import re
from Bio import SeqIO
from io import StringIO




#@profile
def process_record(record):

    if 'gaattc' in record.lower(): # quick check, might be false positive
        real_record = SeqIO.read(StringIO(record), format='gb')
        if 'gaattc' in str(real_record.seq).lower():
            output_file.write(record)

with open('ecori.gb', 'wt') as output_file:
    localgb.do_search_generic(process_record, filenames=sys.argv[1:])
