from asgiref.sync import sync_to_async
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from .utils import FORM_ITEMS
from uploader.models import Upload
from .qc_metadata import qc_metadata
from .qc_fasta import qc_fasta_lite
from django.forms import ValidationError
from .tasks import upload_to_arvados
import tempfile
import json
import datetime
import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

def add_clean_field(cls, field_name):
    def required_field(self):
        metadata_file = self.cleaned_data.get('metadata_file', None)
        value = self.cleaned_data[field_name]
        if metadata_file is not None:
            return value
        if not value:
            raise ValidationError("This field is required!")
        return value
    required_field.__doc__ = "Required field validator for %s" % field_name
    required_field.__name__ = "clean_%s" % field_name
    setattr(cls, required_field.__name__, required_field)

class UploadForm(forms.ModelForm):
    sequence_read_1 = forms.FileField(
        required=True,
        help_text='Gzipped FASTQ File (*.fastq.gz) read 1. Max file size is 512Mb.')
    sequence_read_2 = forms.FileField(
        required=True,
        help_text='Gzipped FASTQ File (*.fastq.gz) read 2. Max file size is 512Mb.')
    metadata_file = forms.FileField(
        required=False,
        help_text='Metadata file in JSON/YAML format. Metadata fields are not required if this file is provided.')

    class Meta:
        model = Upload
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UploadForm, self).__init__(*args, **kwargs)
        for item in FORM_ITEMS:
            if 'id' not in item:
                continue
            help_text = item.get('docstring', '')
            label = item['label']
            if item['required']:
                label += ' *'
            if item['type'] == 'text':
                if not item['list']:
                    self.fields[item['id']] = forms.CharField(
                        max_length=255, label=label,
                        help_text=help_text, required=False)
                else:
                    self.fields[item['id']] = SimpleArrayField(
                        forms.CharField(
                            max_length=255, required=False),
                        label=label, help_text=help_text, required=False)
            elif item['type'] == 'select':
                if not item['list']:
                    self.fields[item['id']] = forms.ChoiceField(
                        label=label, help_text=help_text, required=False,
                        choices=item['options'])
                else:
                    self.fields[item['id']] = SimpleArrayField(
                        forms.CharField(
                            max_length=255, required=False),
                        label=label, help_text=help_text, required=False,
                        widget=forms.Select(choices=item['options']))
            elif item['type'] == 'number':
                if not item['list']:
                    self.fields[item['id']] = forms.DecimalField(
                        label=label, help_text=help_text, required=False)
                else:
                    self.fields[item['id']] = SimpleArrayField(
                        forms.DecimalField(required=False),
                        label=label, help_text=help_text, required=False)
            elif item['type'] == 'date':
                if not item['list']:
                    self.fields[item['id']] = forms.DateField(
                        label=label, input_formats=['%m/%d/%Y',],
                        help_text=help_text, required=False)
                else:
                    self.fields[item['id']] = SimpleArrayField(
                        forms.DateField(
                            input_formats=['%m/%d/%Y',], required=False),
                        label=label, help_text=help_text, required=False)
            if item['required']:
                add_clean_field(UploadForm, item['id'])

    def metadata_id(self):
        return self['metadata.id']
    
    def file_fields(self):
        return [self['sequence_read_1'], self['sequence_read_2'], self['metadata_file']]

    def host_fields(self):
        for name in self.fields:
            if name.startswith('metadata.host'):
                yield self[name]

    def sample_fields(self):
        for name in self.fields:
            if name.startswith('metadata.sample'):
                yield self[name]
    
    def technology_fields(self):
        for name in self.fields:
            if name.startswith('metadata.technology'):
                yield self[name]

    def submitter_fields(self):
        for name in self.fields:
            if name.startswith('metadata.submitter'):
                yield self[name]

    def bacteria_fields(self):
        for name in self.fields:
            if name.startswith('metadata.bacteria'):
                yield self[name]

    def phenotypes_fields(self):
        for name in self.fields:
            if name.startswith('metadata.phenotypes'):
                yield self[name]

    def clean_metadata_file(self):
        metadata_file = self.cleaned_data['metadata_file']
        if metadata_file:
            if not qc_metadata(metadata_file.temporary_file_path()):
                raise ValidationError("Invalid metadata format")   
            
        return metadata_file

    def clean_sequence_read_1(self):
        sequence_read_1 = self.cleaned_data['sequence_read_1']
        try:
            qc_fasta_lite(sequence_read_1.temporary_file_path())
        except ValueError:
            raise ValidationError("Invalid file format")
        except OSError as e:
            raise ValidationError(e)
        return sequence_read_1

    def clean_sequence_read_2(self):
        sequence_read_2 = self.cleaned_data['sequence_read_2']
        try:
            qc_fasta_lite(sequence_read_2.temporary_file_path())
        except ValueError:
            raise ValidationError("Invalid file format")
        except OSError as e:
            raise ValidationError(e)
        return sequence_read_2

    def clean(self):
        if 'metadata_file' not in self.cleaned_data or ('metadata_file' in self.cleaned_data and not self.cleaned_data['metadata_file']):
            metadata = {}
            for key, val in self.cleaned_data.items():
                if not key.startswith('metadata') or not val:
                    continue
                if isinstance(val, datetime.date):
                    val = val.strftime('%Y-%m-%d')
                keys = key.split('.')
                if len(keys) == 2:
                    metadata[keys[1]] = val
                elif len(keys) == 3:
                    if keys[1] not in metadata:
                        metadata[keys[1]] = {}
                    metadata[keys[1]][keys[2]] = val
                #bind phenotypes properties
                elif len(keys) == 4:
                    if keys[1] not in metadata:
                        metadata[keys[1]] = {}
                    if keys[2] not in metadata[keys[1]]:
                        metadata[keys[1]][keys[2]] = [{}]
                    metadata[keys[1]][keys[2]][0][keys[3]] = val
            
            metadata_str = json.dumps(metadata)
            f = tempfile.NamedTemporaryFile('wt', delete=False)
            f.write(metadata_str)
            f.close()

            if not qc_metadata(f.name):
                os.remove(f.name)
                raise ValidationError("Invalid metadata format")
            self.cleaned_data['fields_metadata_file'] = f.name
        return self.cleaned_data
    

    def save_file(self, f):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        for chunk in f.chunks():
            tmp_file.write(chunk)
        tmp_file.close()
        return tmp_file.name        

    def save(self):
        self.instance = super(UploadForm, self).save(commit=False)
        self.instance.user = self.request.user
        if not self.instance.id:
            self.instance.save()
        sequence_read_1 = self.save_file(self.cleaned_data['sequence_read_1'])
        sequence_read_2 = self.save_file(self.cleaned_data['sequence_read_2'])
        metadata_file = self.cleaned_data['metadata_file']
        if metadata_file:
            metadata_file = self.save_file(metadata_file)
        else:
            metadata_file = self.cleaned_data['fields_metadata_file']
        
        upload_to_arvados.delay(
            self.instance.id, 
            sequence_read_1,
            sequence_read_2,
            metadata_file)
        return self.instance
