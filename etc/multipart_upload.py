#http://boto.readthedocs.org/en/latest/s3_tut.html#storing-large-data
import math, os, sys
import boto
from filechunkio import FileChunkIO



# Connect to S3
ak = os.environ.get('AWS_ACCESS_KEY',None)
sk = os.environ.get('AWS_SECRET_KEY',None)
c = boto.connect_s3(aws_access_key_id=ak,aws_secret_access_key=sk)
b = c.get_bucket('adsabs-solrindex')

# Get file info
try:
  source_path = sys.argv[1]
except IndexError:
  sys.exit('Usage: multipart_upload.py PATH')
  
source_size = os.stat(source_path).st_size

# Create a multipart upload request
mp = b.initiate_multipart_upload(os.path.basename(source_path))

# Use a chunk size of 50 MiB (feel free to change this)
chunk_size = 52428800*2
chunk_count = int(math.ceil(source_size / chunk_size))

# Send the file parts, using FileChunkIO to create a file-like object
# that points to a certain byte range within the original file. We
# set bytes to never exceed the original file size.
for i in range(chunk_count + 1):
  offset = chunk_size * i
  print float(offset)/source_size
  bytes = min(chunk_size, source_size - offset)
  with FileChunkIO(source_path, 'r', offset=offset,bytes=bytes) as fp:
    mp.upload_part_from_file(fp, part_num=i + 1)

# Finish the upload
mp.complete_upload()
