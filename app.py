import os
import boto3
from botocore.client import Config
import base64
from sccrpt import SCCReport

s3 = boto3.resource('s3')
client = boto3.client('s3')


def handler(event, context):
    option = event.get("option")
    bucket = s3.Bucket("esccrpt")

    rpt = SCCReport()

    if option == "rpt":
        path = rpt.report
    elif option == "opdf":
        path = rpt.recent_pdf_report
    else:
        path = rpt.recent_txt_report[0]

    # get filename
    _, fname = os.path.split(path)

    if rpt.BYTES_ONLY:
        # convert to bytes, send file content, and remove.
        with open(path, 'rb') as fobj:
            client.upload_fileobj(fobj, bucket.name, fname)

        # remove file from tmp/___
        os.remove(path)

        # generate presigned url for temp access to s3 file.
        url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket.name,
                'Key': fname
            },
            ExpiresIn=604800  # 7 days
        )

        # redirect url
        return {
            'statusCode': 302,
            'headers': {
                'Location': url
            }
        }
