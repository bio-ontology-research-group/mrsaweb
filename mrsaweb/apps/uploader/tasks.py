from celery import Celery
from uploader.models import Upload
import subprocess
import os
import json

app = Celery('uploader', broker='amqp://guest@localhost//')

@app.task
def upload_to_arvados(upload_pk, sequence_file, metadata_file):
    cmd = ['bh20-seq-uploader', sequence_file, metadata_file]
    print(" ".join(cmd))
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_message=str(result.stderr.decode('utf-8'))
        Upload.objects.filter(pk=upload_pk).update(
            status=Upload.ERROR,
            error_message=error_message)
    else:
        col = str(result.stdout.decode('utf-8')).splitlines()
        col = json.loads(col[-1])
        Upload.objects.filter(pk=upload_pk).update(
            status=Upload.UPLOADED, col_uuid=col['uuid'])
        
    os.remove(sequence_file)
    os.remove(metadata_file)
