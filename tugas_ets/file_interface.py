import os
import json
import base64
from glob import glob
import uuid
import tempfile


class FileInterface:
    def __init__(self):
        os.chdir('files/')
        self.temp_uploads = {}  # Store temporary upload information

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def upload_start(self, params=[]):
        try:
            if len(params) < 2:
                return dict(status='ERROR', data='filename and filesize required')
            
            filename = params[0]
            filesize = int(params[1])
            
            # Create a unique upload ID
            upload_id = str(uuid.uuid4())
            
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            
            self.temp_uploads[upload_id] = {
                'filename': filename,
                'temp_path': temp_file.name,
                'filesize': filesize,
                'chunks_received': set()
            }
            
            return dict(status='OK', upload_id=upload_id)
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def upload_chunk(self, params=[]):
        try:
            if len(params) < 3:
                return dict(status='ERROR', data='upload_id, chunk_number and chunk_data required')
            
            upload_id = params[0]
            chunk_number = int(params[1])
            chunk_data = params[2]
            
            if upload_id not in self.temp_uploads:
                return dict(status='ERROR', data='invalid upload_id')
            
            upload_info = self.temp_uploads[upload_id]
            
            # Check if chunk already received
            if chunk_number in upload_info['chunks_received']:
                return dict(status='OK', data='chunk already received')
            
            # Write chunk to temporary file
            with open(upload_info['temp_path'], 'ab') as f:
                f.write(base64.b64decode(chunk_data))
            
            upload_info['chunks_received'].add(chunk_number)
            
            return dict(status='OK', data='chunk received')
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def upload_finish(self, params=[]):
        try:
            if len(params) < 1:
                return dict(status='ERROR',data='upload_id required')
            
            upload_id = params[0]
            
            if upload_id not in self.temp_uploads:
                return dict(status='ERROR',data='invalid upload_id')
            
            upload_info = self.temp_uploads[upload_id]
            
            # Copy the file instead of moving it
            try:
                with open(upload_info['temp_path'], 'rb') as src, open(upload_info['filename'], 'wb') as dst:
                    dst.write(src.read())
                # After successful copy, remove the temporary file
                os.unlink(upload_info['temp_path'])
            except Exception as e:
                return dict(status='ERROR', data=f'Failed to copy file: {str(e)}')
            
            # Clean up
            del self.temp_uploads[upload_id]
            
            return dict(status='OK', data=f'{upload_info["filename"]} uploaded')
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        try:
            filename = params[0]
            if os.path.exists(filename):
                os.remove(filename)
                return dict(status='OK', data=f'{filename} deleted')
            else:
                return dict(status='ERROR', data='file not found')
        except Exception as e:
            return dict(status='ERROR', data=str(e))


if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))