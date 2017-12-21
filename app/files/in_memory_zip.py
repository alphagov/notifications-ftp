from io import BytesIO
import zipfile


class InMemoryZip(object):
    def __init__(self):
        # Create the in-memory file-like object
        self.in_memory_zip = BytesIO()

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        with zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_STORED, False) as zf:
            # Write the file to the in-memory zip
            zf.writestr(filename_in_zip, file_contents)

            # Mark the files as having been created on Windows so that
            # Unix permissions are not inferred as 0000
            for zfile in zf.filelist:
                zfile.create_system = 0

        return self

    def read(self):
        '''Returns a string with the contents of the in-memory zip.'''
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()
