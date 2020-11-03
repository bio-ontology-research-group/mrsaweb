
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

from celery import task
from celery.schedules import crontab
from celery.task import periodic_task

from uploader.models import Upload

from .qc_fasta import qc_fasta
from .qc_metadata import qc_metadata, to_rdf
from .galaxy import clean_folder, upload
from django.conf import settings
from mrsaweb.virtuoso import insert

@task
def upload_to_arvados(upload_pk, sequence_read_1, sequence_read_2, metadata_file):
    try:
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
        graph = update_rdfstore(response['uuid'], metadata_file)
        upload_rdf_file(col,graph)
    except Exception as e:
        logger.exception("message")
        update_upload_failed(update_upload_failed, e)
    finally:
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
    return graph

def upload_file(col, filename_local, filename_remote):
    lf = open(filename_local, 'rb')
    with col.open(filename_remote, "wb") as f:
        r = lf.read(65536)
        while r:
            f.write(r)
            r = lf.read(65536)
    lf.close()

def upload_rdf_file(col, graph):
    with col.open('metadata.rdf', "wb") as f:
        f.write(graph.serialize(format="pretty-xml"))

    col.save()

# Every 12th hour
# @periodic_task(run_every=crontab(minute=0, hour='11,23'))
def run_pangenome_analysis():
    logger = run_pangenome_analysis.get_logger()
    cmd = 'mrsa-seq-analyzer'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, shell=True)
    for line in process.stdout:
        logger.info(line.strip())

# Every 3rd hour
@periodic_task(run_every=crontab(minute=0, hour='2,14'))
def sync_results2galaxy():
    logger = sync_results2galaxy.get_logger()
    clean_folder()
    folder_id=settings.GALAXY_PANGENOME_RESULT_DIR
    collection_url = settings.ARVADOS_COL_BASE_URI + "/" + settings.PANGENOME_RESULT_UUID

    core_full_aln_url = collection_url + "/" + 'core.full.aln'
    logger.info("uploading: %s", core_full_aln_url)
    upload(core_full_aln_url, folder_id)
    
    core_full_aln_iqtree_url = collection_url + "/" + 'core.full.aln.iqtree'
    logger.info("uploading: %s", core_full_aln_iqtree_url)
    upload(core_full_aln_iqtree_url, folder_id)
    
    core_full_aln_treefile = collection_url + "/" + 'core.full.aln.treefile'
    logger.info("uploading: %s", core_full_aln_treefile)
    upload(core_full_aln_treefile, folder_id)
    
    core_full_tab_url = collection_url + "/" + 'core.full.tab'
    logger.info("uploading: %s", core_full_tab_url)
    upload(core_full_tab_url, folder_id)
    
    core_url = collection_url + "/" + 'core.txt'
    logger.info("uploading: %s", core_url)
    upload(core_url, folder_id)
    
    cwl_output_url = collection_url + "/" + 'cwl.output.json'
    logger.info("uploading: %s", cwl_output_url)
    upload(cwl_output_url, folder_id)
    
    gene_presence_absence_url = collection_url + "/" + 'gene_presence_absence.svg'
    logger.info("uploading: %s", gene_presence_absence_url)
    upload(gene_presence_absence_url, folder_id)

    output_url = collection_url + "/" + 'output.json'
    logger.info("uploading: %s", output_url)
    upload(output_url, folder_id)

    pan_genome_reference_url = collection_url + "/" + 'pan_genome_reference.fa'
    logger.info("uploading: %s", pan_genome_reference_url)
    upload(pan_genome_reference_url, folder_id)

    seqwish_gfa_url = collection_url + "/" + 'seqwish.gfa'
    logger.info("uploading: %s", seqwish_gfa_url)
    upload(seqwish_gfa_url, folder_id)

    seqwish_url = collection_url + "/" + 'seqwish.png'
    logger.info("uploading: %s", seqwish_url)
    upload(seqwish_url, folder_id)

    summary_statistics_url = collection_url + "/" + 'summary_statistics.txt'
    logger.info("uploading: %s", summary_statistics_url)
    upload(summary_statistics_url, folder_id)

    logger.info('Finished syncing pangenomic analysis results to galaxy server')