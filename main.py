import aiohttp
import asyncio
import http.cookies
from bs4 import BeautifulSoup


URL = "https://e-learning.unpam.ac.id/my/"
LOGIN_URL = "https://e-learning.unpam.ac.id/login/index.php"

async def login():
    async with aiohttp.ClientSession() as session:
        async with session.get(LOGIN_URL) as response:
            html = await response.text()
            raw_cookies =  response.headers.getall('Set-Cookie')
            cookie_obj = http.cookies.SimpleCookie()
            for raw_cookie in raw_cookies:
                cookie_obj.load(raw_cookie)
            moodleSession = cookie_obj.get('MoodleSession').value #type: ignore
            print(moodleSession)
            parser = BeautifulSoup(html, "html.parser")
            logintoken = parser.find_all("input", {"name":"logintoken"})[0].get('value')
            payload = {
                "anchor": "",
                "logintoken": logintoken,
                "username": "211011450446",
                "password": "02194316762a"
            }
            async with session.post(LOGIN_URL, data=payload) as login_response:
                if login_response.status == 200:
                    print("sukses")
                await asyncio.create_task(getMatkul(await login_response.text()))
                    
async def getMatkul(html):
    parser = BeautifulSoup(html, "html.parser")

    side = parser.find('div', class_='dashbord_nav_list ccn_dashbord_nav_list')
    ul_element = side.select("ul") # type: ignore
    for li in ul_element[0].select("li"):
        try:
            a = li.a
            if a != None:
                href = a.get("href")
                if str(href).find("https://e-learning.unpam.ac.id/course/view.php?id") != -1:
                    print(href)
        except AttributeError:
            pass

asyncio.run(login())