import os


class Config:
    URL = "https://www.eurofinsus.com/food-testing/services/testing-services/dairy/dqci-calibration-standards-archive/somatic-cells/"
    RES_PATH = os.path.join(os.path.dirname(__file__), "resources")
    HTML_ELEM_ARGS = ("div", {"id": "pagecontent"})
    REGEX_PATTERN = r"Set:\s(\d{6})\sDate:\s(\d{2}/\d{2}/\d{2})\n(\d+)\s(\d+)\s(\d+)\s(\d+)\s"
    LOW_PCT = 0.15
    OTHER_PCT = 0.10
