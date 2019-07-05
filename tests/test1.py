# -*- coding: utf-8 -*-

from beryllium import Beryllium, FieldList
import time
from selenium.webdriver.common.touch_actions import TouchActions


if __name__ == "__main__":
    with Beryllium(is_open_devtools=True, is_mobile=True) as bery:
        bery.fast_get_page("https://m.tb.cn/h.38Dj85B")
        # bery.until_send_text_by_css_selector(text="携程", css_selector="#kw")
        # bery.until_send_enter_by_css_selector(css_selector="#kw")
        # bery.until_scroll_to_center_click_by_first_partial_link_text(link_text="携程")
        # bery.until_scroll_to_center_click_by_first_partial_link_text(link_text="门票")
        bery.driver.refresh()
        time.sleep(1000)
