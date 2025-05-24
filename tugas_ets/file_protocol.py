import json
import logging
import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""



class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    def proses_string(self,string_datamasuk=''):
        try:
            # Split only the command part (first three parts) to avoid issues with base64 data
            parts = string_datamasuk.split(maxsplit=3)
            c_request = parts[0].lower().strip()
            
            # For upload_chunk, handle the parameters differently
            if c_request == "upload_chunk":
                if len(parts) != 4:
                    return json.dumps(dict(status='ERROR',data='invalid upload chunk format'))
                params = [parts[1], parts[2], parts[3]]  # upload_id, chunk_number, chunk_data
            else:
                # For other commands, use shlex to properly handle quoted strings
                params = shlex.split(string_datamasuk)[1:]
                
            cl = getattr(self.file,c_request)(params)
            return json.dumps(cl)
        except Exception as e:
            return json.dumps(dict(status='ERROR',data='request tidak dikenali'))

if __name__=='__main__':
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))