'''
Helper functions for the view implementations.
'''

import io
import zipfile

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView
from django.http import FileResponse, HttpResponse


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    '''
    Ensures that the user is logged in and has backend rights.
    '''
    def test_func(self):
        return self.request.user.is_staff


class BinaryDownloadMixin(object):
    f = None
    fname = None

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        assert(self.f is not None)
        assert(self.fname is not None)
        response = HttpResponse(self.f, content_type='application/binary')
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.fname
        return response


class ZipDownloadDetailView(DetailView):
    '''
    Specialized DetailView base class for ZIP downloads.

    Only intended as base class.
    '''
    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        output = io.BytesIO()
        z = zipfile.ZipFile(output, 'w')
        file_name = self.fill_zip_file(z)
        z.close()
        # go back to start in ZIP file so that Django can deliver it
        output.seek(0)
        response = FileResponse(
            output, content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename=%s.zip' % file_name
        return response

    def fill_zip_file(self, z):
        '''
        Function that fills the given ZIP file instance with data.
        To be implemented by derived class.

        Parameters:
            z:  ZIP file instance

        Returns:   File name for the download
        '''
        raise NotImplementedError
