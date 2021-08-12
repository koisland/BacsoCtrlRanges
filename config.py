import os
import re
import numpy as np


class Config:
    URL = "https://www.eurofinsus.com/food-testing/services/testing-services/dairy/calibration-standards-results/"
    RES_PATH = os.path.join(os.path.dirname(__file__), "resources")
    OUT_PATH = os.path.join(os.path.dirname(__file__), "output")
    ST_CATEGS_HTML_ELEM_ARGS = ("td", {"class": "inpagebtn"})
    REGEX_PATTERN = re.compile(r"Set:\s+(\d{6})\s+Date:\s+(\d{2}/\d{2}/\d{2})\n"
                               r"\s+LOW\s+LOW/MED\s+MED/HI\s+HIGH\n"
                               r"\s+(\d{2,3})\s+(\d{2,3})\s+(\d{3,4})\s+(\d{3,4})")

    PCT_LBL_Y = 800
    # 1st array is distance between each label. 2nd array is adjustment by some num of pixels.
    PCT_LBL_X = np.cumsum(np.array([225] * 4) + np.array([0, 115, 120, 110]))
    LOW_PCT = 0.15
    OTHER_PCT = 0.10
