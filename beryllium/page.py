# -*- coding:utf-8 -*-
from beryllium.field import FieldList
from beryllium.tabsetup import TabSetup
from beryllium.listcssselector import ListCssSelector
from beryllium.mongodb import Mongodb


class Page(object):
    def __init__(self, field_list: FieldList, name="", is_save=False, mongodb=Mongodb(),
                 list_css_selector=ListCssSelector(), tab_setup=TabSetup(), x_offset=0, y_offset=0):
        """

        :param field_list:
        :param name:
        :param is_save:
        :param mongodb:
        :param list_css_selector:
        :param tab_setup:
        :param x_offset:这个参数在移动端页面的时候使用，在调用driver.move_to_element方法的时候使用
        :param y_offset:和上面x_offset的作用一样
        """
        self.field_list = field_list
        self.name = name
        self.is_save = is_save
        self.mongodb = mongodb
        self.list_css_selector = list_css_selector
        self.tab_setup = tab_setup
        self.x_offset = x_offset
        self.y_offset = y_offset

    def __str__(self):
        if not self.name or self.field_list is None:
            return str(None)
        else:
            result = {"name": self.name, "is_save": self.is_save}
            if self.field_list is not None:
                result.setdefault("field_list", str(self.field_list))
            if self.is_save:
                result.setdefault("mongodb", str(self.mongodb))
            if self.list_css_selector is not None:
                result.setdefault('list_css_selector', str(self.list_css_selector))
            if self.tab_setup is not None:
                result.setdefault("tab_setup", str(self.tab_setup))
            result.setdefault("x_offset", self.x_offset)
            result.setdefault("y_offset", self.y_offset)
            return str(result).replace("\\", "")

    def __eq__(self, other):
        if other is None:
            return not self.name or self.field_list is None
        else:
            if vars(other) == vars(self):
                return True
            else:
                super.__eq__(self, other)

    def __iter__(self):
        return self

    def set_field_list(self, field_list):
        self.field_list = field_list


class PageGroup(object):
    def __init__(self, *args: Page):
        self.iter = iter(args)
        self.tuple = args

    def __iter__(self):
        return self

    def __next__(self):
        for i in self.iter:
            return i

    def __str__(self):
        return "(%s)" % ",".join([str(i) for i in self.tuple])

    def __eq__(self, other):
        if other is None or other == []:
            return not self
        else:
            super.__eq__(self, other)


class PageFunc(object):
    def __init__(self, func=None, **kwargs):
        self.func = func
        self.kwargs = kwargs

    def set_kwargs(self, **kwargs):
        self.kwargs = kwargs

    def run(self):
        if self.func:
            self.func(**self.kwargs)
        else:
            print("func为空!!!")


class NextPageCssSelectorSetup(object):
    def __init__(self, css_selector: str, page: Page, stop_css_selector="", ele_timeout=1, pause_time=1, is_next=True,
                 is_proxy=True, pre_page_func=PageFunc(), main_page_func=PageFunc(), after_page_func=PageFunc()):
        """

        :param css_selector:
        :param page:
        :param stop_css_selector:
        :param ele_timeout:
        :param pause_time:
        :param is_next:
        :param is_proxy:
        :param pre_page_func:
        :param main_page_func:
        :param after_page_func:
        """
        self.css_selector = css_selector
        self.stop_css_selector = stop_css_selector
        self.ele_timeout = ele_timeout
        self.pause_time = pause_time
        self.is_next = is_next
        self.is_proxy = is_proxy
        self.page = page
        self.pre_page_func = pre_page_func
        self.main_page_func = main_page_func
        self.after_page_func = after_page_func

    def set_main_page_func(self, page_func: PageFunc):
        self.main_page_func = page_func

    # def __str__(self):
    #     if not self.css_selector:
    #         return str(None)
    #     else:
    #         return str(vars(self))
    #
    # def __eq__(self, other):
    #     if other is None:
    #         return not self.css_selector
    #     else:
    #         if vars(other) == vars(self):
    #             return True
    #         else:
    #             super.__eq__(self, other)


class NextPageLinkTextSetup(object):
    def __init__(self, link_text: str, page: Page, ele_timeout=1, pause_time=1, is_next=True, is_proxy=True,
                 pre_page_func=PageFunc(), main_page_func=PageFunc(), after_page_func=PageFunc()):
        """

        :param link_text:
        :param page:
        :param ele_timeout:
        :param pause_time:
        :param is_next:
        :param is_proxy:
        :param pre_page_func:
        :param main_page_func:
        :param after_page_func:
        """
        self.link_text = link_text
        self.ele_timeout = ele_timeout
        self.pause_time = pause_time
        self.is_next = is_next
        self.is_proxy = is_proxy
        self.page = page
        self.pre_page_func = pre_page_func
        self.main_page_func = main_page_func
        self.after_page_func = after_page_func

    def set_main_page_func(self, page_func: PageFunc):
        self.main_page_func = page_func
