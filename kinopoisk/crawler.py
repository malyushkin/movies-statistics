import pandas as pd
import re
import requests

from lxml import etree

from config import COOKIES, KP_LIST_SIZE, KP_URL, KP_USER_LIST_URL, KP_USER_ID


def get_kp_dom(url) -> etree._Element:
    """Get Kinopoisk data"""

    headers = {
        "cookie": COOKIES,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/106.0.0.0 Safari/537.36"
    }

    request = requests.get(url, headers=headers)
    print(request.url)

    if request.status_code != 200:
        raise Exception(f"URL response has {request.status_code} status code!")

    return etree.HTML(request.text)


def parse_kp_list(dom: etree._Element) -> list:
    """Parse Kinopoisk list"""

    items = dom.xpath("//div[@class='profileFilmsList']/div[contains(@class, 'item')]")

    profile_data = [
        {
            "name": item.xpath("div[@class='info']/div[@class='nameEng']")[0].text,
            "name_rus": item.xpath("div[@class='info']/div[@class='nameRus']/a")[0].text,
            "url": KP_URL.format(path=item.xpath("div[@class='info']/div[@class='nameRus']/a")[0].attrib["href"]),
            "date": item.xpath("div[@class='date']")[0].text.split(", ")[0],
            "vote": int(re.search(
                pattern=r"rating: [^,]*",
                string=item.xpath("script")[0].text.strip()[13:-2]
            ).group().split(" ")[1].strip("'")),
        } for item in items
    ]

    return profile_data


def crawler() -> pd.DataFrame:
    """Crawler code"""

    page_num = 1
    kp_dom = get_kp_dom(KP_USER_LIST_URL.format(user=KP_USER_ID, page_num=page_num))

    pages_range = kp_dom.xpath("//div[@class='pagesFromTo']")

    if pages_range:
        movies_count = int(pages_range[0].text.split(" из ")[1])
    else:
        raise Exception("Page range parse problem!")

    kd_df = pd.DataFrame(parse_kp_list(kp_dom))

    if movies_count > KP_LIST_SIZE:
        page_num += 1

        while page_num <= (movies_count // KP_LIST_SIZE) + 1:
            kp_dom = get_kp_dom(KP_USER_LIST_URL.format(user=KP_USER_ID, page_num=page_num))
            kd_df = pd.concat([kd_df, pd.DataFrame(parse_kp_list(kp_dom))], ignore_index=True)

            page_num += 1

    return kd_df


if __name__ == "__main__":
    data = crawler()
    data.to_csv("kinopoisk_test.csv")