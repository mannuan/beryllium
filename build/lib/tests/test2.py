from selenium import webdriver

mobile_emulation = { "deviceName": "Nexus 5" }

chrome_options = webdriver.ChromeOptions()

chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

driver = webdriver.Remote(command_executor='http://127.0.0.1:4444/wd/hub',

                          desired_capabilities = chrome_options.to_capabilities())