import os
import re
import io
import datetime
import requests

import fitz
import pdfplumber
import numpy as np
from PIL import ImageDraw, ImageFont, Image
from bs4 import BeautifulSoup

from config import Config


class SCCReport(Config):

    def __init__(self):
        self.set_number = None

        # declare dict to store paths
        self.paths = {}

        # create initial pdf so can be referenced in other functions
        init_pdf = self.recent_pdf_report

    def cleanup(self):
        """
        Cleanup generated intermediate files/output.
        :return: None
        """
        for _, path in self.paths.items():
            os.remove(path)

    @staticmethod
    def get_content(url, content_type="bytes"):
        """
        Make request to url and pull content
        :param url: (str) url to request
        :param content_type: (str) content types to get between bytes, text, url, or response obj
        :return: See above.
        """
        try:
            r = requests.get(url)
            r.raise_for_status()
            if content_type == "bytes":
                return r.content
            elif content_type == "text":
                return r.text
            elif content_type == "url":
                return r.url
            else:
                return r
        except requests.exceptions.RequestException as ex:
            raise Exception(f"Request error: {ex}")

    @property
    def curr_date(self):
        return datetime.datetime.strftime(datetime.datetime.now(), "%m_%d_%y")

    @property
    def recent_pdf_report(self):
        """
        Generate a pdf report of most recent SCC data.
        :return: File path to pdf
        """

        # return file path if already exists
        if "pdf" in self.paths:
            return self.paths["pdf"]

        bs = BeautifulSoup(self.get_content(self.URL), "html.parser")

        # all recent archived report under table elements with class inpagebtn
        all_report_elems = bs.find_all(self.ST_CATEGS_HTML_ELEM_ARGS)

        # loop through found elements and grab button links
        try:
            for report_elem in all_report_elems:
                # strong tag for categories of results on eurofins website
                elem_name_query = report_elem.a.find("strong")

                # check if something found and then if "somatic cells" in name
                if elem_name_query and "Somatic Cells" in elem_name_query:
                    recent_report_url = report_elem.a.get("href")

                    bytes_pdf = self.get_content(recent_report_url, content_type="bytes")

                    # get set number from url
                    if set_number := re.search(self.URL_SET_REGEX, recent_report_url):
                        self.set_number = set_number.groups()[0]

                        # declare pdf path with set number
                        pdf_path = os.path.join(self.OUT_PATH, f'orig_report_{self.set_number}.pdf')
                    else:
                        raise Exception("Could not parse set number from url.")

                    with open(pdf_path, "wb") as fobj:
                        fobj.write(bytes_pdf)

                        # add path
                        self.paths["pdf"] = pdf_path
                        return pdf_path

        except AttributeError as ex:
            raise Exception(f"Page element not found on Eurofins site. {ex}")

    @property
    def recent_txt_report(self):
        """
        Generates a text doc of most recent SCC data.
        :return: File path to text file AND text as dict
        """

        if "txt" in self.paths:
            return self.paths["txt"]

        text_path = os.path.join(self.OUT_PATH, f'report_{self.set_number}.txt')

        # convert image to string
        with pdfplumber.open(self.paths["pdf"]) as pdf:
            first_page = pdf.pages[0]
            pdf_text = first_page.extract_text()

            # search for vals and info
            set_info = re.search(self.PDF_SET_REGEX, pdf_text)
            set_vals = re.search(self.PDF_SET_VAL_REGEX, pdf_text)

            # convert values to int and get ranges
            pcts, _, bounds = self.gen_scc_ranges([int(val) for val in set_vals.groups()])

            if set_info and set_vals:
                data = dict(zip(["Set Number", "Date", "Low", "Low-Medium", "Medium-High", "High"],
                                set_info.groups() + set_vals.groups()))
                with open(text_path, "w") as fobj:
                    fobj.write(f"Set Number: {data.get('Set Number')}\n")
                    fobj.write(f"Date: {data.get('Date')}\n\n")
                    # write values and bounds
                    scc_vals = list(data.items())[2:]
                    for (k, v), pct, (lbound, ubound) in zip(scc_vals, pcts, bounds):
                        fobj.write(f"[{k}]\n"
                                   f"   SCC: {v}\n"
                                   f"   Range ({pct * 100}%): {lbound} - {ubound}\n")
            else:
                raise Exception("Text not found.")

        # add text path
        self.paths["txt"] = text_path
        return text_path, data

    @property
    def recent_img_report(self):
        """
        Convert pdf to image.
        :return: File path to img.
        """

        if "img" in self.paths:
            return self.paths["img"]

        img_path = os.path.join(self.OUT_PATH, f'orig_report_{self.set_number}.png')

        with fitz.open(self.paths["pdf"]) as pdf:
            # create matrix for pixmap and increase resolution
            mat = fitz.Matrix(2, 2)
            page = pdf.loadPage(0)
            pic = page.getPixmap(matrix=mat)
            pic.writePNG(img_path)

        self.paths["img"] = img_path
        return img_path

    def gen_scc_ranges(self, scc_vals):
        """
        Calculate ranges for scc values.
        :param scc_vals:
        :return:
        """
        scc_vals = np.array(scc_vals)
        pcts = np.array([self.LOW_PCT, *([self.OTHER_PCT] * 3)])
        if len(scc_vals) != len(pcts):
            raise Exception("Data and percents are not equal length.")
        pct_diff = np.round(np.multiply(scc_vals, pcts), 0)
        pct_diff = pct_diff.astype(int)
        lower_bounds = scc_vals - pct_diff
        upper_bounds = scc_vals + pct_diff
        bounds = zip(lower_bounds, upper_bounds)
        return pcts, pct_diff, list(bounds)

    @property
    def report(self):
        """
        Generates an annotated report with accepted ranges of counts for SCC standards.
        Data pulled from Eurofins website. (See config.py)
        :return: File path to report
        """

        img_path = self.recent_img_report
        txt_path, txt_data = self.recent_txt_report

        if "rpt" in self.paths:
            return self.path["rpt"]

        rpt_path = os.path.join(self.OUT_PATH, f"report_{self.set_number}.png")

        data = list(txt_data.values())[2:]

        # convert dict into list of scc values into np arr
        scc_vals = [int(scc) for scc in data]

        pct_lbl_font = ImageFont.truetype("Helvetica-Bold-Font.ttf", size=30)
        img = Image.open(img_path, "r")
        d = ImageDraw.Draw(img)

        pcts, pct_diff, bounds = self.gen_scc_ranges(scc_vals)

        # add received date/time/analyst line
        d.text(self.DESC_LBL_X_Y, self.SET_REC_MSG, fill=(0, 0, 0), font=pct_lbl_font)

        # draw scc values on pic
        for x, pct, diff, (scc_lower, scc_upper) in zip(self.PCT_LBL_X, pcts, pct_diff, bounds):
            pct_str = f"{pct * 100}%"
            diff_str = f"({diff})"
            range_str = f"{scc_lower} — {scc_upper}"

            d.text((x, self.PCT_LBL_Y), f"{pct_str} {diff_str}\n\n{range_str}",
                   fill=(0, 0, 0), font=pct_lbl_font)

        img.save(rpt_path, "PNG")

        self.paths["rpt"] = rpt_path
        return rpt_path
