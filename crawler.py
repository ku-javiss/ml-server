from convertor import Convertor
from queue import Queue
import re
import requests
from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
import threading
from convertor import Webpage
import time

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/100.0.4896.127 Safari/537.36'}


class Frontier:
    def __init__(self):
        self.permit_site_en = ['CNN', 'CNBC', 'Daily Mail', 'ESPN', 'Reuters', 'CBS Sports',
                               'Space.com', 'BBC', 'PEOPLE']
        self.naver_url = 'https://search.naver.com/search.naver?where=news&sm=tab_jum&query={}&start={}'
        self.youtube_url = 'https://www.google.com/search?q='
        self.googleNews = {'CNN': 'https\:\/\/www.cnn\.com',
                           'CNBC': 'https\:\/\/www.cnbc\.com',
                           'Daily Mail': 'https\:\/\/www.dailymail\.co\.uk',
                           'The Guardian': 'https\:\/\/www.theguardian\.com',
                           'ESPN': 'https\:\/\/www.espn\.com',
                           'Reuters': 'https\:\/\/www.reuters\.com',
                           'CBS Sports': 'https\:\/\/www.cbssports\.com',
                           'Space.com': 'https\:\/\/www.space\.com',
                           'BBC': 'https\:\/\/www\.bbc\.com',
                           'PEOPLE': 'https\:\/\/people\.com'}
        self.count = 0
        self.number = 0
        self.switch = False

    def getLinks(self, role, keyword, queue: Queue, number=1):
        if role == 'youtube':
            self.getYoutubeLinks(keyword, queue)
        elif role == 'news ko':
            self.getNewsLinkBySearch_Ko(keyword, queue, number)
        elif role == 'news en':
            self.getNewsLinkBySearch_En(keyword, queue, number)
        elif role == 'google search':
            self.getGoogleSearchLink(keyword, queue)

    def getNewsLinkBySearch_Ko(self, keyword, queue, number):
        keyword = re.sub(' ', '%20', keyword)
        count = 0
        non_sites = set()
        for i in range(1000):
            url = self.naver_url.format(keyword, (i*10 + 1))
            try:
                get_url = requests.get(url=url, headers=header)
            except HTTPError or URLError:
                break
            bs = BeautifulSoup(get_url.text, 'lxml')
            main_newses = bs.find_all('div', {'class': 'news_area'})
            sub_newses = bs.find_all('span', {'class': 'sub_wrap'})
            for main_news in main_newses:
                info = main_news.find('div', {'class': 'info_group'})
                site = info.find('a').text
                site = re.sub('언론사 선정', '', site)
                naver_link = info.find('a', href=re.compile('https\:\/\/news\.naver\.com\/'))
                if naver_link is not None:
                    naver_link = naver_link.attrs['href']
                else:
                    non_sites.add(site)
                main_link = main_news.find('a', {'class': 'news_tit'})
                title = main_link.attrs['title']
                main_link = main_link.attrs['href']
                article = Webpage(title=title, site=site, link=main_link, pass_url=naver_link, ko=True)
                # -------------------------------------Queue 추가--------------------------------------
                queue.put(article)
                count += 1
            for sub_news in sub_newses:
                site = sub_news.find('cite', {'class': 'sub_txt press'}).attrs['title']
                link = sub_news.find('a', {'class': 'elss sub_tit'})
                title = link.attrs['title']
                main_link = link.attrs['href']
                naver_link = sub_news.find('a', href=re.compile('https\:\/\/news\.naver\.com\/'))
                if naver_link is not None:
                    naver_link = naver_link.attrs['href']
                else:
                    non_sites.add(site)
                article = Webpage(title=title, site=site, link=main_link, pass_url=naver_link, ko=True)
                # -------------------------------------Queue 추가--------------------------------------
                queue.put(article)
                count += 1
            if count >= number:
                return

    def getYoutubeLinks(self, keyword, queue):
        keyword += 'site:youtube.com'
        keyword = re.sub(' ', '%20', keyword)
        url = self.youtube_url + keyword
        webpage = Webpage(title='Youtube link', site='Youtube', link=url)
        # -------------------------------------Queue 추가--------------------------------------
        queue.put(webpage)
        return

    def getNewsLinkBySearch_En(self, keyword, queue, number):
        self.switch = True
        self.number = number
        keyword = self.forth_processing(keyword)
        keyword = re.sub('\[cls\]', '', keyword)
        addition = [''] + self.permit_site_en
        for i in range(len(self.permit_site_en)+1):
            if addition[i] != '':
                keyword = addition[i] + '%20' + keyword
            url = 'https://news.google.com/search?q={}&hl=en-US&gl=US&ceid=US%3Aen'.format(keyword)
            try:
                get_url = requests.get(url=url, headers=header).text
            except HTTPError or URLError:
                continue
            bs = BeautifulSoup(get_url, 'lxml')
            bodys = bs.find('div', {'class': 'ajwQHc BL5WZb RELBvb'}).find_all('article')
            for body in bodys:
                if self.switch is False:
                    return
                content = body.find('h3')
                if content is None:
                    continue
                title = content.text
                link = content.find('a').attrs['href']
                link = re.sub('\.', 'https://news.google.com', link)
                site = body.find('a', {'class': 'wEwyrc AVN2gc uQIVzc Sksgp'}).text
                if site in self.permit_site_en:
                    new_site = Webpage(title=title, site=site, link=link)
                    t = threading.Thread(target=self.convertGoogleNews, args=(new_site, queue))
                    t.start()

    def convertGoogleNews(self, article: Webpage, queue):
        link = article.link
        get_url = requests.get(url=link, headers=header).text
        bs = BeautifulSoup(get_url, 'lxml')
        new_link = bs.find('a', href=re.compile(self.googleNews[article.site]))
        if new_link is not None:
            new_link = new_link.attrs['href']
            article.link = new_link
            p = re.compile('\/video\/')
            if p.search(article.link) is None:
                queue.put(article)
            self.count += 1
            if self.count >= self.number:
                self.switch = False
                self.count = 0
        else:
            if article.site == 'BBC':
                new_link = bs.find('a', href=re.compile('https\:\/\/www\.bbc\.co\.uk'))
                new_link = new_link.attrs['href']
                new_link = re.sub('\.co\.uk', '.com', new_link)
                article.link = new_link
                queue.put(article)
            if self.count >= self.number:
                self.switch = False
                self.count = 0

    def getGoogleSearchLink(self, keyword, queue):
        baseurl = "https://www.google.com/search?q="
        p = re.compile('^(what is )[A-Za-z0-9 ]+')
        if p.match(keyword) is not None:
            keyword += ' meaning'
        keyword = re.sub('\&', '%26', keyword)
        keyword = re.sub('\'', '%27', keyword)
        keyword = re.sub(' ', '+', keyword)
        url = baseurl+keyword
        print(url)
        webpage = Webpage(title='Google search link', site='google', link=url)
        queue.put(webpage)
        return

    def forth_processing(self, keyword):
        p = re.compile(
            '([tT]he |[oO]n |[aA][nN]* )*([aA][rR][tT][iI][cC][lL][eE][sS]*|[nN][eE][wW][sS])+( [aA]bout| [oO]f)*')
        c = list(p.findall(keyword))
        if len(c) > 0:
            for pattern in c:
                pattern = ''.join(list(pattern))
                keyword = re.sub(pattern, '', keyword)
        return keyword


class Crawler:
    def __init__(self):
        self.results = []
        self.url_queue = Queue()

    def startCrawl(self, role, keyword, number=1):
        start = time.time()
        frontier = Frontier()
        if role == 'youtube' or role == 'google search':
            number = 1
        t = threading.Thread(target=frontier.getLinks, args=(role, keyword, self.url_queue, number))
        t.start()
        count = 0
        threads = []
        while True:
            if not self.url_queue.empty():
                count += 1
                webpage = self.url_queue.get()
                t = threading.Thread(target=self.startConvertor, args=(webpage, ))
                t.start()
                threads.append(t)
            if (time.time()-start) > (number*0.3 + 1) or count > number:
                break
            time.sleep(0.0005)

        for thread in threads:
            thread.join()
        result_time = time.time()
        return self.results

    def startConvertor(self, webpage: Webpage):
        convertor = Convertor()
        result = convertor.extract_content(webpage)
        if result is not None:
            self.results.append(result)
