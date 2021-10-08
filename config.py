import os
import tempfile
import re
import numpy as np


class Config:
    # save to temp dir
    OUT_PATH = tempfile.gettempdir()

    URL = "https://www.eurofinsus.com/food-testing/services/testing-services/dairy/calibration-standards-results/"
    ST_CATEGS_HTML_ELEM_ARGS = ("td", {"class": "inpagebtn"})

    URL_SET_REGEX = re.compile("escc-set(\d{6})")
    PDF_SET_REGEX = re.compile("Set:\s(\d{6,7})\sDate:\s(\d{2}/\d{2}/\d{2})\n")
    PDF_SET_VAL_REGEX = re.compile("LOW LOW/MED MED/HI HIGH\n(\d{3})\s(\d{3})\s(\d{3,4})\s(\d{3,4})")
    SET_REC_MSG = "Received:     /    /    \n\n" \
                  "By:                     \n\n" \
                  "TC:          °C         \n\n"

    DESC_LBL_X_Y = (800, 50)
    PCT_LBL_Y = 650
    # 1st array is distance between each label. 2nd array is adjustment by some num of pixels.
    PCT_LBL_X = np.cumsum(np.array([140] * 4) + np.array([0, 115, 120, 110]))
    LOW_PCT = 0.15
    OTHER_PCT = 0.10
