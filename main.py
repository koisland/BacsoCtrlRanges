import os
import re
import cv2
import pprint
import datetime
import requests
import logging
import pdf2image
import pytesseract
from bs4 import BeautifulSoup

from config import Config

logging.basicConfig(filename="report.log", level=logging.INFO)


class eSCCReport(Config):

    def __init__(self, save_as_pdf=True):
        self.save_as_pdf = save_as_pdf

        self._clear_files()

    def _clear_files(self, time_interval=14):
        """
        Clear stored reports older than time interval.
        Called on cls init
        :param time_interval: time interval to save from current date in days
        :return: None
        """
        pass

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
        curr_date = datetime.datetime.strftime(datetime.datetime.now(), "%m_%d_%y")
        file_path = os.path.join(self.RES_PATH, f"original_report_{curr_date}.pdf")

        # return file path if already exists
        if os.path.exists(file_path):
            return file_path

        bs = BeautifulSoup(self.raw_content(self.URL), "html.parser")

        # all recent archived report under table elements with class inpagebtn
        all_report_elems = bs.find_all("td", {"class": "inpagebtn"})

        # loop through found elements and grab button links
        try:
            for report_elem in all_report_elems:
                # strong tag for categories of results on eurofins website
                elem_name_query = report_elem.a.find("strong")

                # check if something found and then if "somatic cells" in name
                if elem_name_query and "Somatic Cells" in elem_name_query:
                    recent_report_purl = report_elem.a.get("href")

                    # write bytes pdf to file
                    with open(file_path, "wb") as fobj:
                        fobj.write(self.raw_content(recent_report_url, content_type="content"))

                    return file_path

        except AttributeError as ex:
            logging.error("Eurofins site must have undergone design change. Element not found.")
            raise Exception(f"Page element not found on Eurofins site. {ex}")

    @property
    def recent_txt_report(self):
        # returns list of images from pdf so take first image
        img = pdf2image.convert_from_path(self.recent_pdf_report)[0]

        cv2.imwrite(os.path.join(self.RES_PATH, ""))

        # convert image to string
        img_str = pytesseract.image_to_string(img)

        if res := re.search(self.REGEX_PATTERN, img_str):
            logging.info("Text pattern found in pdf image.")

            data = dict(zip(["Set Number", "Date", "Low", "Low-Medium", "Medium-High", "High"],
                            res.groups()))
            report = self._fmt_report(img, data)
            return report
        else:
            raise Exception("Text not found.")

    def _fmt_report(self, img, data):
        return


def main():
    escc_report = eSCCReport(save_as_pdf=True)
    print(escc_report.recent_txt_report)


if __name__ == "__main__":
    main()
