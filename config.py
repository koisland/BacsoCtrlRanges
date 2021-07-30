import os
import numpy as np


class Config:
    URL = "https://www.eurofinsus.com/food-testing/services/testing-services/dairy/calibration-standards-results/"
    RES_PATH = os.path.join(os.path.dirname(__file__), "resources")
    OUT_PATH = os.path.join(os.path.dirname(__file__), "output")
    ST_CATEGS_HTML_ELEM_ARGS = ("td", {"class": "inpagebtn"})
    REGEX_PATTERN = r"Set:\s(\d{6})\sDate:\s(\d{2}/\d{2}/\d{2})\n(\d+)\s(\d+)\s(\d+)\s(\d+)\s"

    PCT_LBL_Y = 800
    # 1st array is distance between each label. 2nd array is adjustment by some num of pixels.
    PCT_LBL_X = np.cumsum(np.array([225] * 4) + np.array([0, 115, 120, 110]))
    LOW_PCT = 0.15
    OTHER_PCT = 0.10
