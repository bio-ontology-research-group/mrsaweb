from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .utils import api
COLLECTIONS_URL = 'https://collections.cborg.cbrc.kaust.edu.sa'


class Upload(models.Model):

    SUBMITTED = "submitted"
    VALIDATED = "validated"
    ERROR = "error"
    UPLOADED = "uploaded"
    
    STATUSES = [
        (SUBMITTED, SUBMITTED),
        (VALIDATED, VALIDATED),
        (ERROR, ERROR),
        (UPLOADED, UPLOADED)
    ]
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL,
        related_name="uploads")
    date = models.DateTimeField(default=timezone.now)
    col_uuid = models.CharField(max_length=31, blank=True, null=True)
    status = models.CharField(
        max_length=15, default=SUBMITTED, choices=STATUSES)
    error_message = models.CharField(max_length=255, blank=True, null=True)

    @property
    def collection(self):
        if not self.col_uuid:
            return None
        if hasattr(self, '_col'):
            return self._col
        self._col = api.collections().get(uuid=self.col_uuid).execute()
        return self._col

    @property
    def name(self):
        if not self.collection:
            return None
        return self.collection['properties']['sequence_label']

    @property
    def sequence_read_1_link(self):
        if not self.collection:
            return None
        portable_data_hash = self.collection['portable_data_hash']
        return COLLECTIONS_URL + f'/c={portable_data_hash}/_/reads1.fastq.gz'

    
    @property
    def sequence_read_2_link(self):
        if not self.collection:
            return None
        portable_data_hash = self.collection['portable_data_hash']
        return COLLECTIONS_URL + f'/c={portable_data_hash}/_/reads2.fastq.gz'

    @property
    def metadata_link(self):
        if not self.collection:
            return None
        portable_data_hash = self.collection['portable_data_hash']
        return COLLECTIONS_URL + f'/c={portable_data_hash}/_/metadata.yaml'
