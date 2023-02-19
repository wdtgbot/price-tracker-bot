import logging
import random
import time

import requests
from bs4 import BeautifulSoup

import pt_config
import pt_error
from pt_entity import GoodInfo

logger = logging.getLogger("momo")


def find_good_info(good_id=None):
    logger.info("good_id %s", good_id)
    response = _get_good_info_from_momo(i_code=good_id)

    if not response:
        raise pt_error.EmptyPageError

    soup = BeautifulSoup(response, "html.parser")
    try:
        if soup.find("meta", property="og:title") is None:
            raise pt_error.GoodNotExist
        good_name = soup.find("meta", property="og:title")["content"]
        logger.info("good_name %s", good_name)
        price = _format_price(soup.find("meta", property="product:price:amount")["content"])
        logger.info("price %s", price)
        stock_state = soup.find("meta", property="product:availability")["content"]
        if stock_state == "in stock":
            stock_state = GoodInfo.STOCK_STATE_IN_STOCK
        else:
            stock_state = GoodInfo.STOCK_STATE_OUT_OF_STOCK
        logger.info("stock_state %s", stock_state)
    except pt_error.GoodNotExist as e:
        raise e
    except Exception:
        logger.error("Parse good_info and catch an exception. good_id:%s", good_id, exc_info=True)
        raise pt_error.CrawlerParseError
    return GoodInfo(good_id=good_id, name=good_name, price=price, stock_state=stock_state)


def _format_price(price):
    return int(str(price).strip().replace(",", ""))


def _get_good_info_from_momo(i_code=None):
    time.sleep(round(random.uniform(0, 1), 2))
    result = None
    try:
        params = {"i_code": i_code}
        response = requests.get(
            pt_config.momo_good_url(),
            params=params,
            headers={"user-agent": pt_config.USER_AGENT,
                     "content-type": "text/html; charset=UTF-8",
                     "referer": "https://m.momoshop.com.tw/"},
            timeout=pt_config.MOMO_REQUEST_TIMEOUT,
        )
        result = response.text
    except requests.exceptions.ReadTimeout:
        logger.error(f"ReadTimeout i_code:{i_code}")
    return result


def generate_momo_url_by_good_id(good_id):
    return (pt_config.MOMO_URL + pt_config.MOMO_GOOD_URI + "?i_code=%s") % str(good_id)
