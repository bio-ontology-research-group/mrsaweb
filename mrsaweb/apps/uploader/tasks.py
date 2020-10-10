from celery import task
from uploader.models import Upload
import subprocess
import os
import json
import arvados
import urllib
import getpass
import socket
import logging
import yaml
import gzip

from .qc_fasta import qc_fasta
from .qc_metadata import qc_metadata, to_rdf
from django.conf import settings
from mrsaweb.virtuoso import insert

@task
def upload_to_arvados(upload_pk, sequence_read_1, sequence_read_2, metadata_file):
    logger = upload_to_arvados.get_logger()
    api = arvados.api(host=settings.ARVADOS_API_HOST, token=settings.ARVADOS_API_TOKEN)
    col = arvados.collection.Collection(api_client=api)
    
    metadata = yaml.load(open(metadata_file), Loader=yaml.FullLoader)
    qc_fasta(sequence_read_1)
    qc_fasta(sequence_read_2)

    upload_file(col, sequence_read_1, 'reads1.fastq.gz')
    upload_file(col, sequence_read_2, 'reads2.fastq.gz')
    upload_file(col, metadata_file, 'metadata.yaml')
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

    try:
        username = getpass.getuser()
    except KeyError:
        username = "unknown"

    properties = {
        "sequence_label": metadata['sample']['sample_id'],
        "upload_app": "mrsa-uploader",
        "upload_ip": external_ip,
        "upload_user": "%s@%s" % (username, socket.gethostname())
    }
    logger.info("%s uploaded by %s from %s", metadata['sample']['sample_id'], properties['upload_user'], properties['upload_ip'])
    result = col.save_new(owner_uuid=settings.UPLOAD_PROJECT, name="%s uploaded by %s from %s" %
                 (metadata['sample']['sample_id'], properties['upload_user'], properties['upload_ip']),
                 properties=properties, ensure_unique_name=True)
    response = col.api_response()
    update_upload_success(upload_pk, response['uuid'])
    update_rdfstore(response['uuid'], metadata_file)

    os.remove(sequence_read_1)
    os.remove(sequence_read_2)
    os.remove(metadata_file)


def update_upload_failed(upload_pk, error_message):
    Upload.objects.filter(pk=upload_pk).update(
        status=Upload.ERROR,
        error_message=error_message)

def update_upload_success(upload_pk, uuid):
    Upload.objects.filter(pk=upload_pk).update(
        status=Upload.UPLOADED, col_uuid=uuid)

def update_rdfstore(uuid, metadata_file):
    res_uri = settings.ARVADOS_COL_BASE_URI + uuid
    graph = to_rdf(res_uri, metadata_file)
    insert(graph)

def upload_file(col, filename_local, filename_remote):
    lf = open(filename_local, 'rb')
    with col.open(filename_remote, "wb") as f:
        r = lf.read(65536)
        while r:
            f.write(r)
            r = lf.read(65536)
    lf.close()
