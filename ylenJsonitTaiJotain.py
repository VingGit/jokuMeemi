import requests
import xmltodict
import json
from bs4 import BeautifulSoup
import os
import re

def getNewLinks(rssFeedLink: str) -> list:
    newsLinks = []
    response = requests.get(rssFeedLink)
    if response.status_code == 200:
        try:
            data = xmltodict.parse(response.text)
            with open("feed_output.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            items = data["rss"]["channel"]["item"]
            if isinstance(items, list):
                for entry in items:
                    print(entry.get("link"))
                    newsLinks.append(entry.get("link"))
            elif isinstance(items, dict):
                print(items.get("link"))
                newsLinks.append(items.get("link"))

        except Exception as e:
            print(f"Failed to parse XML: {e}")
    else:
        print(f"HTTP request failed with status code {response.status_code}")
    
    return newsLinks

def extractArticlesAsJson(newsLinks: list) -> list:
    article_json_objects = []
    for url in newsLinks:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")
                articles = soup.find_all("article", class_="yle__article arkki-theme-default")
                for article in articles:
                    xml_string = article.prettify()
                    article_dict = xmltodict.parse(xml_string)
                    article_json_objects.append(article_dict)
            else:
                print(f"Failed to load page: {url} (status code {response.status_code})")
        except Exception as e:
            print(f"Exception fetching {url}: {e}")
    return article_json_objects

def extractTitleFromArticle(article_dict: dict) -> str:
    def recursive_find_h1(obj):
        if isinstance(obj, dict):
            if "@class" in obj and "yle__article__heading--1" in obj["@class"] and "#text" in obj:
                return obj["#text"]
            for value in obj.values():
                result = recursive_find_h1(value)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = recursive_find_h1(item)
                if result:
                    return result
        return None

    raw_title = recursive_find_h1(article_dict)
    if raw_title:
        safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title).strip()
        return safe_title
    else:
        return "unnamed_article"


def writeArticlesToJson(articles: list, output_dir="articles_json"):
    os.makedirs(output_dir, exist_ok=True)
    for article in articles:
        title = extractTitleFromArticle(article)
        filename = f"{title}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article, f, indent=2, ensure_ascii=False)
        print(f"Saved: {filepath}")

# Execution
links = getNewLinks("https://feeds.yle.fi/uutiset/v1/majorHeadlines/YLE_UUTISET.rss")
article_json_objects = extractArticlesAsJson(links)
writeArticlesToJson(article_json_objects)

