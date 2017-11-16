from django.core.management.base import BaseCommand
from opensubmit.models import SubmissionFile

class Command(BaseCommand):
    help = 'Refreshes all MD5 checksums for uploaded files'
    def handle(self, *args, **options):
        print("Scanning existing file uploads ...")
        files = SubmissionFile.valid_ones.all()
        for f in files:
            print("Updating checksum for %s ..."%(str(f)))
            try:
                f.md5 = f.attachment_md5()
                f.save()
            except IOError as e:
                print("Failed: "+str(e))

