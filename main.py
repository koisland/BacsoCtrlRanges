import os
import re
import numpy as np
import datetime
import requests
import logging
import pdf2image
import pytesseract
from PIL import ImageDraw, ImageFont
from bs4 import BeautifulSoup

from config import Config

logging.basicConfig(filename="report.log", level=logging.INFO)


class SCCReport(Config):
    def __init__(self, save_res=False):
        """
        :param save_res: (bool) Save resources used to make report in resources folder.
        """
        self.save_res = save_res

    @staticmethod
    def raw_content(url, content_type="bytes"):
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
            logging.error(f"Request error: {ex}")

    @property
    def curr_date(self):
        return datetime.datetime.strftime(datetime.datetime.now(), "%m_%d_%y")

    @property
    def recent_pdf_report(self):
        """
        Generate a pdf report of most recent SCC data.
        :return: File path to pdf
        """
        pdf_path = os.path.join(self.RES_PATH, f"original_report_{self.curr_date}.pdf")

        # return file path if already exists
        if os.path.exists(pdf_path):
            return pdf_path

        bs = BeautifulSoup(self.raw_content(self.URL), "html.parser")

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

                    # write bytes pdf to file
                    with open(pdf_path, "wb") as fobj:
                        fobj.write(self.raw_content(recent_report_url, content_type="bytes"))

                    return pdf_path

        except AttributeError as ex:
            logging.error("Eurofins site must have undergone design change. Element not found.")
            raise Exception(f"Page element not found on Eurofins site. {ex}")

    @property
    def recent_img_report(self):
        """
        Generates an image report of most recent SCC data.
        :return: File path to image AND PIL image obj
        """
        pdf_path = self.recent_pdf_report
        # returns list of images from pdf so take first image
        img = pdf2image.convert_from_path(pdf_path)[0]

        img_path = os.path.join(self.RES_PATH, f"original_report_{self.curr_date}.png")
        img.save(img_path, "PNG")

        if not self.save_res:
            os.remove(pdf_path)

        return img_path, img

    @property
    def recent_txt_report(self):
        """
        Generates a text doc of most recent SCC data.
        :return: File path to text file AND text as dict
        """
        file_path = os.path.join(self.RES_PATH, f"original_report_{self.curr_date}.txt")

        img_path, img = self.recent_img_report

        # convert image to string
        img_str = pytesseract.image_to_string(img)

        if res := re.search(self.REGEX_PATTERN, img_str):
            data = dict(zip(["Set Number", "Date", "Low", "Low-Medium", "Medium-High", "High"],
                            res.groups()))
            with open(file_path, "w") as fobj:
                for k, v in data.items():
                    fobj.write(f"{k}: {v}\n")

            return file_path, data
        else:
            raise Exception("Text not found.")

    @property
    def report(self):
        """
        Generates an annotated report with accepted ranges of counts for SCC standards.
        Data pulled from Eurofins website. (See config.py)
        :return: File path to report
        """
        rpt_path = os.path.join(self.OUT_PATH, f"report_{self.curr_date}.png")
        if os.path.exists(rpt_path):
            return rpt_path

        img_path, img = self.recent_img_report
        txt_path, txt_data = self.recent_txt_report
        data = list(txt_data.values())[2:]

        # convert dict into list of scc values into np arr
        try:
            cvt_scc = [int(scc) for scc in data]
        except ValueError:
            logging.error("Pytesseract output incorrect value.")
            raise Exception("Pytesseract error.")

        pct_lbl_font = ImageFont.truetype(os.path.join(self.RES_PATH, "Helvetica-Bold-Font.ttf"), size=45)
        d = ImageDraw.Draw(img)

        data = np.array(cvt_scc)
        pcts = np.array([self.LOW_PCT, *([self.OTHER_PCT] * 3)])
        pct_diff = np.round(np.multiply(data, pcts), 0)
        pct_diff = pct_diff.astype(int)
        lower_bound = data - pct_diff
        upper_bound = data + pct_diff

        for x, pct, diff, scc_lower, scc_upper in zip(self.PCT_LBL_X, pcts, pct_diff, lower_bound, upper_bound):
            pct_str = f"{pct * 100}%"
            diff_str = f"({diff})"
            range_str = f"{scc_lower} — {scc_upper}"

            d.text((x, self.PCT_LBL_Y + 50), f"{pct_str} {diff_str}\n\n{range_str}",
                   fill=(0, 0, 0), font=pct_lbl_font)

        logging.info("Report successfully created.")
        img.save(rpt_path, "PNG")

        if not self.save_res:
            os.remove(txt_path)
            os.remove(img_path)

        return rpt_path


def main():
    escc_standards = SCCReport(save_res=False)

    print(escc_standards.recent_pdf_report)
    print(escc_standards.recent_img_report[0])
    print(escc_standards.recent_txt_report[0])

    # print(escc_standards.report)


if __name__ == "__main__":
    main()
