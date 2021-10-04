import os
import base64
from sccrpt import SCCReport


def handler(event, context):
    option = event.get("option")
    rpt = SCCReport()
    if option == "rpt":
        path = rpt.report
        content_type = "image/png"
    elif option == "opdf":
        path = rpt.recent_pdf_report
        content_type = "application/pdf"
    else:
        path = rpt.recent_txt_report[0]
        content_type = "text/plain"

    if rpt.BYTES_ONLY:
        # convert to bytes, send file content, and remove.
        with open(path, 'rb') as fobj:
            file_content = base64.b64encode(fobj.read())

        os.remove(path)

        return {
            'isBase64Encoded': True,
            'statusCode': 200,
            'headers': {'Content-Type': content_type},
            'body': file_content.decode("utf-8")
        }
