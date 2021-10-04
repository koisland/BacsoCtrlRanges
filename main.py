import os
import argparse
from sccrpt import SCCReport


def main():
    ap = argparse.ArgumentParser(description="Generate a SCC controls report from Eurofins website.")
    # allow only one or the other
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("-op", "--og_pdf", action="store_true", help="Generate original pdf.")
    group.add_argument("-ot", "--og_txt", action="store_true", help="Generate text document with original pdf values.")
    group.add_argument("-r", "--report", action="store_true", help="Generate annotated report.")

    rpt = SCCReport()
    args = vars(ap.parse_args())
    if args["report"]:
        path = rpt.report
    elif args["og_pdf"]:
        path = rpt.recent_pdf_report
    elif args["og_txt"]:
        path = rpt.recent_txt_report[0]
    else:
        return
    print(path)
