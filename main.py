from fastapi import FastAPI
from bs4 import BeautifulSoup
import aiohttp

app = FastAPI()


async def get_site_content(link):
    hdr = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/92.0.4515.107 Mobile Safari/537.36'}
    async with aiohttp.ClientSession() as session:
        async with session.get(link, headers=hdr) as resp:
            text = await resp.read()
    return text


async def mangas(search):
    url = f"https://mangakomi.io/?s={search}&post_type=wp-manga"
    page_html = await get_site_content(url)

    page_soup = BeautifulSoup(page_html, "html.parser")
    mana = page_soup.find_all("div", {"class": "col-4 col-12 col-md-2"})
    latest = page_soup.find_all("span", {"class": "font-meta chapter"})
    results = []
    latest_chapters = []
    manga_urls = []
    for i in mana:
        results.append(i.div.a['title'])
        manga_urls.append(i.a['href'])
    for x in latest:
        latest_chapters.append(x.a.text)
    return results, latest_chapters, manga_urls


async def chapters(url: str, chapter: int):
    new_url = f"{url}chapter-{chapter}/"
    new_page_html = await get_site_content(new_url)

    new_page_soup = BeautifulSoup(new_page_html, "html.parser")
    images = new_page_soup.find_all("img")
    return images[2:]

async def get_manga_info(url: str):
    page_html = await get_site_content(url)

    page_soup = BeautifulSoup(page_html, "html.parser")

    image = page_soup.find_all("div", {"class": "summary_image"})
    title = page_soup.find_all("h1")

    return image[0].a.img['data-src'], title[0].text


async def get_earliest(url: str):
    page_html = await get_site_content(url)
    page_soup = BeautifulSoup(page_html, "html.parser")
    chapters = page_soup.find_all("li", {"class": "wp-manga-chapter"})
    e = len(chapters)
    return chapters[e - 1].a.text.replace("\n", "")


@app.get("/")
async def root():
    return {"Yo": "Hello World"}


@app.get("/ms/")
async def manga_search(name: str):
    titles, latest_chapters, manga_urls = await mangas(name)
    if titles and latest_chapters:
        return {
            "results": [
                {
                    "title": i,
                    "latest_chapter": x,
                    "earliest_chapter": await get_earliest(y),
                    "url": y
                }
            for i, x, y in zip(titles, latest_chapters, manga_urls)]
        }
    else:
        return {
            "error": "Could not find the title"
        }


@app.get("/get_chapter/")
async def get_chapter(url: str, chapter: int = 1):
    """
    Get the panel images through this

    - **url**: The chapter url which you can get through /manga/{title}
    - **chapter**: The specific chapter you want by default its 1 but pls keep in mine that not all manga have a chapter 1
    """
    images = await chapters(url, chapter)
    cover_image, title = await get_manga_info(url)
    if images:
        return {
            "name": title.replace("\n", ""),
            "chapter": chapter,
            "manga-cover": cover_image,
            "pages": [
            i['data-src'].replace("\t\t\t\n\t\t\t", "") for i in images]
            }
