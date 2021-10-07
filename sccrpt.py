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
    def original_fname(self):
        return os.path.join(self.OUT_PATH, f"original_report")

    @property
    def recent_pdf_report(self):
        """
        Generate a pdf report of most recent SCC data.
        :return: File path to pdf
        """
        pdf_path = f"{self.original_fname}.pdf"

        # return file path if already exists
        if os.path.exists(pdf_path):
            return pdf_path

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

                    with open(pdf_path, "wb") as fobj:
                        fobj.write(bytes_pdf)
                        return pdf_path

        except AttributeError as ex:
            raise Exception(f"Page element not found on Eurofins site. {ex}")

    @property
    def recent_txt_report(self):
        """
        Generates a text doc of most recent SCC data.
        :return: File path to text file AND text as dict
        """
        file_path = f"{self.original_fname}.txt"

        pdf_src = self.recent_pdf_report

        # convert image to string
        with pdfplumber.open(pdf_src) as pdf:
            first_page = pdf.pages[0]
            pdf_text = first_page.extract_text()

            # search for vals and info
            set_info = re.search(self.SET_REGEX_PATTERN, pdf_text)
            set_vals = re.search(self.SET_VAL_REGEX_PATTERN, pdf_text)

            if set_info and set_vals:
                data = dict(zip(["Set Number", "Date", "Low", "Low-Medium", "Medium-High", "High"],
                                set_info.groups() + set_vals.groups()))
                with open(file_path, "w") as fobj:
                    for k, v in data.items():
                        fobj.write(f"{k}: {v}\n")
            else:
                raise Exception("Text not found.")

        if not self.SAVE_RES:
            os.remove(pdf_src)

        return file_path, data

    @property
    def recent_img_report(self):
        """
        Convert pdf to image.
        :return: File path to img.
        """
        img_path = f"{self.original_fname}.png"
        if os.path.exists(img_path):
            return img_path

        pdf_path = self.recent_pdf_report
        with fitz.open(pdf_path) as pdf:
            # create matrix for pixmap and increase resolution
            mat = fitz.Matrix(2, 2)
            page = pdf.loadPage(0)
            pic = page.getPixmap(matrix=mat)
            pic.writePNG(img_path)

        # remove if not saving resources
        if not self.SAVE_RES:
            os.remove(pdf_path)

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
        return pcts, pct_diff, lower_bounds, upper_bounds

    @property
    def report(self):
        """
        Generates an annotated report with accepted ranges of counts for SCC standards.
        Data pulled from Eurofins website. (See config.py)
        :return: File path to report
        """
        rpt_path = os.path.join(self.OUT_PATH, f"report.png")
        if os.path.exists(rpt_path):
            return rpt_path

        img_path = self.recent_img_report
        txt_path, txt_data = self.recent_txt_report

        data = list(txt_data.values())[2:]

        # convert dict into list of scc values into np arr
        scc_vals = [int(scc) for scc in data]

        pct_lbl_font = ImageFont.truetype("Helvetica-Bold-Font.ttf", size=30)
        img = Image.open(img_path, "r")
        d = ImageDraw.Draw(img)

        pcts, pct_diff, lower_bounds, upper_bounds = self.gen_scc_ranges(scc_vals)

        # add received date/time/analyst line
        d.text(self.DESC_LBL_X_Y, self.SET_REC_MSG, fill=(0, 0, 0), font=pct_lbl_font)

        # draw scc values on pic
        for x, pct, diff, scc_lower, scc_upper in zip(self.PCT_LBL_X, pcts, pct_diff, lower_bounds, upper_bounds):
            pct_str = f"{pct * 100}%"
            diff_str = f"({diff})"
            range_str = f"{scc_lower} — {scc_upper}"

            d.text((x, self.PCT_LBL_Y), f"{pct_str} {diff_str}\n\n{range_str}",
                   fill=(0, 0, 0), font=pct_lbl_font)

        img.save(rpt_path, "PNG")

        if not self.SAVE_RES:
            os.remove(txt_path)
            os.remove(img_path)

        return rpt_path




