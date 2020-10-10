import pkg_resources
import tempfile
import magic
import logging
import re
import gzip

from Bio import SeqIO

def qc_fasta(sequence):
    with gzip.open(sequence, 'rt') as f:
        for record in SeqIO.parse(f, 'fastq'):
            pass
    return True

def qc_fasta_lite(sequence):
    with gzip.open(sequence, 'rt') as f:
        f.read(1)
