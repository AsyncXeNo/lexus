import zipfile

from selenium import webdriver
from fake_useragent import UserAgent

HOST = 'proxy.packetstream.io'
PORT = '31112'
USER = 'm_eddielee'
PASS = 'v4Xj5Z96gpJrppUV'

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (HOST, PORT, USER, PASS)


def get_chromedriver(use_proxy=False):
    chrome_options = webdriver.ChromeOptions()

    chrome_prefs = {
        "profile.default_content_setting_values": {
            "images": 2,  # 2 means block images
            # "javascript": 2,  # 2 means block JavaScript
            "plugins": 2,  # 2 means block plugins
            "css": 2,  # 2 means block CSS
        }
    }

    ua = UserAgent()

    chrome_options.add_argument(f'--user-agent={ua.random}')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_experimental_option('prefs', chrome_prefs)

    if use_proxy:
        pluginfile = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        chrome_options.add_extension(pluginfile)

    driver = webdriver.Chrome(options=chrome_options)

    return driver
