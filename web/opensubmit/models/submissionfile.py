from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse

from django.conf import settings

import zipfile, tarfile, unicodedata, os, hashlib

import logging
logger = logging.getLogger('OpenSubmit')

def upload_path(instance, filename):
    '''
        Sanitize the user-provided file name, add timestamp for uniqness.
    '''

    filename = filename.replace(" ", "_")
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').lower()
    return os.path.join(str(timezone.now().date().isoformat()), filename)

class ValidSubmissionFileManager(models.Manager):
    '''
        A model manager used by SubmissionFile. It returns only submission files
        that were not replaced, for submission that were not withdrawn.
    '''
    def get_queryset(self):
        from .submission import Submission
        return super(ValidSubmissionFileManager, self).get_queryset().filter(replaced_by=None).exclude(submissions__state=Submission.WITHDRAWN)

class SubmissionFile(models.Model):
    '''
        A file attachment for a student submission. File attachments may be replaced
        by the student, but we keep the original version for some NSA-style data gathering.
        The "fetched" field defines the time stamp when the file was fetched for
        checking by some executor. On result retrieval, this timestamp is emptied
        again, which allows to find 'stucked' executor jobs on the server side.
        The "md5" field keeps a checksum of the file upload, for duplicate detection.
    '''

    attachment = models.FileField(upload_to=upload_path, verbose_name="File upload")
    fetched = models.DateTimeField(editable=False, null=True)
    replaced_by = models.ForeignKey('SubmissionFile', null=True, blank=True, editable=False)
    md5 = models.CharField(max_length=36, null=True, blank=True, editable=False)

    class Meta:
        app_label = 'opensubmit'

    def __unicode__(self):
        return unicode(self.attachment.name)

    def attachment_md5(self):
        '''
            Calculate the checksum of the file upload.
            For binary files (e.g. PDFs), the MD5 of the file itself is used.

            Archives are unpacked and the MD5 is generated from the sanitized textfiles
            in the archive. This is done with some smartness:
            - Whitespace and tabs are removed before comparison.
            - For MD5, ordering is important, so we compute it on the sorted list of
              file hashes.
        '''
        MAX_MD5_FILE_SIZE = 10000
        md5_set = []

        def md5_add_text(text):
            try:
                text=unicode(text, errors='ignore')
                text=text.replace(' ','').replace('\n','').replace('\t','')
                md5_set.append(hashlib.md5(text).hexdigest())
            except:
                # not unicode decodable
                pass

        def md5_add_file(f):
            try:
                md5 = hashlib.md5()
                for chunk in f.chunks():
                    md5.update(chunk)
                md5_set.append(md5.hexdigest())
            except:
                pass

        try:
            if zipfile.is_zipfile(self.attachment.path):
                zf = zipfile.ZipFile(self.attachment.path, 'r')
                for zipinfo in zf.infolist():
                    if zipinfo.file_size < MAX_MD5_FILE_SIZE:
                        md5_add_text(zf.read(zipinfo))
            elif tarfile.is_tarfile(self.attachment.path):
                tf = tarfile.open(self.attachment.path,'r')
                for tarinfo in tf.getmembers():
                    if tarinfo.isfile():
                        if tarinfo.size < MAX_MD5_FILE_SIZE:
                            md5_add_text(tf.extractfile(tarinfo).read())
            else:
                md5_add_file(self.attachment)
        except Exception as e:
            logger.warning("Exception on archive MD5 computation, using file checksum: "+str(e))

        result=hashlib.md5(str(sorted(md5_set))).hexdigest()
        return result

    def basename(self):
        return self.attachment.name[self.attachment.name.rfind('/') + 1:]

    def get_absolute_url(self):
        # To realize access protection for student files, we implement our own download method here.
        # This implies that the Apache media serving (MEDIA_URL) is disabled.
        assert(len(self.submissions.all()) > 0)
        return reverse('download', args=(self.submissions.all()[0].pk, 'attachment'))

    def get_preview_url(self):
        return reverse('preview', args=(self.submissions.all()[0].pk,))

    def absolute_path(self):
        return settings.MEDIA_ROOT + "/" + self.attachment.name

    def is_executed(self):
        return self.fetched is not None

    def is_archive(self):
        '''
            Determines if the attachment is an archive.
        '''
        try:
            if zipfile.is_zipfile(self.attachment.path) or tarfile.is_tarfile(self.attachment.path):
                return True
        except:
            pass
        return False

    def archive_previews(self):
        '''
            Return preview on archive file content as dictionary.
            In order to avoid browser and web server trashing by the students, there is a size limit for the single files shown.
        '''
        MAX_PREVIEW_SIZE = 1000000

        def sanitize(text):
            try:
                return unicode(text, errors='ignore')
            except:
                return unicode("(unreadable text data)")

        result = []
        if zipfile.is_zipfile(self.attachment.path):
            zf = zipfile.ZipFile(self.attachment.path, 'r')
            for zipinfo in zf.infolist():
                if zipinfo.file_size < MAX_PREVIEW_SIZE:
                    result.append({'name': zipinfo.filename, 'preview': sanitize(zf.read(zipinfo))})
                else:
                    result.append({'name': zipinfo.filename, 'preview': '(maximum size exceeded)'})
        elif tarfile.is_tarfile(self.attachment.path):
            tf = tarfile.open(self.attachment.path,'r')
            for tarinfo in tf.getmembers():
                if tarinfo.isfile():
                    if tarinfo.size < MAX_PREVIEW_SIZE:
                        result.append({'name': tarinfo.name, 'preview': sanitize(tf.extractfile(tarinfo).read())})
                    else:
                        result.append({'name': tarinfo.name, 'preview': '(maximum size exceeded)'})
        else:
            # single file
            f=open(self.attachment.path)
            fname = f.name[f.name.rfind(os.sep)+1:]
            result = [{'name': fname, 'preview': sanitize(f.read())},]
        return result

    def test_result_dict(self):
        '''
            Create a compact data structure representation of all result
            types for this file.

            Returns a dictionary where the keys are the result types, and
            the values are dicts of all the other result information.
        '''
        list_of_dicts=self.test_results.all().values()
        return {entry['kind']: {'result':entry['result']} for entry in list_of_dicts}

    objects = models.Manager()
    valid_ones = ValidSubmissionFileManager()

