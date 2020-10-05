import pkg_resources
import tempfile
import magic
import logging
import re

def read_fasta(sequence):
    entries = 0
    bases = []
    label = None
    for line in sequence:
        if line.startswith(">"):
            label = line
            entries += 1
        else:
            bases.append(line)
        if entries > 1:
            raise ValueError("FASTA file contains multiple entries")
            break
    return label, bases

def qc_fasta(sequence):
    schema_resource = pkg_resources.resource_stream(__name__, "validation/formats")
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(schema_resource.read())
        tmp.flush()
        val = magic.Magic(magic_file=tmp.name,
                          uncompress=False, mime=True)
    seq_type = val.from_buffer(sequence.read(4096)).lower()
    sequence.seek(0)
    if seq_type == "text/fasta":
        # ensure that contains only one entry
        submitlabel, submitseq = read_fasta(sequence)
        sequence.seek(0)
        return "sequence.fasta"
    elif seq_type == "text/fastq":
        return "reads.fastq"
    else:
        raise ValueError("Sequence file does not look like a DNA FASTA or FASTQ")
