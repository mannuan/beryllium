# Beryllium Package

This is beryllium package. You can use [beryllium](https://github.com/mannuan/beryllium/) to write your lean.

## Beryllium Demo
```python
# -*- coding: utf-8 -*-

from beryllium import Beryllium
import time
from beryllium import FieldList, Field, FieldName, Page, ListCssSelector, Mongodb, NextPageCssSelectorSetup, PageFunc
bery = Beryllium()
bery.driver = bery.get_driver()
bery.fast_get_page("https://www.baidu.com")
time.sleep(1)
bery.until_send_text_by_css_selector(css_selector="#kw", text="杭州")
bery.until_send_enter_by_css_selector(css_selector="#kw")
time.sleep(2)

fieldlist_shop = FieldList(
    Field(field_name=FieldName.SHOP_NAME, css_selector="h3"),
)
page_shop = Page(name="shop_page",
                 field_list=fieldlist_shop,
                 list_css_selector=ListCssSelector(list_css_selector="#content_left > div.result.c-container"))

bery.until_click_no_next_page_by_css_selector(
    next_page_setup=NextPageCssSelectorSetup(
        page=page_shop,
        css_selector="#page > a.n",
        main_page_func=PageFunc(func=bery.from_page_get_data_list, page=page_shop)
    )
)
```

## Demonstration

<img src="https://mannuan.github.io/images/IMG_0813.GIF">


## Outlook
Committed to creating an interactive crawler library. I hope programmers with the same desire to join my development. You can contact me by email: wujunleiwang@gmail.com
