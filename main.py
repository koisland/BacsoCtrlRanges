import os
import re
import datetime
import requests
import logging
import pdf2image
import pytesseract
from bs4 import BeautifulSoup
from config import Config

logging.basicConfig(filename="report.log", level=logging.INFO)


class eSCCReport(Config):

    @staticmethod
    def raw_content(url, content_type="content"):
        try:
            r = requests.get(url)
            r.raise_for_status()
            if content_type == "content":
                return r.content
            elif content_type == "text":
                return r.text
            else:
                return r
        except requests.exceptions.RequestException as ex:
            logging.error(f"Request error: {ex}")

    @property
    def recent_pdf_report(self):
        bs = BeautifulSoup(self.raw_content(self.URL), "html.parser")

        # all archived report under div - pagecontent id
        all_reports = bs.find("div", {"id": "pagecontsent"})

        # find returns first item matching query. take link from <a> tag
        try:
            first_report_url = all_reports.find("li").a['href']
        except AttributeError as ex:
            logging.error("Eurofins site must have undergone design change. Element not found.")
            raise Exception(f"Page element not found on Eurofins site. {ex}")

        # get pdf as bytes
        first_report_pdf = self.raw_content(first_report_url, content_type="content")

    def cvt_report(self):
        # returns list of images from pdf so take first image
        img = pdf2image.convert_from_bytes(self.recent_pdf_report)[0]

        # convert image to string
        img_str = pytesseract.image_to_string(img)

        if res := re.search(self.REGEX_PATTERN, img_str):
            logging.info("Text pattern found in pdf image.")

            return dict(zip(["Set Number", "Date", "Low", "Low-Medium", "Medium-High", "High"],
                            res.groups()))
        else:
            raise Exception("Text not found.")

    def fmt_report(self):
        pass


escc_report = eSCCReport()
print(escc_report.recent_pdf_report)
# print(res)
