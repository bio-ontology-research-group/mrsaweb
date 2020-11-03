
import urllib
import os
import logging

from bioblend.galaxy import GalaxyInstance

from django.conf import settings

logger = logging.getLogger(__name__)
gi = GalaxyInstance(settings.GALAXY_API_BASEURL, key=settings.GALAXY_API_KEY)

tmpdir = '/tmp'

def upload(file_url, base_folder_id):
    try:
        filename = file_url.rsplit('/', 1)[1]
        f = urllib.request.urlopen(file_url)
        tmpfile = os.path.join(tmpdir, filename)
        with open(tmpfile, 'wb+') as tmp:
            tmp.write(f.read())

        result = gi.libraries.upload_file_from_local_path(settings.LIBRARY_ID, tmpfile, folder_id=base_folder_id)
        logger.info('uploaded: %s', str(result))
        return result
    except Exception as e:
        logger.exception("message")
        raise Exception(e)
    finally: 
        os.remove(tmpfile)

def create_folder(name):
    result = gi.libraries.create_folder(settings.LIBRARY_ID, name)
    logger.info('folder created: %s', result[0]['id'])
    return result[0]['id']


def clean_folder():
    response = gi.folders.show_folder(settings.GALAXY_PANGENOME_RESULT_DIR, contents=True)
    for item in response['folder_contents']:
        gi.libraries.delete_library_dataset(settings.LIBRARY_ID, item['id'], purged=True)