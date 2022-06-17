import re
import requests
from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/100.0.4896.127 Safari/537.36'}


class Webpage:
    def __init__(self, title, site, link, pass_url=None, ko=False):
        self.title = title
        self.link = link
        self.site = site
        self.pass_url = pass_url
        self.ko = ko


class Convertor:
    def __init__(self):
        self.extract_tag_ko = {'시사포커스': '#article-view-content-div > p',
                               '데일리한국': '#article-view-content-div',
                               '뉴데일리': '#article_conent > span',
                               '인사이트': 'body > div.content > div > div.news-container > div.news-wrap > '
                                       'div.news-article > div.news-article-memo > p',
                               '신아일보': '#article-view-content-div'}
        cnn_extract_tag = {'role': 'article',
                           'title': 'body > div.pg-right-rail-tall.pg-wrapper > article > div.l-container > h1',
                           'content': '#body-text'}
        cnbc_extract_tag = {'role': 'article',
                            'title': '#main-article-header > div > div.ArticleHeader-wrapperHeroNoImage.ArticleHeader'
                                     '-wrapperHero.ArticleHeader-wrapper.ArticleHeader-wrapperNoImage > '
                                     'div:nth-child(2) > h1',
                            'content': '#SpecialReportArticle-ArticleBody-6 > div.group'}
        dm_extract_tag = {'role': 'article',
                          'title': '#js-article-text > h2',
                          'content': '#js-article-text'}
        guardian_extract_tag = {'role': 'article',
                                'title': 'body > main > article > div > div > div.dcr-1nupfq9',
                                'content': 'body > main > article > div > div > div.dcr-185kcx9'}
        espn_extract_tag = {'role': 'article',
                            'title': '#article-feed > article:nth-child(1) > div > header',
                            'content': '#article-feed > article:nth-child(1) > div > div.article-body > p'}
        reuters_extract_tag = {'role': 'article',
                               'title': '#main-content > article > div > header > div > '
                                        'div.article-header__heading__15OpQ > h1',
                               'content': '#main-content > article > div > div > div > '
                                          'div.article-body__content__17Yit.paywall-article > p'}
        cbssports_extract_tag = {'role': 'article',
                                 'title': '#article0 > article > div.Article-head > h1',
                                 'content': '#Article-body > div.Article-bodyContent > p'}
        spacecom_extract_tag = {'role': 'article',
                                'title': '#main > article > header > h1',
                                'content': '#article-body > p'}
        bbc_extract_tag = {'role': 'article',
                           'title': '#main-heading',
                           'content': '#main-content > div.ssrcss-1ocoo3l-Wrap.e42f8511 > div > '
                                      'div.ssrcss-rgov1k-MainColumn.e1sbfw0p0 > article'}
        people_extract_tag = {'role': 'article',
                              'title': 'body > div.container-full-width.clearfix.template-two-col.karma-below-banner'
                                       '.with-sidebar-right.karma-below-banner.karma-site-container > main > article '
                                       '> div.articleContainer.karma-sticky-grid > div.articleContainer__header > div '
                                       '> div.intro.article-info > div > h1',
                              'content': 'body > div.container-full-width.clearfix.template-two-col.karma-below'
                                         '-banner.with-sidebar-right.karma-below-banner.karma-site-container > main > '
                                         'article > div.articleContainer.karma-sticky-grid'}
        youtube_extract_tag = {'role': 'youtube', 'content': '#search'}
        self.extract_tag_en = {'Youtube': youtube_extract_tag,
                               'CNN': cnn_extract_tag,
                               'CNBC': cnbc_extract_tag,
                               'Daily Mail': dm_extract_tag,
                               'The Guardian': guardian_extract_tag,
                               'ESPN': espn_extract_tag,
                               'Reuters': reuters_extract_tag,
                               'CBS Sports': cbssports_extract_tag,
                               'Space.com': spacecom_extract_tag,
                               'BBC': bbc_extract_tag,
                               'PEOPLE': people_extract_tag}

    def extract_content(self, webpage: Webpage):
        print('extract content: {}'.format(webpage.link))
        if webpage.title == 'Google search link':
            return self.extract_Google_Search(webpage)
        if webpage.ko:
            return self.extract_Article_Ko(webpage)
        try:
            get_url = requests.get(url=webpage.link, headers=header).text
        except HTTPError or URLError:
            return
        bs = BeautifulSoup(get_url, 'lxml')
        extract_tag = self.extract_tag_en[webpage.site]
        if extract_tag['role'] == 'article':
            title = bs.select(extract_tag['title'])
            bodies = bs.select(extract_tag['content'])
            if webpage.site == 'Daily mail':
                bodies = bodies[0].find('div', {'itemprop': 'articleBody'}).find_all('p')
            elif webpage.site == 'BBC':
                if len(bodies) > 0:
                    divs = bodies[0].find_all('div', {'data-component': 'text-block'})
                    bodies = []
                    for div in divs:
                        bodies.append(div.find('p'))
                else:
                    article = bs.find('article')
                    title = [article.find('h1')]
                    ps = article.find_all('p')
                    bodies = []
                    for p in ps:
                        bodies.append(p)
            elif webpage.site == 'PEOPLE':
                divs = bodies[0].find_all('div', {'class': 'articleContainer__content'})
                bodies = []
                for div in divs:
                    ps = div.find_all('p')
                    if len(ps) == 0:
                        continue
                    for p in ps:
                        bodies.append(p)
            if len(title) == 0:
                return
            if len(bodies) == 0:
                return
            title = title[0].text
            content = ''
            for body in bodies:
                content += body.text + ' '
            content = self.preprocessingArticle(content)
            title = self.preprocessingArticle(title)
            temp = {'site': webpage.site, 'title': title, 'content': content}
            return temp
        elif extract_tag['role'] == 'youtube':
            content = bs.select(extract_tag['content'])
            content = content[0].find('a', href=re.compile('https\:\/\/www.youtube\.com'))
            if content is not None:
                content = content.attrs['href']
                p = re.compile('https://www.youtube.com/channel/[a-zA-Z0-9]+|https://www.youtube.com/c/[a-zA-Z0-9]+')
                if p.search(content) is not None:
                    return "None"
            return content
        elif extract_tag['role'] == 'wiki':
            return self.extract_wikipedia(webpage)


    @staticmethod
    def preprocessingArticle(content):
        content = re.sub('\n|\xa0|\t', '', content)
        content = re.sub('  ', '', content)
        content.replace("\\", "")
        return content

    def extract_Article_Ko(self, article: Webpage):
        title = article.title
        if article.pass_url is not None:
            url = article.pass_url
            try:
                get_url = requests.get(url=url, headers=header)
            except HTTPError or URLError:
                return
            bs = BeautifulSoup(get_url.text, 'lxml')
            content = bs.find('div', id='dic_area')
            unexpects = [content.find('strong')] + content.find_all('span', {'class': 'end_photo_org'})
            for exception in unexpects:
                if exception is not None:
                    exception.extract()
            content = content.text
            for i in range(2):
                content = re.sub('  ', ' ', content)
            content = re.sub('\n|\t|\xa0', ' ', content)
            return {'site': article.site, 'title': title, 'content': content}
        else:
            url = article.link
            try:
                get_url = requests.get(url=url, headers=header)
            except HTTPError or URLError:
                return
            bs = BeautifulSoup(get_url.text, 'lxml')
            if article.site in self.extract_tag_ko:
                bodys = bs.select(self.extract_tag_ko[article.site])
            else:
                return None
            if article.site == '신아일보':
                bodys = bodys[0].find_all('p')
            content = ''
            for body in bodys:
                content += body.text
            for i in range(2):
                content = re.sub('  ', ' ', content)
            content = re.sub('\n|\t|\xa0', ' ', content)
            return {'site': article.site, 'title': title, 'content': content}

    def extract_Google_Search(self, webpage: Webpage):
        try:
            get_url = requests.get(url=webpage.link, headers=header).text
        except HTTPError or URLError:
            return
        bs = BeautifulSoup(get_url, 'lxml')
        recommends = bs.find_all('span', {'class': 'hgKElc'})
        if len(recommends) > 0:
            print("!")
            recommend = recommends[0]
            emphasis = recommend.find('b')
            answer = recommend.text
            if emphasis is not None:
                emphasis = emphasis.text
                return [emphasis, answer]
            else:
                return [answer]
        search = bs.find(id='search')
        if search is not None:
            recommend = search.find('div', {'data-tts:' 'answer'})
        if recommend is not None:
            emphasis = recommend.find('b')
            answer = recommend.text
            if emphasis is not None:
                emphasis = emphasis.text
                return [emphasis, answer]
            else:
                return [answer]
        if search is not None:
            meaning = search.find('div', {'class': 'thODed'})
        if meaning is not None:
            answer = meaning.find('span').text
            return [answer]
        answer = bs.find('a', {'class', 'FLP8od'})
        if answer is not None:
            answer = answer.text
            return [answer]
        if search is not None:
            answer = search.find('div', {'class': 'BRoiGe'})
            if answer is not None:
                return answer.text
        # 차선책: 검색 결과 링크
        search_results = []
        results = bs.find_all('div', {'class': 'g tF2Cxc'})
        for result in results:
            link = result.find('a')
            attrs = link.attrs['href']
            title = link.find('h3').text
            search_results.append((title, attrs))
        return search_results
