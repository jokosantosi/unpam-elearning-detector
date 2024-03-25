import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
sem = asyncio.Semaphore(10)

class unpamChecker():
    def __init__(self) -> None:
        self.username = os.getenv("UNPAM_NIM") or str(input("Masukan NIM kamu : "))
        self.password = os.getenv("UNPAM_PASS") or str(input("Masukan password E-learning kamu : "))
        self.URL = "https://e-learning.unpam.ac.id/my/"
        self.LOGIN_URL = "https://e-learning.unpam.ac.id/login/index.php"

    async def getLoginToken(self, session):
        async with session.get(self.LOGIN_URL) as response:
            htmlSource = BeautifulSoup(await response.text(), "html.parser")
            loginToken = htmlSource.find_all("input", {"name":"logintoken"})[0].get('value')
            return loginToken
        
    async def loginRequest(self, session, params):
        async with session.post(self.LOGIN_URL, data=params) as response:
            print("[+] Login...")
            if (response.status == 200): return True
            else:
                return False

    async def getCourseUrls(self, session, url):
        async with session.get(url) as response:
            htmlSource = BeautifulSoup(await response.text(), "html.parser")
            dashboardContent = htmlSource.find('div', class_='dashbord_nav_list ccn_dashbord_nav_list').select_one("ul").select("li") #type: ignore
            courseList:list = []
            for content in dashboardContent:
                try:
                    aElement = content.a
                    if aElement != None:
                        courseUrl = str(aElement.get("href"))
                        courseName = aElement.select_one("span")
                        courseLinkIndentity = "https://e-learning.unpam.ac.id/course/view.php?id"
                        if (courseUrl.find(courseLinkIndentity) != -1) and (courseName != None):
                            courseList.append({"courseName": courseName.text, "courseUrl": courseUrl})
                except AttributeError: pass
            return courseList

    async def getDiscussUrls(self, session, url):
        async with session.get(url) as response:
            htmlSource = BeautifulSoup(await response.text(), 'html.parser')
            forumDiscussList = htmlSource.find_all('li', class_='activity forum modtype_forum')
            forumDiscussUrls:list = []
            for item in forumDiscussList:
                forumDiscussUrls.append(item.find('a')['href'])
            return forumDiscussUrls

    async def findDiscussExistence(self, session, url):
        async with sem:
            async with session.get(url) as response:
                htmlSource = BeautifulSoup(await response.text(), 'html.parser')
                discussTable = htmlSource.find('table', class_='table discussion-list')
                if discussTable != None:
                    discussForums = discussTable.find_all("tr", class_="discussion") #type: ignore
                    manyDiscussForum = len(discussForums)
                    for discussForum in discussForums:
                        if (len(discussForum['class']) == 2): manyDiscussForum -= 1
                    if manyDiscussForum >= 1: return True
                    else: return False

    async def getDiscussInfo(self, session, url):
        async with session.get(url) as response:
            htmlSource = BeautifulSoup(await response.text(), "html.parser")
            courseTitle = htmlSource.find("h4", class_="breadcrumb_title").text #type: ignore
            forumTitle = htmlSource.find("h2", class_="ccnMdlHeading").text #type:ignore
            return [courseTitle, forumTitle, url]

    async def main(self):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            params = {
                "anchor": "",
                "logintoken": await asyncio.create_task(self.getLoginToken(session)),
                "username": self.username,
                "password": self.password
            }
            if await asyncio.create_task(self.loginRequest(session, params)):
                print("[+] Getting course list...")
                courseList = await asyncio.create_task(self.getCourseUrls(session, self.URL))
                discussTasks:list = []
                courseName:list = []
                for courseData in courseList:
                    courseName.append(courseData["courseName"])
                    discussTasks.append(asyncio.ensure_future(self.getDiscussUrls(session, courseData["courseUrl"])))
                discussResults = await asyncio.gather(*discussTasks)
                discussDatas = dict(zip(courseName, discussResults))

                findDiscussTasks:list = []
                discussUrls:list = []
                for discussName in courseName:
                    for discussUrl in discussDatas[discussName]:
                        discussUrls.append(discussUrl)
                        findDiscussTasks.append(asyncio.create_task(self.findDiscussExistence(session, discussUrl)))
                print("[+] Getting Discuss Task...")
                forumResults = await asyncio.gather(*findDiscussTasks)
                forumDatas = dict(zip(discussUrls, forumResults))

                forumUrls:list = []
                getTitleTasks:list = []
                for url, status in forumDatas.items():
                    if (status and status != None): forumUrls.append(url)
                for forumUrl in forumUrls:
                    getTitleTasks.append(asyncio.create_task(self.getDiscussInfo(session, forumUrl))) #type: ignore
                print("[+] Getting Information About The Task...")
                titleResults = await asyncio.gather(*getTitleTasks)
                result:str = ""
                if len(getTitleTasks) != 0:
                    for i in range(len(titleResults)):
                        if (titleResults[i][0] != titleResults[i-1][0]):
                            result += titleResults[i][0] + "\n"
                            result += f'  {titleResults[i][1]} : {titleResults[i][2]}\n'
                        else:
                            result += f'  {titleResults[i][1]} : {titleResults[i][2]}\n'
                    return result
                else: return "Selamat! kamu udah nyelesain semua tugas dosen, pasti dosen senang dan kamu aman"
            else: return "Gk bisa login, coba cek lagi deh"
            
if __name__ == "__main__":
    asyncio.run(unpamChecker().main())