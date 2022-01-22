import os
import boto3
from botocore.client import Config
import base64
from sccrpt import SCCReport

s3 = boto3.resource('s3')
client = boto3.client('s3')


def handler(event, _):
    # for cloudwatch log
    print(event)

    # default event.
    default = {"queryStringParameters": {"option": "rpt"}}
    params = event.get("queryStringParameters", default["queryStringParameters"])
    option = params.get("option", "rpt")

    bucket = s3.Bucket("esccrpt")

    rpt = SCCReport()

    if option == "rpt":
        path = rpt.report
    elif option == "opdf":
        path = rpt.recent_pdf_report
    elif option == "otxt":
        path = rpt.recent_txt_report
    else:
        path = rpt.report

    # get filename
    _, fname = os.path.split(path)

    # convert to bytes, send file content, and remove.
    with open(path, 'rb') as fobj:
        client.upload_fileobj(fobj, bucket.name, fname)

    # remove created files from tmp/___
    rpt.cleanup()

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
