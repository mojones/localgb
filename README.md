# localgb
A collection of command line tools for mirroring and querying GenBank locally. 

Currently this is implemented as three Python programs. `update.py` is repsonsible for downloading and updating local copies of genbank format flat files and the NCBI taxonomy dump. `get_taxids.py` generates list of taxids to be used in searches. `query.py` searches your genbank files for records and features of interest and writes them to an output file. 

## Installation 

**Currently the scripts only work on Python 3**

First install dependencies:

`pip install tqdm biopython`

and ignore any biopython warnings about numpy. 

Next, clone the repo:

```
git clone https://github.com/mojones/localgb.git
cd localgb
```
## Tutorial

### Downloading the files

The first step is to download the genbank files you want. Run `python update.py --help` to see options. You need to explicitly say which divisions you want (see the help for brief description of the divisions). You'll see how much space it's going to take up so you have a chance to cancel if you don't have room. While the download is running you'll see a bunch of output:

![update](https://i.imgur.com/0b141z5.png)

At the point of this screenshot, I have an 1 hour 20 mins to wait. After it has downloaded the latest genbank release, it will go on and get the daily updates. Finally, it will get the genbank taxonomy dump (it does this every time you update, since it takes less time to download it than it would to figure out whether any new taxids have been added). 

If you run `update.py` again later, it will skip the release (unless there's a new one) and just get the daily updates (but not any that you already have). The daily updates aren't sorted by division, but that doesn't matter as they're much smaller. 


After this has finished you'll have 

- a bunch of files ending _.seq.gz_ which are the release files
- a bunch of files ending _.flat.gz_ which are the daily updates
- a bunch of files ending _.dmp_, which are the taxonomy dumps
- a bunch of files ending _.p_, which are the Python pickles of the taxonomy data structures (don't worry if this sounds like nonsense).


If you want to trade off some disk space for higher query speed at any point, extract the files by running

`gunzip *.gz` 

Extracted files take up about 4x as much space, and are about 2x as quick to query. 

### Extracting some taxids

Run `python get_taxids.py --help` to see how it works. Give a list of taxids who's descendents you want to include, and (optionally) a list of taxids whose descendents you want to exclude. We can add more fancy queries to this but I think this should take care of most cases. Examples:

```
# all molluscs
python get_taxids.py --include 6447 --output molluscs.txt

# all insects except genus Drosophila 
python get_taxids.py --include 50557 --exclude 7215 --output most_insects.txt

# all insects and chelicerates except dipterans and spiders
python get_taxids.py --include 50557 6843 --exclude 7147 6893 --output my_taxids.txt
```

You get the idea. If you're feeling lucky/lazy, you can also search for a taxid by name:

`python get_taxids.py --lookup Onychophora`

### Querying the genbank files

The interface for this is a bit more complicated. For reasons of flexibility, I made it so that you **have to** tell it:

- a feature type that you're looking for

and optionally:

- a qualifier (i.e. a property of a feature) that you want to check
- a list of possible values that the qualifier can take

This seems confusing, but trust me, it's a good design :-) So if I run the script with

```
--type CDS
--qualifier product
--terms enolase
```
I am looking for records that have a **CDS** feature, where that feature has a **product** qualifier, and where the product qualifier is **enolase**. Here's an example of a feature from a genbank file that fits the criteria:

```
... rest of the genbank fil e...

CDS             join(<1..100,165..311,373..463,532..>631)
      /gene="Eno"
      /codon_start=1
      /product="enolase"
      /protein_id="ACN51870.1"
      /translation="PEIILPTPAFNVINGGSHAGNKLAMQEFMIFPTGASSFTEAMRM
      GTETYHHLKKVINNRFGLDATAVGDEGGFAPNILNNKDALELISTAIEKAGYTGKIEI
      GMDVAASEFHKNGKYDLDFKNPASDPATYLESAKLAELYQEFIK"
       
... rest of the genbank file ...
```
To run the script, I also have to give a `--output` to specify an output file and a `--files` to specify the genbank files. Normally this will be `--files *.seq.gz *.flat.gz` if I havent' extracted the files, or `--files *.seq *.flat` if I have).

Finally, I also have to specify what I want to do with the records/features that I find. So far there are three options:

- `--count-features` : just print out how many features matched the query
- `--fasta-features` : write the feature sequences out in FASTA format to the output file
- `--fasta-protein-features` : write the feature protein sequences out in FASTA format to the output file. This only works for features that have a `translation` qualifier, which AFAIK is only **CDS** features. 
- `--dump-genbank` : write out the records that contain matching features in genbank format to the output file. Of course, this file can then be the input file for a different query. 

So, a complete command line will look like this...

```
# search for records containing enolase coding sequences and write the resulting records to enolase.gb
python query.py --type CDS --qualifier product --terms enolase --output enolase.gb --files *.seq --dump-genbank

```
While the query is running we get a similar progress bar to the download stage so we can estimate how long it's going to take.

If we want to do the same search but get FASTA records for the enolase coding sequences themselves, we will pass `--fasta-features` instead of `--dump-genbank`:

```
# search for records containing enolase coding sequences and write the resulting records to enolase.gb
python query.py --type CDS --qualifier product --terms enolase --output enolase.fasta --files *.seq --fasta-features
```
Note that with the above command we get the sequence of **just the features**, not the entire records. Since the feature type here is **CDS**, which normally have **translation** qualifiers, I can also get the protein sequences:

```
# search for records containing enolase coding sequences and write the resulting records to enolase.gb
python query.py --type CDS --qualifier product --terms enolase --output enolase_proteins.fasta --files *.seq --fasta-protein-features
```
If we're not sure what feature or qualifier we should be looking for, we can run `dump_features.py` on some genbank files (compressed or not) and it will tell us what the most common features were and what the most common qualifiers were for those features:

```
python dump_features.py *.seq.gz`
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 22/22 [01:37<00:00,  3.87s/files]
source : 1173339
	db_xref : 1531335
	organism : 1173339
	mol_type : 1173339
	PCR_primers : 714685
	organelle : 539534
	country : 524426
	estimated_length : 459494
 ... etc ...
 ```

This is kind of slow as it involves running a lot of regular expressions, so you probably want to save the output somewhere so you don't need to run it too often. 

### Limiting by taxid

To restrict the search to a list of taxids (probably generated by `get_taxids.py` add it as a `--taxid-file` argument to any kind of search):

```
# extract enolase protein FASTA sequences only from molluscs
python query.py --type CDS --qualifier product --terms enolase --output enolase_proteins.fasta --files *.seq --fasta-protein-features --taxid-file molluscs.txt
```

### Searching just for features

If we want to find all features that match a particular type, and don't care about any of the qualifiers, omit the `--qualifier` or `--terms` option or both:

```
# extract all transfer RNA sequences from molluscs
python query.py --type tRNA --output tRNAs.fasta --files *.seq --fasta-features --taxid-file molluscs.txt 
looking for "trna"
```

### Finding genes with multiple synonyms

If, as is often the case, there's more than one name for a gene, just give multiple arguments to `--terms`. Remember to use quotes around names that have spaces in or the shell will get confused:

```
# get COX1 protein sequences for molluscs 
python query.py --type CDS --qualifier product --terms "cytochrome oxidase subunit 1" "cytochrome oxidase subunit I" --output cox1_proteins.fasta --files *.seq --fasta-protein-features --taxid-file molluscs.txt 
```

## Examples

### Taxonomic pre-filtering

If we know that we're going to be running a bunch of queries on the same taxonomic group, we can use a taxids file and search for the **source** feature (which every record has), then dump the resulting genbank records and use that file as the input for subsequent queries:

```
# dump all mollusc records
python query.py --type CDS --qualifier product --terms "cytochrome oxidase subunit 1" "cytochrome oxidase subunit I" --output enolase_proteins.fasta --files *.seq --fasta-protein-features --taxid-file molluscs.txt 

# now search in the prefiltered gb file
python query.py --type CDS --qualifier product --terms "cytochrome oxidase subunit 1" --output mollusc_cox1_proteins.fasta --files mollusca.gb --fasta-protein-features
python query.py --type CDS --qualifier product --terms "cytochrome oxidase subunit 2" --output mollusc_cox2_proteins.fasta --files mollusca.gb --fasta-protein-features
python query.py --type CDS --qualifier product --terms "cytochrome oxidase subunit 3" --output mollusc_cox3_proteins.fasta --files mollusca.gb --fasta-protein-features
```
This saves a bunch of time as for the real searches we only have to look at the prefiltered records. 

### Finding records that have a host identified

The **host** qualifier belongs to the **source** feature, so we'll search for that but not put in anything for `--terms` as we don't care what the host actually is:

`python query.py --type source --qualifier host  --dump-genbank --files *.seq --output with_host.gb`

of course, if we do care what the host qualifier is, we just add it as a term:

```
# find records belonging to parasites of humans
python query.py --type source --qualifier host --terms "Homo sapiens"  --dump-genbank --files *.seq --output human_host.gb
```

### finding records for first, second, third etc. exons 

Because we are just running a command line, we can wrap the call to `query.py` in a bash for loop:

```
for i in {1..10}; do python query.py --type exon --qualifier number --terms $i --files *.seq --fasta-features --output exon.$i.fasta; done
# now we have a bunch of files named exon.1.fasta, exon.2.fasta, etc. etc.
grep -c '>' exon.*.fasta
exon.10.fasta:118
exon.1.fasta:3401
exon.2.fasta:2998
exon.3.fasta:1873
exon.4.fasta:1286
exon.5.fasta:703
exon.6.fasta:524
exon.7.fasta:345
exon.8.fasta:235
exon.9.fasta:164
```

Now we go and look at the properties of sequences in different numbered exons......

## Extending localgb to do something different. 

To extend localgb, we write a function which takes a single record as a string and does something with it. Then we call `localgb.do_search_generic()` with the name of our function and a list of filenames. Here's the hello world example - we will use a regular expression to pull out the length of each record and add it to a total:

```import localgb
import sys
import re

length_regex = re.compile('source          1..(\d+)')

total_length = 0

def process_record(record):

    global total_length
    match = re.search(length_regex, record)
    if match:   # some source features are more complicated, ignore them
        total_length += int(match.group(1))

localgb.do_search_generic(process_record, filenames=sys.argv[1:])

print('counted {:,d} bases total\n\n'.format(total_length))
```

More complex examples will probably involve parsing the record into a `SeqIO` object using BioPython. Here's how we find all records that contain an EcoRI restriction site (`GAATTC`):

```
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
```


