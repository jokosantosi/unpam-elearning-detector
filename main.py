import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
    
    def loginBySelenium(self):
        chromeOptions = ChromeOptions()
        chromeOptions.add_argument("--headless")
        driver = webdriver.Chrome(options=chromeOptions)
        print("[+] Login...")
        try:
            driver.get(self.LOGIN_URL)
            wait = WebDriverWait(driver, 30)
            
            userInput = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="username"]'))).send_keys(self.username)
            passInput = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="password"]'))).send_keys(self.password)
            loginButton = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="loginbtn"]'))).click()
            courseContainer = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@data-region="course-content"]')))
            
            aiohttp_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
            return [driver.page_source, aiohttp_cookies]
        except:
            return False
        
    async def loginRequest(self, session, params):
        async with session.post(self.LOGIN_URL, data=params) as response:
            print("[+] Login...")
            if (response.status == 200): return True
            else:
                return False

    async def getCourseUrls(self, response):
        htmlSource = BeautifulSoup(response, "html.parser")
        dashboardContent = htmlSource.find_all('div', class_="card dashboard-card") #type: ignore
        courseLinkIndentity = "https://e-learning.unpam.ac.id/course/view.php?id"
        courseList:list = []
        for content in dashboardContent:
            try:
                aElement = content.find('a', class_="aalink coursename mr-2 mb-1")
                if aElement != None:
                    courseUrl = str(aElement.get("href"))
                    courseName = aElement.find('span', class_="multiline")
                    if (courseUrl.find(courseLinkIndentity) != -1) and (courseName != None):
                        courseList.append({"courseName": courseName.text.replace("\n", ""), "courseUrl": courseUrl})
            except AttributeError: pass
        return courseList

    async def getDiscussUrls(self, session, url):
        async with session.get(url) as response:
            htmlSource = BeautifulSoup(await response.text(), 'html.parser')
            forumDiscussList = htmlSource.find_all('li', class_='activity activity-wrapper forum modtype_forum hasinfo')
            forumDiscussUrls:list = []
            for item in forumDiscussList:
                discussUrl = item.find('a', class_="aalink stretched-link")
                if (discussUrl): forumDiscussUrls.append(discussUrl['href'])
                else: forumDiscussUrls.append(None)
            return forumDiscussUrls

    async def findDiscussExistence(self, session, url):
        async with sem:
            async with session.get(url) as response:
                htmlSource = BeautifulSoup(await response.text(), 'html.parser')
                discussTable = htmlSource.find('table', class_='table discussion-list generaltable')
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
            courseData = htmlSource.find_all('li', class_="breadcrumb-item")
            print(courseData)
            if courseData:
                courseTitle = courseData[0].a['title']
                forumTitle = courseData[1].span.text
                return [courseTitle, forumTitle, url]

    async def main(self):
        res = self.loginBySelenium()
        if res:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), cookies=res[1]) as session:
                    print("[+] Getting course list...")
                    courseList = await asyncio.create_task(self.getCourseUrls(res[0]))
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
                            if discussUrl:
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
                        getTitleTasks.append(asyncio.create_task(self.getDiscussInfo(session, forumUrl)))
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
    print(asyncio.run(unpamChecker().main()))