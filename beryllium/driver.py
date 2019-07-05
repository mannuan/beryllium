# -*- coding:utf-8 -*-
import warnings
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from pyvirtualdisplay import Display
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import traceback
import inspect
from selenium.webdriver.common.keys import Keys
import time
from beryllium.logger import get_logger
from beryllium.page import Page, PageFunc, NextPageCssSelectorSetup, NextPageLinkTextSetup
from beryllium.listcssselector import ListCssSelector
from beryllium.field import Field, FieldName, FieldType, FieldList
from beryllium.mongodb import Mongodb
import re
import json
import sys
from selenium.webdriver.support.ui import Select
from pymongo.collection import Collection
import os


class Beryllium(object):
    desktop_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                         "Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393"
    mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 " \
                        "(KHTML, like Gecko) Version/9.0 Mobile/13C75 Safari/601.1"
    curr_user_agent = desktop_user_agent

    scroll_to_center_js_script = "window.scrollBy(arguments[0].getClientRects()[0].x + arguments[0].clientWidth / 2" \
                                 " - window.innerWidth / 2, arguments[0].getClientRects()[0].y" \
                                 " + arguments[0].clientHeight / 2 - window.innerHeight / 2)"
    # 验证页面标题
    verify_page_title_list = ["验证"]

    def __init__(self, is_save_logs=False, log_file_name="00000000", is_mobile=False, is_virtual_display=False,
                 is_headless=False, is_load_images=False, is_open_devtools=False, is_proxy=False,
                 initial_proxy_ip="127.0.0.1"):
        """

        :param is_save_logs:是否保存日志
        :param log_file_name:日志文件名称
        :param is_mobile:是否是移动端
        :param is_virtual_display:是否隐藏窗口
        :param is_headless:是否隐藏窗口
        :param is_load_images:是否加载图片
        :param is_open_devtools:是否打开开发者工具
        :param is_proxy:是否代理
        :param initial_proxy_ip:初始的代理ip
        """
        self.is_save_logs = is_save_logs
        self.log_file_name = log_file_name
        self.is_mobile = is_mobile
        self.is_virtual_display = is_virtual_display
        self.is_headless = is_headless
        self.is_load_images = is_load_images
        self.is_open_devtools = is_open_devtools
        self.is_proxy = is_proxy
        self.initial_proxy_ip = initial_proxy_ip  # 用户设定的初始化ip
        self.data_key = {}  # 保存到数据的关键标识字段
        self.pre_proxy_ip = initial_proxy_ip  # 之前的代理ip，这个ip是实时变化的，不用设置
        self.logger = get_logger(self.log_file_name, self.is_save_logs)
        self.driver = None

    def set_initial_proxy_ip(self, ip):
        """

        :param ip:初始化ip
        :return:
        """
        self.initial_proxy_ip = ip

    def set_data_key(self, data_key: dict):
        """

        :param data_key:{str:value, str:value}
        :return:
        """
        self.data_key = data_key

    def start(self):
        print("Start driver")
        self.driver = self.get_driver()

    def __del__(self):
        """
        析构函数
        :return:
        """
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        """
        with
        :return:
        """
        print("Start driver")
        self.driver = self.get_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        print("Stop driver")
        self.driver.quit()

    @staticmethod
    def get_curr_ip():
        """
        获取当前ip
        :return:
        """
        return re.findall(r"[\d]{1,3}.[\d]{1,3}.[\d]{1,3}.[\d]{1,3}",
                          os.popen("tsocks wget -q -O - http://pv.sohu.com/cityjson | awk '{print $5}'").read())[0]

    def get_curr_proxy_ip(self):
        """
        获得当前代理ip
        :return:
        """
        while True:
            try:
                proxy_ip = re.findall(r"[\d]{1,3}.[\d]{1,3}.[\d]{1,3}.[\d]{1,3}", os.popen(
                    "tsocks wget -q -O - http://pv.sohu.com/cityjson | awk '{print $5}'").read())[0]
                return proxy_ip
            except Exception as e:
                self.error_log(e=e)
                self.info_log(data="获取proxy_ip出错!!!")
            self.debug_log(data="暂停2秒....")
            time.sleep(2)

    def is_verify_page(self):
        self.switch_window_by_index(index=-1)
        return True in [i in self.driver.title for i in self.verify_page_title_list]

    def get_options(self):
        options = webdriver.ChromeOptions()
        prefs = {}
        if self.is_mobile:
            options.add_argument(
                "user-agent=%s" % self.mobile_user_agent)
            self.curr_user_agent = self.mobile_user_agent
            # mobile_emulation = {
            #     "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
            #     "userAgent": self.mobile_user_agent}
            # mobile_emulation = {"deviceName": "Galaxy S5"}
            # options.add_experimental_option("mobileEmulation", mobile_emulation)
            mobile_emulation = {"deviceName": "Nexus 5"}

            options.add_experimental_option("mobileEmulation", mobile_emulation)
        else:
            options.add_argument(
                "user-agent=%s" % self.desktop_user_agent)
            self.curr_user_agent = self.desktop_user_agent
        options.add_argument("lang=zh_CN.UTF-8")
        if self.is_virtual_display:
            print("Virtual display is running")
            display = Display(visible=0, size=(1440, 900))
            display.start()
        if self.is_virtual_display is False and self.is_headless is True:
            print("Headless is running")
            options.add_argument("--headless")
        if not self.is_load_images:
            print("Load images is false")
            # 1允许所有图片；2阻止所有图片；3阻止第三方服务器图片
            prefs.setdefault("profile.managed_default_content_settings.images", 2)
        prefs.setdefault("profile.default_content_setting.notifications", 2)  # 禁用消息通知
        prefs.setdefault("profile.default_content_setting.geolocation", 2)  # 禁用地理位置
        # options.add_argument('start-maximized')  # 使得页面在窗口里面达到最大
        options.add_argument("disable-infobars")  # 隐藏自动化软件测试的提示
        options.add_argument("--disable-notifications")  # 禁止页面通知
        options.add_argument("--disk-cache=true")  # 允许页面缓存,来加快页面的加载速度
        if self.is_open_devtools:  # 打开开发者工具
            options.add_argument("auto-open-devtools-for-tabs")
        options.add_experimental_option("prefs", prefs)
        # options.add_experimental_option("mobileEmulation", {"deviceName": "Nexus 5"})
        return options

    def get_driver(self):
        """
        获得驱动
        :return:
        """
        driver = webdriver.Chrome(chrome_options=self.get_options())
        driver.set_page_load_timeout(30)
        return driver

    @staticmethod
    def __get_running_func__(level=2):
        """

        :param level:
        :return:
        """
        inspect_stack = inspect.stack()
        if len(inspect_stack) < 2:
            pass
        elif len(inspect_stack) < level:
            inspect_stack = inspect_stack[:-2][::-1]
        elif len(inspect_stack) > level:
            inspect_stack = inspect.stack()[-level - 2:-2][::-1]
        return " - ".join("%s.%s.[%s]" % (i[1].split("/")[-1].split(".")[0], i[3], i[2]) for i in inspect_stack)

    def error_log(self, e: Exception, name="", istraceback=True, level=2):
        """

        :param name:
        :param e:
        :param istraceback:
        :param level:
        :return:
        """
        traceback_e = ""
        if istraceback:
            traceback_e = traceback.format_exc()
        self.logger.error("%s %s: %s\n%s" % (self.__get_running_func__(level=level), name, traceback_e, str(e)))

    def warning_log(self, e: Exception, name="", level=2):
        """

        :param name:
        :param e:
        :param level:
        :return:
        """
        self.logger.warning("%s %s: %s" % (self.__get_running_func__(level=level), name, str(e)))

    def info_log(self, data: str, name="", level=2):
        """

        :param name:
        :param data:
        :param level:
        :return:
        """
        self.logger.info("%s %s: %s" % (self.__get_running_func__(level=level), name, data))

    def debug_log(self, data: str, name="", level=2):
        """

        :param name:
        :param data:
        :param level:
        :return:
        """
        self.logger.debug("%s %s: %s" % (self.__get_running_func__(level=level), name, data))

    def new_window(self, url: str):
        """
        新建一个标签页
        :param url:
        :return:
        """
        self.driver.execute_script("window.open(\"{}\");".format(url))

    def random_vertical_scroll_to(self, min_offset=1000, max_offset=5000):
        """
        随机下拉滚动加载
        :param min_offset:
        :param max_offset:
        :return:
        """
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight + %s)" % random.randint(min_offset, max_offset))

    def vertical_scroll_to(self, offset=0):
        """
        下拉滚动加载, offset为0默认把页面下拉到最下端
        :param offset:
        :return:
        """
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight + %s)" % offset)

    def until_scroll_to_center_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        把页面元素滚动到页面中间
        :param css_selector:
        :param ele:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        try:
            self.driver.execute_script(
                self.scroll_to_center_js_script, self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=css_selector, timeout=timeout))
        except Exception:
            pass

    def until_scroll_to_center_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        把页面元素滚动到页面中间
        :param link_text:匹配的文字
        :param ele:WebElement对象
        :param timeout:超时时间
        :return:
        """
        if not ele:
            ele = self.driver
        try:
            self.driver.execute_script(
                self.scroll_to_center_js_script, self.until_presence_of_element_located_by_partial_link_text(
                    ele=ele, link_text=link_text, timeout=timeout))
        except Exception:
            pass

    def until_scroll_to_center_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        把页面元素滚动到页面中间
        :param link_text:匹配的文字
        :param ele:WebElement对象
        :param timeout:超时时间
        :return:
        """
        if not ele:
            ele = self.driver
        try:
            self.driver.execute_script(
                self.scroll_to_center_js_script, self.until_presence_of_element_located_by_link_text(
                    ele=ele, link_text=link_text, timeout=timeout))
        except Exception:
            pass

    def scroll_to_center(self, ele: WebElement):
        """
        把页面元素滚动到页面中间
        :param ele:
        :return:
        """
        try:
            self.driver.execute_script(self.scroll_to_center_js_script, ele)
        except Exception:
            pass

    def vertical_scroll_by(self, offset=100):
        """
        页面默认向下滚动100
        :param offset:
        :return:
        """
        self.driver.execute_script("window.scrollBy(0,%s)" % offset)

    def scroll_into_view(self, ele: WebElement):
        """
        将页面滚动到元素所在位置
        Deprecated use scroll_element_to_center
        :param ele:
        :return:
        """
        warnings.warn("use scroll_element_to_center instead", DeprecationWarning)
        self.driver.execute_script("arguments[0].scrollIntoView(false);", ele)

    def focus_on_element(self, ele: WebElement):
        """
        将页面滚动到元素所在位置
        Deprecated use scroll_element_to_center
        :param ele:
        :return:
        """
        warnings.warn("use scroll_element_to_center instead", DeprecationWarning)
        self.driver.execute_script("arguments[0].focus();", ele)

    def focus_on_element_by_css_selector(self, css_selector: str):
        """
        通过css_selector，将页面滚动到元素所在位置
        Deprecated until_scroll_element_to_center_by_css_selector
        :param css_selector:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_css_selector instead", DeprecationWarning)
        ele = self.until_presence_of_element_located_by_css_selector(css_selector=css_selector)
        self.driver.execute_script("arguments[0].focus();", ele)

    def focus_on_element_by_partial_link_text(self, link_text: str):
        """
        通过部分匹配文字，将页面滚动到元素所在位置
        Deprecated until_scroll_element_to_center_by_partial_link_text
        :param link_text:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_partial_link_text instead", DeprecationWarning)
        ele = self.until_presence_of_element_located_by_partial_link_text(link_text=link_text)
        self.driver.execute_script("arguments[0].focus();", ele)

    def until_scroll_into_view_by_css_selector(self, css_selector: str, ele=None):
        """
        通过css_selector将页面移动到元素所在位置
        Deprecated until_scroll_element_to_center_by_css_selector
        :param ele:WebElement
        :param css_selector:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_css_selector instead", DeprecationWarning)
        if not ele:
            ele = self.driver
        ele = self.until_presence_of_element_located_by_css_selector(ele=ele, css_selector=css_selector)
        self.driver.execute_script("arguments[0].scrollIntoView(false);", ele)

    def until_scroll_into_view_by_partial_link_text(self, link_text: str, ele=None):
        """
        通过部分匹配文字将页面移动到元素所在位置
        Deprecated until_scroll_element_to_center_by_partial_link_text
        :param ele:WebElement
        :param link_text:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_partial_link_text instead", DeprecationWarning)
        if not ele:
            ele = self.driver
        ele = self.until_presence_of_element_located_by_partial_link_text(ele=ele, link_text=link_text)
        self.driver.execute_script("arguments[0].scrollIntoView(false);", ele)

    def until_scroll_into_view_by_link_text(self, link_text: str, ele=None):
        """
        通过匹配文字将页面移动到元素所在位置
        Deprecated until_scroll_element_to_center_by_link_text
        :param ele:
        :param link_text:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_link_text instead", DeprecationWarning)
        if not ele:
            ele = self.driver
        ele = self.until_presence_of_element_located_by_link_text(ele=ele, link_text=link_text)
        self.driver.execute_script("arguments[0].scrollIntoView(false);", ele)

    def until_move_to_element_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        通过css_selector将页面移动到元素所在位置
        Deprecated until_scroll_element_to_center_by_css_selector
        :param ele:WebElement
        :param css_selector:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        ActionChains(self.driver).move_to_element(
            self.until_presence_of_element_located_by_css_selector(
                ele=ele, css_selector=css_selector, timeout=timeout)).perform()

    def until_move_to_element_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过部分匹配文字将页面移动到元素所在位置
        Deprecated until_scroll_element_to_center_by_partial_link_text
        :param ele:WebElement
        :param link_text:
        :param timeout:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_partial_link_text instead", DeprecationWarning)
        if not ele:
            ele = self.driver
        ActionChains(self.driver).move_to_element(
            self.until_presence_of_element_located_by_partial_link_text(
                ele=ele, link_text=link_text, timeout=timeout)).perform()

    def until_move_to_element_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过匹配文字将页面移动到元素所在位置
        Deprecated until_scroll_element_to_center_by_link_text
        :param ele:WebElement
        :param link_text:
        :param timeout:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_link_text instead", DeprecationWarning)
        if not ele:
            ele = self.driver
        ActionChains(self.driver).move_to_element(
            self.until_presence_of_element_located_by_link_text(
                ele=ele, link_text=link_text, timeout=timeout)).perform()

    def move_to_element(self, ele=None, x_offset=0, y_offset=0):
        """
        将页面移动到元素所在位置
        Deprecated scroll_element_to_center but if you are in mobile, the method is encouraged
        这个方法由于在移动端使用到，所以被保留
        :param ele:WebElement
        :param x_offset:
        :param y_offset:
        :return:
        """
        # warnings.warn("use scroll_element_to_center instead while you are in desktop", DeprecationWarning)
        if not ele:
            raise ValueError
        ActionChains(self.driver).move_to_element(ele).move_by_offset(xoffset=x_offset, yoffset=y_offset).perform()

    def until_scroll_to_center_click_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        通过css_selector将元素滚动找页面中间，并点击
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :param timeout:超时时间
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).click()

    def until_scroll_to_center_click_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过部分匹配文字将元素滚动找页面中间，并点击
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_presence_of_element_located_by_partial_link_text(
            ele=ele, link_text=link_text, timeout=timeout).click()

    def until_scroll_to_center_click_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过匹配文字将元素滚动找页面中间，并点击
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_presence_of_element_located_by_link_text(
            ele=ele, link_text=link_text, timeout=timeout).click()

    def until_scroll_to_center_click_by_first_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        通过第一个css_selector将元素滚动找页面中间，并点击
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        ele = self.until_presence_of_all_elements_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout)[0]
        self.scroll_to_center(ele=ele)
        ele.click()

    def until_scroll_to_center_click_by_first_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过第一个部分匹配文字将元素滚动找页面中间，并点击
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        ele = self.until_presence_of_all_elements_located_by_partial_link_text(
            ele=ele, link_text=link_text, timeout=timeout)[0]
        self.scroll_to_center(ele=ele)
        ele.click()

    def until_scroll_to_center_click_by_first_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过第一个匹配文字将元素滚动找页面中间，并点击
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        ele = self.until_presence_of_all_elements_located_by_link_text(ele=ele, link_text=link_text, timeout=timeout)[0]
        self.scroll_to_center(ele=ele)
        ele.click()

    def until_scroll_to_center_click(self, ele: WebElement):
        """
        将元素滚动找页面中间，并点击
        :param ele:WebElement
        :return:
        """
        self.scroll_to_center(ele=ele)  # 元素居中
        ele.click()

    def until_scroll_to_center_send_enter_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        通过css_selector将元素滚动找页面中间，并回车
        :param ele:WebElement对象
        :param css_selector:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_css_selector(ele=ele, css_selector=css_selector, timeout=timeout)
        self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).send_keys(Keys.ENTER)

    def until_send_enter_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        通过css_selector将元素滚动找页面中间，并回车
        :param ele:WebElement
        :param css_selector:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).send_keys(Keys.ENTER)

    def until_scroll_to_center_send_enter_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过匹配文字将元素滚动找页面中间，并回车
        :param ele:WebElement
        :param link_text:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_link_text(ele=ele, link_text=link_text, timeout=timeout)
        self.until_presence_of_element_located_by_link_text(
            ele=ele, link_text=link_text, timeout=timeout).send_keys(Keys.ENTER)

    def until_send_enter_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过匹配文字对元素回车
        :param ele:WebElement
        :param link_text:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_presence_of_element_located_by_link_text(
            ele=ele, link_text=link_text, timeout=timeout).send_keys(Keys.ENTER)

    def until_scroll_to_center_send_enter_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过部分匹配文字将元素滚动找页面中间，并回车
        :param ele:WebElement
        :param link_text:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_partial_link_text(ele=ele, link_text=link_text, timeout=timeout)
        self.until_presence_of_element_located_by_partial_link_text(
            ele=ele, link_text=link_text, timeout=timeout).send_keys(Keys.ENTER)

    def until_send_enter_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        通过匹配文字对元素回车
        :param ele:WebElement
        :param link_text:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_presence_of_element_located_by_partial_link_text(
            ele=ele, link_text=link_text, timeout=timeout).send_keys(Keys.ENTER)

    def until_scroll_to_center_send_text_by_css_selector(self, text: str, css_selector: str, ele=None, timeout=10):
        """
        通过css_selector将元素滚动找页面中间，并发送文字
        :param ele:WebElement
        :param css_selector:
        :param text:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_css_selector(ele=ele, css_selector=css_selector, timeout=timeout)
        self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).clear()
        self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).send_keys(text)

    def until_send_text_by_css_selector(self, text: str, css_selector: str, ele=None, timeout=10):
        """
        通过css_selector对元素发送文字
        :param ele:WebElement
        :param css_selector:
        :param text:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).clear()
        self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout).send_keys(text)

    def until_get_elements_len_by_css_selector(self, css_selector: str, ele=None, timeout=1):
        """
        通过css_selector将元素的数量
        :param ele:WebElement
        :param css_selector:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        return len(self.until_presence_of_all_elements_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout))

    def until_send_key_arrow_down_by_css_selector(
            self, css_selector: str, ele=None, min_frequency=100, max_frequency=300, timeout=1):
        """
        通过css_selector对元素发送向下的命令
        :param ele:WebElement
        :param css_selector:
        :param min_frequency:
        :param max_frequency:
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        for i in range(random.randint(min_frequency, max_frequency)):
            ActionChains(self.driver).move_to_element(
                self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=css_selector, timeout=timeout)).send_keys(Keys.ARROW_DOWN).perform()

    def until_send_key_arrow_down_by_partial_link_text(self, link_text: str, ele=None, frequency=100):
        """
        通过部分匹配文字对元素发送向下的命令
        :param ele:WebElement
        :param link_text:
        :param frequency:
        :return:
        """
        if not ele:
            ele = self.driver
        for i in range(frequency):
            ActionChains(self.driver).move_to_element(
                self.until_presence_of_element_located_by_partial_link_text(
                    ele=ele, link_text=link_text)).send_keys(Keys.ARROW_DOWN).perform()

    def until_send_key_arrow_down_by_link_text(self, link_text: str, ele=None, frequency=100):
        """
        通过匹配文字对元素发送向下的命令
        :param ele:WebElement
        :param link_text:
        :param frequency:
        :return:
        """
        if not ele:
            ele = self.driver
        for i in range(frequency):
            ActionChains(self.driver).move_to_element(
                self.until_presence_of_element_located_by_link_text(
                    ele=ele, link_text=link_text)).send_keys(Keys.ARROW_DOWN).perform()

    def until_title_is(self, title: str, ele=None, timeout=10):
        """
        判断title,返回布尔值
        :param ele:WebElement
        :param timeout:
        :param title:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.title_is(title))

    def until_title_contains(self, title: str, ele=None, timeout=10):
        """
        判断title，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param title:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.title_contains(title))

    def until_presence_of_element_located_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_element_located((By.ID, _id)))

    def until_presence_of_element_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))

    def until_scroll_to_center_presence_of_element_located_by_css_selector(
            self, css_selector: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_css_selector(ele=ele, css_selector=css_selector, timeout=timeout)  # 元素居中
        return self.until_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector, timeout=timeout)

    def until_presence_of_element_located_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_element_located((By.LINK_TEXT, link_text)))

    def until_scroll_to_center_presence_of_element_located_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_link_text(ele=ele, link_text=link_text, timeout=timeout)
        return self.until_presence_of_element_located_by_link_text(ele=ele, link_text=link_text, timeout=timeout)

    def until_presence_of_element_located_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, link_text)))

    def until_scroll_to_center_presence_of_element_located_by_partial_link_text(
            self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素是否被加到了dom树里，并不代表该元素一定可见，如果定位到就返回WebElement
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        self.until_scroll_to_center_by_partial_link_text(ele=ele, link_text=link_text, timeout=timeout)
        return self.until_presence_of_element_located_by_partial_link_text(
            ele=ele, link_text=link_text, timeout=timeout)

    def until_visibility_of_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断元素是否可见，如果可见就返回这个元素
        :param _id:
        :param ele:WebElement
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.visibility_of((By.ID, _id)))

    def until_visibility_of_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断元素是否可见，如果可见就返回这个元素
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.visibility_of((By.CSS_SELECTOR, css_selector)))

    def until_visibility_of_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断元素是否可见，如果可见就返回这个元素
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.visibility_of((By.LINK_TEXT, link_text)))

    def until_visibility_of_by_partial_link_text(self, partial_link_text: str, ele=None, timeout=10):
        """
        判断元素是否可见，如果可见就返回这个元素
        :param ele:WebElement
        :param timeout:
        :param partial_link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.visibility_of((By.PARTIAL_LINK_TEXT, partial_link_text)))

    def until_presence_of_all_elements_located_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断是否至少有1个元素存在于dom树中，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.ID, _id)))

    def until_presence_of_all_elements_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断是否至少有1个元素存在于dom树中，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))

    def until_presence_of_all_elements_located_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断是否至少有1个元素存在于dom树中，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.LINK_TEXT, link_text)))

    def until_presence_of_all_elements_located_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断是否至少有1个元素存在于dom树中，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.PARTIAL_LINK_TEXT, link_text)))

    def until_visibility_of_any_elements_located_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断是否至少有一个元素在页面中可见，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.ID, _id)))

    def until_visibility_of_any_elements_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断是否至少有一个元素在页面中可见，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))

    def until_visibility_of_any_elements_located_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断是否至少有一个元素在页面中可见，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.LINK_TEXT, link_text)))

    def until_visibility_of_any_elements_located_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断是否至少有一个元素在页面中可见，如果定位到就返回列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.PARTIAL_LINK_TEXT, link_text)))

    def until_text_to_be_present_in_element_located_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断指定的元素中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.ID, _id)))

    def until_text_to_be_present_in_element_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断指定的元素中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))

    def until_text_to_be_present_in_element_located_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断指定的元素中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.LINK_TEXT, link_text)))

    def until_text_to_be_present_in_element_located_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断指定的元素中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.presence_of_all_elements_located((By.PARTIAL_LINK_TEXT, link_text)))

    def until_text_to_be_present_in_element_value_by_id(self, _id: str, text: str, ele=None, timeout=10):
        """
        判断指定元素的属性值中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param _id:
        :param text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.text_to_be_present_in_element_value((By.ID, _id), text))

    def until_text_to_be_present_in_element_value_by_css_selector(
            self, css_selector: str, text: str, ele=None, timeout=10):
        """
        判断指定元素的属性值中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :param text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.text_to_be_present_in_element_value((By.CSS_SELECTOR, css_selector), text))

    def until_text_to_be_present_in_element_value_by_link_text(self, link_text: str, text: str, ele=None, timeout=10):
        """
        判断指定元素的属性值中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :param text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.text_to_be_present_in_element_value((By.LINK_TEXT, link_text), text))

    def until_text_to_be_present_in_element_value_by_partial_link_text(
            self, link_text: str, text: str, ele=None, timeout=10):
        """
        判断指定元素的属性值中是否包含了预期的字符串，返回布尔值
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :param text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.text_to_be_present_in_element_value((By.PARTIAL_LINK_TEXT, link_text), text))

    def until_frame_to_be_available_and_switch_to_it(self, ele=None, timeout=10):
        """
        判断该frame是否可以switch进去，如果可以的话，返回True并且switch进去，否则返回False
        :param ele:WebElement
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.frame_to_be_available_and_switch_to_it(ele))

    def until_invisibility_of_element_located_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断某个元素在是否存在于dom或不可见,如果可见返回False,不可见返回这个元素
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.invisibility_of_element_located((By.ID, _id)))

    def until_invisibility_of_element_located_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断某个元素在是否存在于dom或不可见,如果可见返回False,不可见返回这个元素
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_selector)))

    def until_invisibility_of_element_located_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素在是否存在于dom或不可见,如果可见返回False,不可见返回这个元素
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.invisibility_of_element_located((By.LINK_TEXT, link_text)))

    def until_invisibility_of_element_located_by_partial_link_text(self, partial_link_text: str, ele=None, timeout=10):
        """
        判断某个元素在是否存在于dom或不可见,如果可见返回False,不可见返回这个元素
        :param ele:WebElement
        :param timeout:
        :param partial_link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.invisibility_of_element_located((By.LINK_TEXT, partial_link_text)))

    def until_element_to_be_clickable_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断某个元素中是否可见并且是enable的，代表可点击
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_clickable((By.ID, _id)))

    def until_element_to_be_clickable_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断某个元素中是否可见并且是enable的，代表可点击
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))

    def until_element_to_be_clickable_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素中是否可见并且是enable的，代表可点击
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_clickable((By.LINK_TEXT, link_text)))

    def until_element_to_be_clickable_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素中是否可见并且是enable的，代表可点击
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, link_text)))

    def until_staleness_of_by_id(self, _id: str, ele=None, timeout=10):
        """
        等待某个元素从dom树中移除
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.staleness_of((By.ID, _id)))

    def until_staleness_of_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        等待某个元素从dom树中移除
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.staleness_of((By.CSS_SELECTOR, css_selector)))

    def until_staleness_of_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        等待某个元素从dom树中移除
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.staleness_of((By.LINK_TEXT, link_text)))

    def until_staleness_of_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        等待某个元素从dom树中移除
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.staleness_of((By.PARTIAL_LINK_TEXT, link_text)))

    def until_element_to_be_selected_by_id(self, _id: str, ele=None, timeout=10):
        """
        判断某个元素是否被选中了,一般用在下拉列表
        :param ele:WebElement
        :param timeout:
        :param _id:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_selected((By.ID, _id)))

    def until_element_to_be_selected_by_css_selector(self, css_selector: str, ele=None, timeout=10):
        """
        判断某个元素是否被选中了,一般用在下拉列表
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_selected((By.CSS_SELECTOR, css_selector)))

    def until_element_to_be_selected_by_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素是否被选中了,一般用在下拉列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_selected((By.LINK_TEXT, link_text)))

    def until_element_to_be_selected_by_partial_link_text(self, link_text: str, ele=None, timeout=10):
        """
        判断某个元素是否被选中了,一般用在下拉列表
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_to_be_selected((By.PARTIAL_LINK_TEXT, link_text)))

    def until_element_selection_state_to_be_by_id(self, _id: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param _id:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_selection_state_to_be((By.ID, _id), status))

    def until_element_selection_state_to_be_by_css_selector(self, css_selector: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.element_selection_state_to_be((By.CSS_SELECTOR, css_selector), status))

    def until_element_selection_state_to_be_by_link_text(self, link_text: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_selection_state_to_be((By.LINK_TEXT, link_text), status))

    def until_element_selection_state_to_be_by_partial_link_text(
            self, link_text: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.element_selection_state_to_be((By.PARTIAL_LINK_TEXT, link_text), status))

    def until_element_located_selection_state_to_be_by_id(self, _id: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param _id:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.element_located_selection_state_to_be((By.ID, _id), status))

    def until_element_located_selection_state_to_be_by_css_selector(
            self, css_selector: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param css_selector:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.element_located_selection_state_to_be((By.CSS_SELECTOR, css_selector), status))

    def until_element_located_selection_state_to_be_by_link_text(
            self, link_text: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.element_located_selection_state_to_be((By.LINK_TEXT, link_text), status))

    def until_element_located_selection_state_to_be_by_partial_link_text(
            self, link_text: str, ele=None, timeout=10, status=True):
        """
        判断某个元素的选中状态是否符合预期
        :param ele:WebElement
        :param timeout:
        :param link_text:
        :param status:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(
            EC.element_located_selection_state_to_be((By.PARTIAL_LINK_TEXT, link_text), status))

    def until_alert_is_present(self, ele=None, timeout=10):
        """
        判断页面上是否存在alert,如果有就切换到alert并返回alert的句柄
        :param ele:WebElement
        :param timeout:
        :return:
        """
        if not ele:
            ele = self.driver
        return WebDriverWait(ele, timeout).until(EC.alert_is_present())

    def until_is_more_by_scroll_page_judge_by_len(
            self, css_selector: str, min_offset=1000, max_offset=5000, comment_len=0):
        """
        通过长度判断页面是否有更多
        :param css_selector:
        :param min_offset:
        :param max_offset:
        :param comment_len:
        :return:
        """
        self.info_log(data="...开始下拉页面...")
        while True:
            list_len = self.until_get_elements_len_by_css_selector(
                css_selector=css_selector, timeout=1)
            self.random_vertical_scroll_to(min_offset=min_offset, max_offset=max_offset)
            list_len2 = self.until_get_elements_len_by_css_selector(css_selector=css_selector, timeout=1)
            self.info_log(data="当前数量%s:" % list_len2)
            if list_len == list_len2:
                if comment_len:
                    if list_len2 >= comment_len:
                        break
                time.sleep(2)
                self.random_vertical_scroll_to(min_offset=min_offset, max_offset=max_offset)
                list_len2 = self.until_get_elements_len_by_css_selector(css_selector=css_selector, timeout=1)
                if list_len == list_len2:
                    break
        self.logger.info("...结束下拉页面...")

    def until_is_more_by_send_key_arrow_down_judge_by_len(
            self, list_css_selector: str, ele_css_selector: str, min_frequency=100, max_frequency=300, comment_len=0,
            timeout=1):
        """
        通过长度判断页面是否有更多
        :param list_css_selector:列表的css样式
        :param ele_css_selector:发送向下指令的元素的css样式
        :param min_frequency:表示按向下键的次数
        :param max_frequency:
        :param comment_len:
        :param timeout:
        :return:
        """
        self.info_log(data="...开始下拉页面...")
        while True:
            list_len = self.until_get_elements_len_by_css_selector(css_selector=list_css_selector, timeout=timeout)
            self.until_send_key_arrow_down_by_css_selector(css_selector=ele_css_selector, min_frequency=min_frequency,
                                                           max_frequency=max_frequency, timeout=timeout)
            list_len2 = self.until_get_elements_len_by_css_selector(css_selector=list_css_selector)
            self.info_log(data="当前数量%s:" % list_len2)
            if list_len == list_len2:
                if comment_len:
                    if list_len2 >= comment_len:
                        break
                time.sleep(2)
                self.until_send_key_arrow_down_by_css_selector(css_selector=ele_css_selector,
                                                               min_frequency=min_frequency,
                                                               max_frequency=max_frequency, timeout=timeout)
                list_len2 = self.until_get_elements_len_by_css_selector(css_selector=list_css_selector, timeout=timeout)
                if list_len == list_len2:
                    break
        self.logger.info("...结束下拉页面...")

    def until_click_by_vertical_scroll_page_down_by_css_selector(
            self, css_selector: str, ele=None, offset=8, try_times=20):
        """
        通过css_selector向下滚动页面，直到点击成功
        Deprecated use until_click_by_css_selector
        :param css_selector:
        :param ele:
        :param offset:
        :param try_times:
        :return:
        """
        warnings.warn("use until_click_by_css_selector instead", DeprecationWarning)
        failed_times = 0
        click_ele = self.until_presence_of_element_located_by_css_selector(ele=ele, css_selector=css_selector)
        while True:
            self.scroll_to_center(ele=click_ele)
            if failed_times > try_times:
                break
            try:
                click_ele.click()
                self.info_log(data="点击成功")
                break
            except Exception:
                failed_times += 1
                self.info_log(data="...正在尝试第%s次点击..." % failed_times)
                self.vertical_scroll_by(offset=offset)

    def until_click_by_vertical_scroll_page_down(self, ele: WebElement, offset=8, try_times=20):
        """
        向下滚动页面，直到点击成功
        Deprecated use until_click
        :param ele:
        :param offset:
        :param try_times:
        :return:
        """
        warnings.warn("use until_click instead", DeprecationWarning)
        failed_times = 0
        while True:
            self.scroll_to_center(ele=ele)
            if failed_times > try_times:
                break
            try:
                ele.click()
                self.info_log(data="点击成功")
                break
            except Exception:
                failed_times += 1
                self.info_log(data="...正在尝试第%s次点击..." % failed_times)
                self.vertical_scroll_by(offset=offset)

    def until_presence_by_vertical_scroll_page_down_by_css_selector(
            self, css_selector: str, ele=None, offset=8, try_times=20, timeout=1):
        """
        通过css_selector向下滚动页面，直到元素存在
        Deprecated use until_scroll_element_to_center_by_css_selector
        :param ele:WebElement
        :param css_selector:
        :param offset:
        :param try_times:
        :param timeout:
        :return:
        """
        warnings.warn("use until_scroll_element_to_center_by_css_selector instead", DeprecationWarning)
        if not ele:
            ele = self.driver
        failed_times = 0
        while True:
            if failed_times > try_times:
                break
            try:
                self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=css_selector, timeout=int(timeout/10))
                self.info_log(data="元素存在,可以访问")
                break
            except Exception:
                failed_times += 1
                self.warning_log(e="...正在尝试第%s次下拉..." % failed_times)
                self.vertical_scroll_by(offset=offset)

    def until_refresh_by_css_selector(self, css_selector: str, try_times=10):
        """
        通过css_selector获取元素，刷新页面，直到元素存在
        Deprecated use
        :param css_selector:
        :param try_times:
        :return:
        """
        warnings.warn("use instead", DeprecationWarning)
        count = 0
        for i in range(try_times):
            try:
                self.until_presence_of_element_located_by_css_selector(css_selector=css_selector, timeout=1)
            except Exception:
                count += 1
                self.info_log(data="第%s次刷新!!!" % count)
                self.driver.refresh()

    def is_ready_by_proxy_ip(self):
        if self.is_proxy:  # 如果有代理
            count = 0
            while True:
                count += 1
                curr_proxy_ip = self.get_curr_proxy_ip()  # 当前代理ip
                if self.pre_proxy_ip != curr_proxy_ip and curr_proxy_ip != self.initial_proxy_ip:  # 如果ip改变并且不是初始ip
                    self.debug_log(data="proxy_ip由%s变为%s" % (self.pre_proxy_ip, curr_proxy_ip))
                    self.pre_proxy_ip = curr_proxy_ip
                    break
                self.info_log(data="第%s次尝试,proxy_ip没有改变,请等待..." % count)
                time.sleep(1)

    def until_click_no_next_page_by_css_selector(self, next_page_setup: NextPageCssSelectorSetup):
        """
        根据css样式点击直到没有下一页
        :param next_page_setup:
        :return:
        """
        next_page_setup.pre_page_func.run()
        count = 0
        while True:
            count += 1
            self.info_log(data="当前翻到第%s页..." % count)
            self.deal_with_failure_page()
            try:
                next_page_setup.main_page_func.run()
            except Exception as e:
                self.warning_log(e=e)
                break
            if not next_page_setup.is_next:  # 在调试的时候不需要下一页
                break
            try:
                if next_page_setup.stop_css_selector:
                    try:
                        self.until_presence_of_element_located_by_css_selector(
                            css_selector=next_page_setup.stop_css_selector, timeout=next_page_setup.ele_timeout)
                        break
                    except Exception:
                        pass
                if self.is_proxy and next_page_setup.is_proxy:
                    while True:
                        self.is_ready_by_proxy_ip()
                        self.until_scroll_to_center_click_by_css_selector(
                            css_selector=next_page_setup.css_selector, timeout=next_page_setup.ele_timeout)
                        time.sleep(3)
                        if self.is_verify_page():  # 如果这是一个验证页面
                            self.driver.back()
                            self.switch_window_by_index(index=-1)
                            self.info_log(data="这是一个验证页面,后退重试!!!")
                        else:
                            break
                else:
                    self.until_scroll_to_center_click_by_css_selector(
                        css_selector=next_page_setup.css_selector, timeout=next_page_setup.ele_timeout)
                self.info_log(name="点击下一页", data="暂停%s秒..." % next_page_setup.pause_time)
                time.sleep(next_page_setup.pause_time)  # 每一次点击完毕,刷新页面需要缓冲时间
            except Exception as e:
                self.error_log(e=e, istraceback=False)
                break
        next_page_setup.after_page_func.run()

    def until_click_no_next_page_by_partial_link_text(self, next_page_setup: NextPageLinkTextSetup):
        """
        根据链接文字点击直到没有下一页
        :param next_page_setup:
        :return:
        """
        next_page_setup.pre_page_func.run()
        count = 0
        while True:
            count += 1
            self.info_log(data="当前翻到第%s页..." % count)
            try:
                next_page_setup.main_page_func.run()
            except Exception as e:
                self.warning_log(e=e)
                break
            if not next_page_setup.is_next:  # 在调试的时候不需要下一页
                break
            try:
                if self.is_proxy and next_page_setup.is_proxy:
                    while True:
                        self.is_ready_by_proxy_ip()
                        self.until_scroll_to_center_click_by_partial_link_text(
                            link_text=next_page_setup.link_text, timeout=next_page_setup.ele_timeout)
                        time.sleep(3)
                        self.switch_window_by_index(index=-1)  # 确保在当前页面
                        if True in [i in self.driver.title for i in self.verify_page_title_list]:  # 如果这是一个验证页面
                            self.driver.back()
                            self.info_log(data="这是一个验证页面,后退重试!!!")
                        else:
                            break
                else:
                    self.until_scroll_to_center_click_by_partial_link_text(
                        link_text=next_page_setup.link_text, timeout=next_page_setup.ele_timeout)
                self.info_log(name="点击下一页", data="暂停%s秒..." % next_page_setup.pause_time)
                time.sleep(next_page_setup.pause_time)  # 每一次点击完毕,刷新页面需要缓冲时间
            except Exception as e:
                self.error_log(e=e, istraceback=False)
                break
        next_page_setup.after_page_func.run()

    def close_pre_page(self):
        """
        关闭先前的页面
        :return:
        """
        self.driver.switch_to.window(self.driver.window_handles[-2])
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def close_curr_page(self):
        """
        关闭当前的页面
        :return:
        """
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def switch_window_by_index(self, index: int):
        """
        根据索引切换浏览器窗口
        :param index:
        :return:
        """
        self.driver.switch_to.window(self.driver.window_handles[index])

    def until_scroll_to_center_select_by_visible_text_by_css_selector(self, css_selector: str, text: str, ele=None):
        """
        通过可见的文字和css_selector把元素滚动到页面中间
        :param css_selector:
        :param text:
        :param ele:
        :return:
        """
        s = Select(self.until_scroll_to_center_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector))
        s.select_by_visible_text(text)

    def until_scroll_to_center_select_by_value_by_css_selector(self, css_selector: str, value: str, ele=None):
        """
        通过值和css_selector把元素滚动到页面中间
        :param css_selector:
        :param value:
        :param ele:
        :return:
        """
        s = Select(self.until_scroll_to_center_presence_of_element_located_by_css_selector(
            ele=ele, css_selector=css_selector))
        s.select_by_value(value)


# external function

    def get_data_key(self):
        """
        获取数据关键字
        :return:
        """
        return self.data_key

    def get_current_data_list_from_mongodb(self, collection: Collection, *keys):
        """
        获取当前的爬虫数据,以列表形式返回
        :param collection:
        :param keys:表示要保留的关键字，keys是一个列表
        :return:
        """
        if keys:
            data_list = []
            for data in collection.find(self.get_data_key()):
                data_tmp = {}
                for key in keys:
                    data_tmp.setdefault(key, data.get(key))
                data_list.append(data_tmp)
            return data_list
        else:
            return list(collection.find(self.get_data_key()))

    def get_current_data_from_mongodb(self, collection: Collection, other_key=None):
        """
        获取当前的爬虫数据,以字典形式返回
        :param collection:
        :param other_key:dict
        :return:
        """
        if isinstance(other_key, dict):
            raise TypeError
        key = self.merge_dict(other_key, self.get_data_key())
        return collection.find(key)[0]  # 由于返回的是一个长度为1的列表

    def save_data_list_to_mongodb(self, field_list: FieldList, mongodb: Mongodb, data_list: list):
        """
        保存数据列表到mongodb
        :param field_list:
        :param mongodb:
        :param data_list:[{str:value}, {str:value}]
        :return:
        """
        field_key = []
        for field in field_list:
            if field.fieldtype == FieldType.KEY_STR:
                field_key.append(field.fieldname)
        for data in data_list:
            key = self.merge_dict(self.get_data_key(), {fk: data.get(fk) for fk in field_key})
            data = self.merge_dict(self.get_data_key(), data)
            crawl_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))  # 爬虫的时间
            data.setdefault(FieldName.CRAWL_TIME, crawl_time)
            collection_curr = mongodb.get_collection()
            if len(list(collection_curr.find(key))) == 0:
                collection_curr.insert(data)
            else:
                collection_curr.update(key, {"$set": data})

    def save_data_to_mongodb(self, field_list: FieldList, mongodb: Mongodb, data: dict, external_key_name=None):
        """
        通过爬虫单元将数据保存到mongodb
        :param field_list:
        :param mongodb:
        :param data:要保存的数据，{str:value, str:value}
        :param external_key_name:list，{str:value, str:value}
        :return:
        """
        if external_key_name:
            if isinstance(external_key_name, list):
                raise TypeError
            field_key = []
            field_key.extend(external_key_name)
        else:
            field_key = []
        for field in field_list:
            if field.field_type == FieldType.KEY_STR:
                field_key.append(field.field_name)
        key = self.merge_dict(self.get_data_key(), {fk: data.get(fk) for fk in field_key})
        data = self.merge_dict(self.get_data_key(), data)
        crawl_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))  # 爬虫的时间
        data.setdefault(FieldName.CRAWL_TIME, crawl_time)
        collection_curr = mongodb.get_collection()
        if len(list(collection_curr.find(key))) == 0:
            collection_curr.insert(data)
        else:
            collection_curr.update_many(key, {"$set": data})

    @staticmethod
    def update_data_to_mongodb(collection: Collection, key: dict, data: dict):
        collection.update_many(key, {"$set": data})

    @staticmethod
    def merge_dict(data1: dict, data2: dict):
        """
        合并字典
        :param data1:{str:value}
        :param data2:{str:value}
        :return:
        """
        return dict(data1, **data2)

    @staticmethod
    def filter_integer(_str: str):
        """
        从字符串过滤整型数字
        :param _str:
        :return:
        """
        return int(re.sub(r"[^\d]*", "", _str))

    @staticmethod
    def filter_float(_str: str):
        """
        从字符串过滤浮点数
        :param _str:
        :return:
        """
        return float(re.sub(r"[^\d.]*", "", _str))

    @staticmethod
    def filter_str(_str: str):
        """
        过滤掉字符串的换行符
        :param _str:
        :return:
        """
        return re.sub(r"[\n]*", "", _str).strip()

    def get_random_time(self, a=50000, b=150000):
        """

        :param a:
        :param b:
        :return:
        """
        if not isinstance(a, int) or not isinstance(b, int):
            raise TypeError
        c = b
        if a > b:
            b = a
        a = c
        pause_time = float(random.randint(a, b))
        for i in range(len(str(a))-1):
            pause_time /= 10
        self.debug_log(data="随机时间为:%s" % pause_time)
        return pause_time

    def get_key_str_field_by_css_selector(self, field: Field, ele=None):
        """
        获得条目的关键字段
        :param field:
        :param ele: WebElement
        :return:
        """
        time.sleep(field.pause_time)
        try:
            if ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(
                        ele=ele, css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=field.css_selector, timeout=field.timeout)
            elif ele and not field.css_selector:
                if field.is_focus:
                    self.scroll_to_center(ele=ele)
                ele = ele
            elif not ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    css_selector=field.css_selector, timeout=field.timeout)
            else:
                raise AttributeError
            if field.attr:
                _str = ele.get_attribute(field.attr)
            else:
                _str = ele.text
            if field.is_debug:
                self.debug_log(name=field.field_name, data=_str)
            _str = self.filter_str(_str)
            _str = re.sub(field.regex, field.replace, _str)
            if field.filter_func:
                try:
                    _str = field.filter_func(self, _str)
                except Exception as e:
                    self.error_log(e=e)
        except Exception as e:
            self.error_log(name=field.field_name, e=e, level=4)
            _str = ""
        self.info_log(name=field.field_name, data=_str)
        return _str

    def get_str_field_by_css_selector(self, field: Field, ele=None):
        """
        获取条目的字符串字段
        :param field:
        :param ele:WebElement
        :return:
        """
        time.sleep(field.pause_time)
        try:
            if ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(
                        ele=ele, css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=field.css_selector, timeout=field.timeout)
            elif ele and not field.css_selector:
                if field.is_focus:
                    self.scroll_to_center(ele=ele)
                ele = ele
            elif not ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    css_selector=field.css_selector, timeout=field.timeout)
            else:
                raise AttributeError
            if field.attr:
                _str = ele.get_attribute(field.attr)
            else:
                _str = ele.text
            if field.is_debug:
                self.debug_log(name=field.field_name, data=_str)
            _str = self.filter_str(_str)
            _str = re.sub(field.regex, field.replace, _str)
            if field.filter_func:
                try:
                    _str = field.filter_func(self, _str)
                except Exception as e:
                    self.error_log(e=e)
        except Exception as e:
            if field.is_error:
                self.error_log(name=field.field_name, e=e, level=4)
            _str = ""
        if field.is_info:
            self.info_log(name=field.field_name, data=_str)
        return _str

    def get_str_list_field_by_css_selector(self, field: Field, ele=None):
        """
        获取条目的字符串列表字段，如果ele为空或其它错误，都返回为空
        :param field:
        :param ele:WebElement
        :return:
        """
        time.sleep(field.pause_time)
        _list = []
        try:
            list_ele = self.until_presence_of_element_located_by_css_selector(
                ele=ele, css_selector=field.list_css_selector, timeout=field.timeout)
            if not list_ele:
                try:
                    raise ValueError
                except ValueError as e:
                    self.error_log(e=e)
                return None
            for item in self.until_presence_of_all_elements_located_by_css_selector(
                    ele=list_ele, css_selector=field.item_css_selector, timeout=field.timeout):
                _str = self.get_str_field_by_css_selector(ele=item, field=field)
                if _str:
                    _list.append(_str)
        except Exception as e:
            if field.is_error:  # 输出错误日志
                self.error_log(name=field.field_name, e=e, level=4)
            pass
        if field.is_info:
            self.info_log(name=field.field_name, data=json.dumps(_list))
        return _list

    def get_int_field_by_css_selector(self, field: Field, ele=None):
        """
        获取整型的字段
        :param field:
        :param ele:WebElement
        :return:
        """
        time.sleep(field.pause_time)
        try:
            if ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(
                        ele=ele, css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=field.css_selector, timeout=field.timeout)
            elif ele and not field.css_selector:
                if field.is_focus:
                    self.scroll_to_center(ele=ele)
                ele = ele
            elif not ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    css_selector=field.css_selector, timeout=field.timeout)
            else:
                raise ValueError
            if field.attr:
                _str = ele.get_attribute(field.attr)
            else:
                _str = ele.text
            if field.is_debug:
                self.debug_log(name=field.field_name, data=_str)
            _str = self.filter_str(_str)
            _str = re.sub(field.regex, field.replace, _str)
            if field.filter_func:
                try:
                    _str = field.filter_func(self, _str)
                except Exception as e:
                    self.error_log(e=e)
            _int = self.filter_integer(_str)
        except Exception as e:
            if field.is_error:
                self.error_log(name=field.field_name, e=e, level=4)
            _int = 0
        if field.is_info:
            self.info_log(name=field.field_name, data=str(_int))
        return _int

    def get_float_field_by_css_selector(self, field: Field, ele=None):
        """
        获取浮点型的字段
        :param field:
        :param ele:WebElement
        :return:
        """
        time.sleep(field.pause_time)
        try:
            if ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(
                        ele=ele, css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    ele=ele, css_selector=field.css_selector, timeout=field.timeout)
            elif ele and not field.css_selector:
                if field.is_focus:
                    self.scroll_to_center(ele=ele)
                ele = ele
            elif not ele and field.css_selector:
                if field.is_focus:
                    self.until_scroll_to_center_by_css_selector(css_selector=field.css_selector, timeout=field.timeout)
                ele = self.until_presence_of_element_located_by_css_selector(
                    css_selector=field.css_selector, timeout=field.timeout)
            else:
                raise ValueError
            if field.attr:
                _str = ele.get_attribute(field.attr)
            else:
                _str = ele.text
            if field.is_debug:
                self.debug_log(name=field.field_name, data=_str)
            _str = self.filter_str(_str)
            _str = re.sub(field.regex, field.replace, _str)
            if field.filter_func:
                try:
                    _str = field.filter_func(self, _str)
                except Exception as e:
                    self.error_log(e=e)
            _float = self.filter_float(_str)
        except Exception as e:
            if field.is_error:
                self.error_log(name=field.field_name, e=e, level=4)
            _float = 0.0
        if field.is_info:
            self.info_log(name=field.field_name, data=str(_float))
        return _float

    def deal_with_failure_page(self):
        while True:
            try:
                _ = self.driver.find_elements_by_css_selector(css_selector="body")
                break
            except Exception as e:
                self.error_log(e=e)
                if self.is_proxy:
                    self.is_ready_by_proxy_ip()
                self.driver.refresh()

    def run_new_tab_task(self, url: str, try_times=15, pause_time=1, is_close_curr_window=True,
                         pre_page_func=PageFunc(), main_page_func=PageFunc(), after_page_func=PageFunc()):
        """
        运行一个新建标签页的任务(默认根据url打开标签页)
        :param url:标签页链接
        :param try_times:
        :param pause_time:暂停的时间
        :param is_close_curr_window:是否关闭当前窗口
        :param pre_page_func:
        :param main_page_func:
        :param after_page_func:
        :return:
        """
        self.is_ready_by_proxy_ip()
        while True:
            if not self.fast_new_page(url, try_times=try_times):
                return None
            time.sleep(3)
            if self.is_verify_page():  # 如果这是一个验证页面
                self.close_curr_page()
                self.info_log(data="这是一个验证页面,关闭重试!!!")
            else:
                break
        time.sleep(pause_time)
        self.deal_with_failure_page()
        pre_page_func.run()
        data = main_page_func.run()
        after_page_func.run()
        if is_close_curr_window:  # 是否关闭当前页面
            self.close_curr_page()
        return data

    def run_click_tab_task(self, click_css_selector: str, ele=None, try_times=15, pause_time=1,
                           is_close_curr_window=True, pre_page_func=PageFunc(), main_page_func=PageFunc(),
                           after_page_func=PageFunc()):
        """
        运行一个点击出来的标签页的任务(通过按钮点击打开标签页)
        :param click_css_selector:点击的元素css选择器
        :param ele:
        :param try_times:
        :param pause_time:
        :param is_close_curr_window:是否关闭当前窗口
        :param pre_page_func:
        :param main_page_func:
        :param after_page_func:
        :return:
        """
        if not ele:
            ele = self.driver
        while True:
            self.is_ready_by_proxy_ip()
            if not self.fast_click_page_by_css_selector(
                    click_css_selector=click_css_selector, ele=ele, try_times=try_times):  # 如果页面加载失败
                return None
            time.sleep(3)
            if self.is_verify_page():  # 如果这是一个验证页面
                self.close_curr_page()
                self.info_log(data="这是一个验证页面,关闭重试!!!")
            else:
                break
        time.sleep(pause_time)
        self.deal_with_failure_page()
        pre_page_func.run()  # 页面准备函数
        data = main_page_func.run()  # 页面主要函数
        after_page_func.run()
        if is_close_curr_window:  # 是否关闭当前页面
            self.close_curr_page()
        return data

    def select_field_by_css_selector(self, field: Field, ele=None):
        """
        根据css选择器来得到每个字段对应的值
        :param field:
        :param ele:WebElement
        :return:
        """
        if field.is_isolated:  # 如果字段孤立则,把基础页面元素置为driver
            ele = self.driver
        if field.field_type == FieldType.KEY_STR:
            return self.get_key_str_field_by_css_selector(ele=ele, field=field)
        elif field.field_type == FieldType.STR:
            return self.get_str_field_by_css_selector(ele=ele, field=field)
        elif field.field_type == FieldType.LIST_STR:
            return self.get_str_list_field_by_css_selector(ele=ele, field=field)
        elif field.field_type == FieldType.INT:
            return self.get_int_field_by_css_selector(ele=ele, field=field)
        elif field.field_type == FieldType.FLOAT:
            return self.get_float_field_by_css_selector(ele=ele, field=field)

    @staticmethod
    def get_absolute_item_css_selector(list_css_selector: ListCssSelector, index: int):
        """
        index从0开始计数，但是list_css_selector里面的序号是从1开始计数
        根据页面列表的css_selector，获得一个绝对路径的css_selector
        :param list_css_selector:
        :param index:每一个item在列表里面的编号，index必须从0开始
        :return:
        """
        # 注意这里拼接出完整的css selector 是为了防止元素过期, item_css_selector必须放在css_selector的最后面, 也就是元素的编号放在item_css_selector的前面
        if list_css_selector.item_css_selector:
            item_css_selector = "%s:nth-child(%s) > %s" % (
                list_css_selector.list_css_selector, index+1, list_css_selector.item_css_selector)
        else:
            item_css_selector = "%s:nth-child(%s)" % (list_css_selector.list_css_selector, index+1)
        return item_css_selector

    def from_page_get_data_list(self, page: Page):
        """
        item_css_selector的作用就是加快爬虫查找元素的速度
        从页面爬取一个数据列表
        :param page:爬虫页面
        :return:
        """
        self.info_log(data=page.name)
        data_list = list()
        if page.list_css_selector is None:
            raise ValueError
        try:
            elements_list = self.until_presence_of_all_elements_located_by_css_selector(
                css_selector=page.list_css_selector.list_css_selector)
            if page.list_css_selector.item_end < 0 or page.list_css_selector.item_end < 0:  # 如果end或start小于0
                self.info_log(data="item_start和item_end都不可以小于0!!!")
                raise IndexError
            if page.list_css_selector.item_end > 0:
                if page.list_css_selector.item_start > 0:
                    if page.list_css_selector.item_end < page.list_css_selector.item_start:
                        self.info_log(data="item_end在设置的情况下，不可以小于item_start!!!")
                        raise IndexError
            item_start = (lambda x: 0 if x == 0 else x-1)(page.list_css_selector.item_start)
            item_end = (lambda x: len(elements_list) if x == 0 else x)(page.list_css_selector.item_end)
            if not self.is_mobile:  # 如果这是在网页端则支持列表截取，在移动端item_start的作用不是这样的，它作为页面滚动开始标志
                elements_list = elements_list[item_start:item_end]
            for each in elements_list:
                try:
                    if not self.is_mobile:  # 如果是网页端
                        try:
                            self.scroll_to_center(ele=each)  # 把每一个item移动到页面中间
                        except Exception:
                            self.info_log(data="在网页端，这个item无法滚动到页面中间， 所以不是要找的,丢弃...")
                            continue
                    else:
                        try:
                            # 把每一个item移动到页面， 但是不保证在页面中间， 有可能被遮挡
                            self.move_to_element(ele=each, x_offset=page.x_offset, y_offset=page.y_offset)
                        except Exception:
                            self.info_log(data="在移动端，这个item无法拖动到可见的区域， 所以不是要找的,丢弃...")
                            continue
                    item = each
                    if page.list_css_selector.item_css_selector:  # 如果不为空
                        item = self.until_presence_of_element_located_by_css_selector(
                            ele=each, css_selector=page.list_css_selector.item_css_selector)
                    data = self.from_field_list_get_data(page=page, ele=item)
                    if data:  # 如果因为关键字段数据不为空,则数据不为空
                        if page.is_save:
                            if page.mongodb is None:
                                self.info_log(data="无法确定数据保存位置!!!")
                                raise FileNotFoundError
                            else:
                                self.save_data_to_mongodb(field_list=page.field_list, mongodb=page.mongodb, data=data)
                        data_list.append(data)
                except Exception as e:
                    self.error_log(name=page.name, e=e)
            if self.is_mobile:  # 如果是移动端，就会继续判断页面是否有下一个item
                i = page.list_css_selector.item_start
                while True:
                    item_css_selector = self.get_absolute_item_css_selector(page.list_css_selector, i)
                    self.info_log(data="item_css_selector:%s" % item_css_selector)
                    try:
                        self.until_move_to_element_by_css_selector(css_selector=item_css_selector)
                    except Exception:
                        self.info_log(data="经过不停地移动， 移动端页面没有更多了!!!")
                        break
                    item = self.until_presence_of_element_located_by_css_selector(item_css_selector)
                    data = self.from_field_list_get_data(page=page, ele=item)
                    if data:  # 如果因为关键字段数据不为空,则数据不为空
                        if page.is_save:
                            if page.mongodb is None:
                                self.info_log(data="无法确定数据保存位置!!!")
                                raise FileNotFoundError
                            else:
                                self.save_data_to_mongodb(field_list=page.field_list, mongodb=page.mongodb, data=data)
                        data_list.append(data)
                    i += 1
        except Exception:
            self.info_log(data="列表页面找不到需要抓取的元素!!!")
            # 由于列表页面必定是一个不断点击下一页的
            try:
                self.driver.back()
            except Exception:
                self.info_log(data="没有下一页页面无法回退!!!")
                try:
                    self.driver.refresh()
                except Exception:
                    self.info_log(data="页面遇到不可预见的错误,直接退出程序,请检查!!!")
                    self.driver.quit()
                    sys.exit(1)
        return data_list

    def from_field_list_get_data(self, page: Page, ele=None):
        """
        从字段列表获取数据
        :param page:爬虫页面
        :param ele:WebElement,当前条目所在的网页元素
        :return:
        """
        data = dict()
        internal_key = dict()
        for field in page.field_list:
            d = self.select_field_by_css_selector(field=field, ele=ele)
            if not d and field.field_type == FieldType.KEY_STR:  # 如果默认的关键字为空,就不把数据加入数据库
                return None
            if field.field_type == FieldType.KEY_STR:
                internal_key.setdefault(field.field_name, d)
            data.setdefault(field.field_name, d)
        return data

    def from_page_add_data_to_data_list(self, page: Page, pre_page: Page, data_list=None, pre_page_func=PageFunc(),
                                        after_page_func=PageFunc(), extra_page_func=PageFunc()):
        """
        把当前页面的数据再次添加到之前的页面里面
        :param pre_page:先前的页面
        :param page:爬虫页面
        :param data_list:字典类型数据列表，[{str:value},{str:value}]
        :param pre_page_func:
        :param after_page_func:
        :param extra_page_func:
        :return:
        """
        # 整合field_list
        field_list_merge = FieldList()
        for field in page.field_list:
            field_list_merge.append(field)
        for field in pre_page.field_list:
            field_list_merge.append(field)
        data_list_tmp = data_list
        item_start = (lambda x: 0 if x == 0 else x - 1)(pre_page.list_css_selector.item_start)
        item_end = (lambda x: item_start+len(data_list) if x == 0 else x)(pre_page.list_css_selector.item_end)
        data_index_list = range(item_start, item_end)  # 数据索引列表
        for i in data_index_list:
            if page.tab_setup.click_css_selector:
                item_css_selector = self.get_absolute_item_css_selector(pre_page.list_css_selector, i)
                self.debug_log(name="item_css_selector", data=item_css_selector)
                ele = self.until_presence_of_element_located_by_css_selector(css_selector=item_css_selector)
                add_data = self.run_click_tab_task(click_css_selector=page.tab_setup.click_css_selector,
                                                   ele=ele, try_times=page.tab_setup.try_times,
                                                   pause_time=page.tab_setup.pause_time,
                                                   is_close_curr_window=not extra_page_func.func,
                                                   pre_page_func=pre_page_func,
                                                   main_page_func=PageFunc(
                                                       func=self.from_field_list_get_data, page=page),
                                                   after_page_func=after_page_func)
            elif page.tab_setup.url_name:
                add_data = self.run_new_tab_task(try_times=page.tab_setup.try_times,
                                                 pause_time=page.tab_setup.pause_time,
                                                 url=data_list[i].get(page.tab_setup.url_name),
                                                 is_close_curr_window=not extra_page_func.func,
                                                 pre_page_func=pre_page_func,
                                                 main_page_func=PageFunc(func=self.from_field_list_get_data, page=page),
                                                 after_page_func=after_page_func)
            else:
                self.info_log(data="不属于两种标签页类型!!!")
                raise TypeError
            if add_data and data_list_tmp[i]:  # 如果add_data不为空
                data_list_tmp[i].update(add_data)
                if page.is_save:
                    if len(data_list_tmp[i]) == len(field_list_merge):
                        self.save_data_to_mongodb(
                            field_list=field_list_merge, mongodb=page.mongodb,
                            data=data_list_tmp[i])  # 注意关键字段必定出现在前面一页
                    else:
                        self.info_log(data="field的field_name的命名可能出现了重复,请检查!!!")
            if extra_page_func.func:
                extra_page_func.run()
                self.close_curr_page()
        return data_list_tmp

    def from_page_add_data_list_to_data_list(self, page: Page, pre_page: Page, data_list=None, pre_page_func=PageFunc(),
                                             after_page_func=PageFunc(), extra_page_func=PageFunc()):
        """
        把当前页面的数据列表再次添加到之前的页面的数据列表里面
        :param pre_page:先前的页面
        :param page:爬虫页面
        :param data_list:字典类型数据列表，[{str:value},{str:value}]
        :param pre_page_func:
        :param after_page_func:
        :param extra_page_func:
        :return:
        """
        # 整合field_list
        field_list_merge = FieldList()
        for field in page.field_list:
            field_list_merge.append(field)
        for field in pre_page.field_list:
            field_list_merge.append(field)
        data_list_tmp = []
        for i in range(len(data_list)):
            if page.tab_setup.click_css_selector:
                # 注意这里拼接出完整的css selector 是为了防止元素过期
                if pre_page.list_css_selector.item_css_selector:
                    item_css_selector = "%s:nth-child(%s) > %s" % (pre_page.list_css_selector.list_css_selector, i+1,
                                                                   pre_page.list_css_selector.item_css_selector)
                else:
                    item_css_selector = "%s:nth-child(%s)" % (pre_page.list_css_selector.list_css_selector, i+1)
                ele = self.until_presence_of_element_located_by_css_selector(css_selector=item_css_selector)
                add_data_list = self.run_click_tab_task(ele=ele, try_times=page.tab_setup.try_times,
                                                        pause_time=page.tab_setup.pause_time,
                                                        click_css_selector=page.tab_setup.click_css_selector,
                                                        is_close_curr_window=not extra_page_func.func,
                                                        pre_page_func=pre_page_func,
                                                        main_page_func=PageFunc(func=self.from_page_get_data_list,
                                                                                page=page),
                                                        after_page_func=after_page_func)
            elif page.tab_setup.url_name:
                add_data_list = self.run_new_tab_task(
                    try_times=page.tab_setup.try_times, pause_time=page.tab_setup.pause_time,
                    url=data_list[i].get(page.tab_setup.url_name), is_close_curr_window=not extra_page_func.func,
                    pre_page_func=pre_page_func, main_page_func=PageFunc(func=self.from_page_get_data_list, page=page),
                    after_page_func=after_page_func)
            else:
                self.info_log(data="不属于两种标签页类型!!!")
                raise TypeError
            if add_data_list and data_list[i]:  # 如果add_data不为空
                add_data_list = (lambda x: x if x else [])(add_data_list)  # 防止出错
                merge_data_list = [self.merge_dict(add_data, data_list[i]) for add_data in add_data_list]
                if extra_page_func.func:
                    extra_page_func.set_kwargs(data_list=merge_data_list)
                    extra_page_func.run()
                    if extra_page_func.func:
                        self.close_curr_page()
                if page.is_save:
                    if len(merge_data_list[0][0]) == len(field_list_merge):
                        self.debug_log(data="保存数据成功!!")
                        self.save_data_list_to_mongodb(field_list=field_list_merge, mongodb=page.mongodb,
                                                       data_list=merge_data_list)  # 注意关键字段必定出现在前面一页
                    else:
                        self.info_log(data="field的field_name的命名可能出现了重复,请检查!!!")
                data_list_tmp.extend(merge_data_list)
        return data_list_tmp

    def fast_get_page(self, url: str, try_times=15, min_time_to_wait=30, max_time_to_wait=60, is_max=False,
                      is_scroll_to_bottom=True):
        """
        打开网页快速加载页面,直到成功加载
        :param url:页面链接
        :param try_times:尝试的次数
        :param min_time_to_wait:最小的页面等待时间
        :param max_time_to_wait:最大的页面等待时间
        :param is_max:是否最大化页面
        :param is_scroll_to_bottom:页面是否滚动到底部(这个参数的作用是为了保证页面加载完全)
        :return:成功返回True，失败返回False
        """
        time.sleep(2)
        self.driver.get("about:blank")
        if is_max:
            self.driver.maximize_window()
        self.fast_new_page(url=url, try_times=try_times, min_time_to_wait=min_time_to_wait,
                           max_time_to_wait=max_time_to_wait, is_scroll_to_bottom=is_scroll_to_bottom)

    def fast_new_page(self, url: str, try_times=15, min_time_to_wait=30, max_time_to_wait=60, is_scroll_to_bottom=True):
        """
        新建标签页码快速加载页面,直到成功加载
        没有标明含义的参数详见fast_get_page方法
        :param url:
        :param try_times:重试次数
        :param min_time_to_wait:
        :param max_time_to_wait:
        :param is_scroll_to_bottom:
        :return:
        """
        for i in range(1, try_times+1):
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.set_page_load_timeout(random.randint(min_time_to_wait, max_time_to_wait))
                self.new_window(url)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.refresh()
                if is_scroll_to_bottom:
                    self.vertical_scroll_to()  # 滚动到页面底部
                self.debug_log(data="经过%s次创建标签页和%s次关闭标签页,成功加载页面!!!" % (i, i - 1))
                return True
            except TimeoutError:
                self.info_log(data="第%s次加载页面失败!!!" % i)
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[-1])
        try:
            raise TimeoutError
        except TimeoutError:
            self.exit_for_failing_to_load_page()
        return False

    def fast_click_page_by_css_selector(self, click_css_selector: str, ele=None, try_times=15, min_time_to_wait=30,
                                        max_time_to_wait=60, is_scroll_to_bottom=True):
        """
        点击打开新标签页并快速加载页面，直到成功加载
        没有标明含义的参数详见fast_get_page方法
        :param click_css_selector:要点击的按钮的css_selector
        :param ele:WebElement对象
        :param try_times:重试次数
        :param min_time_to_wait:
        :param max_time_to_wait:
        :param is_scroll_to_bottom
        :return:
        """
        if not ele:
            ele = self.driver
        for i in range(1, try_times+1):
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.set_page_load_timeout(random.randint(min_time_to_wait, max_time_to_wait))
                self.until_scroll_to_center_click_by_css_selector(ele=ele, css_selector=click_css_selector)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.refresh()
                if is_scroll_to_bottom:
                    self.vertical_scroll_to()  # 滚动到页面底部
                self.debug_log(data="经过%s次点击和%s次关闭标签页,成功加载页面!!!" % (i, i - 1))
                return True
            except Exception:
                self.info_log(data="第%s次加载页面失败!!!" % i)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
        try:
            raise TimeoutError
        except TimeoutError:
            self.exit_for_failing_to_load_page()
        return False

    def fast_click_same_page_by_css_selector(self, click_css_selector: str, ele=None, try_times=15, min_time_to_wait=30,
                                             max_time_to_wait=60, is_scroll_to_bottom=True):
        """
        点击在相同页面快速加载页面，直到成功加载
        没有标明含义的参数详见fast_click_page_by_css_selector方法
        :param click_css_selector:
        :param ele:
        :param try_times:重试次数
        :param min_time_to_wait:
        :param max_time_to_wait:
        :param is_scroll_to_bottom:
        :return:
        """
        if not ele:
            ele = self.driver
        try:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.set_page_load_timeout(random.randint(min_time_to_wait, max_time_to_wait))
            self.until_scroll_to_center_click_by_css_selector(ele=ele, css_selector=click_css_selector)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.refresh()
            if is_scroll_to_bottom:
                self.vertical_scroll_to()  # 滚动到页面底部
            self.debug_log(data="经过%s次点击和%s次关闭标签页,成功加载页面!!!" % (1, 1 - 1))
            return True
        except Exception as e:
            self.error_log(e=e, istraceback=False)
            curr_url = self.driver.current_url
            self.debug_log(data=curr_url)
            if not self.fast_new_page(url=curr_url, try_times=try_times):
                self.exit_for_failing_to_load_page()
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[-1])

    def fast_click_first_item_page_by_partial_link_text(self, link_text: str, ele=None, try_times=15,
                                                        min_time_to_wait=30, max_time_to_wait=60,
                                                        is_scroll_to_bottom=True):
        """
        点击列表新建标签页第一个元素快速加载页面，直到成功加载
        没有标明含义的参数详见fast_click_page_by_css_selector方法
        :param link_text:按钮的里面包含的文字
        :param ele:
        :param try_times:重试次数
        :param min_time_to_wait:
        :param max_time_to_wait:
        :param is_scroll_to_bottom:
        :return:
        """
        for i in range(1, try_times+1):
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.set_page_load_timeout(random.randint(min_time_to_wait, max_time_to_wait))
                self.until_scroll_to_center_click_by_first_partial_link_text(ele=ele, link_text=link_text)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.refresh()
                if is_scroll_to_bottom:
                    self.vertical_scroll_to()  # 滚动到页面底部
                self.debug_log(data="经过%s次点击和%s次关闭标签页,成功加载页面!!!" % (i, i - 1))
                return True
            except Exception:
                self.info_log(data="第%s次加载页面失败!!!" % i)
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[-1])
        try:
            raise TimeoutError
        except TimeoutError:
            self.exit_for_failing_to_load_page()
        return False

    def fast_enter_page_by_css_selector(self, css_selector: str, try_times=15):
        """
        快速回车加载页面，直到成功加载
        :param css_selector:
        :param try_times:重试次数
        :return:
        """
        try:
            self.until_scroll_to_center_send_enter_by_css_selector(css_selector=css_selector)
        except Exception as e:
            self.error_log(e=e)
            self.fast_new_page(url=self.driver.current_url, try_times=try_times)
            self.driver.switch_to.window(self.driver.window_handles[-2])
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[-1])

    def fast_click_first_item_same_page_by_partial_link_text(self, link_text: str, try_times=15):
        """
        快速点击链接在相同的页面加载，直到成功加载
        :param link_text:
        :param try_times:重试次数
        :return:
        """
        curr_url = ""
        try:
            ele = self.until_presence_of_all_elements_located_by_partial_link_text(link_text=link_text)[0]
            self.scroll_to_center(ele=ele)
            curr_url = ele.get_attribute("href")
            self.until_scroll_to_center_click_by_first_partial_link_text(link_text=link_text)
        except Exception:
            try:
                curr_url = self.driver.current_url
            except Exception:
                pass
            self.debug_log(data=curr_url)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.close()
            if not self.fast_new_page(url=curr_url, try_times=try_times):
                self.exit_for_failing_to_load_page()

    def exit_for_failing_to_load_page(self):
        self.info_log(data="重试次数超过上限!!!")
        self.driver.quit()
        sys.exit(0)
