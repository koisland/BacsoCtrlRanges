import os
import tempfile
import re
import numpy as np
from PIL import ImageFont


class Config:
    # save to temp dir
    OUT_PATH = tempfile.gettempdir()

    URL = "https://www.eurofinsus.com/food-testing/services/testing-services/dairy/calibration-standards-results/"
    ST_CATEGS_HTML_ELEM_ARGS = ("td", {"class": "inpagebtn"})

    URL_SET_REGEX = re.compile(r"escc-set(\d{6})")
    PDF_SET_REGEX = re.compile(r"(?<=Set:\s)(\d{6,7})")
    PDF_SET_DATE_REGEX = re.compile(r"(?<=Date:\s)(\d{2}/\d{2}/\d{2})")
    PDF_SET_VAL_REGEX = re.compile(r"(\d{3})\s(\d{3})\s(\d{3,4})\s(\d{3,4})")
    SET_REC_MSG = "Received:     /    /    \n\n" \
                  "By:                     \n\n" \
                  "TC:          °C         \n\n"

    DESC_LBL_FONT = ImageFont.truetype("Helvetica-Bold-Font.ttf", size=24)
    PCT_LBL_FONT = ImageFont.truetype("Helvetica-Bold-Font.ttf", size=30)

    DESC_LBL_X_Y = (825, 150)
    PCT_LBL_Y = 650
    # 1st array is distance between each label. 2nd array is adjustment by some num of pixels.
    PCT_LBL_X = np.cumsum(np.array([140] * 4) + np.array([0, 115, 120, 110]))
    LOW_PCT = 0.15
    OTHER_PCT = 0.10
