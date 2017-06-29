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
To run the script, I also have to give a `--output` to specify an output file and a `--files` to specify the genbank files (which will normally be `--files *.seq.gz` if I havent' extracted the files, or `--files *.seq` if I have).

Finally, I also have to specify what I want to do with the records/features that I find. So far there are three options:

- `--count-features` : just print out how many features matched the query
- `--fasta-features` : write the feature sequences out in FASTA format to the output file
- `--fasta-protein-features` : write the feature protein sequences out in FASTA format to the output file. This only works for features that have a `translation` qualifier, which AFAIK is only **CDS** features. 
- `--dump-genbank` : write out the records that contain matching features in genbank format to the output file. Of course, this file can then be the input file for a different query. 

TODO
- taxid stuff
more examples
type-only searching
taxonomic pre-filtering
