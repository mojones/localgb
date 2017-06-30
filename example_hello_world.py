import localgb
import sys
import re

length_regex = re.compile('source          1..(\d+)')

total_length = 0

#@profile
def process_record(record):

    global total_length
    match = re.search(length_regex, record)
    if match:   # some source features are more complicated, ignore them
        total_length += int(match.group(1))

localgb.do_search_generic(process_record, filenames=sys.argv[1:])

print('counted {:,d} bases total\n\n'.format(total_length))
