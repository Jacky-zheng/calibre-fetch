#coding=utf-8
'''
Created on 2013-8-21

@author: Jacky.Zheng
'''
import re
import time
class OSChina(BasicNewsRecipe):
    title = u'开源中国'
    auto_cleanup = False
#    remove_tags_before = { 'class' : 'NewsBody' }
#    remove_tags_after  = { 'class' : 'NewsBody' }
#    no_stylesheets = True
    publication_type = 'newspaper'
    delay=2
    m_articles = []
    m_projects=[]
    m_blogs=[]
    m_translates=[]
    m_maxPages =1000
    max_articles_per_feed=100000
    def __init__(self, options, log, progress_reporter):
        BasicNewsRecipe.__init__(self, options, log, progress_reporter)
        options.max_recursions = 0
        
    def parse_page_data(self, index):
        if index > self.m_maxPages:
            return False
        
        soup = self.index_to_soup(u'http://www.oschina.net/action/api/news_list?pageSize=50&catalog=2&pageIndex=' + str(index))
        newslist = soup.findAll('news')
        size = len(newslist)
        if size == 0:
            return False
        for news in newslist:
            tryCount = 0;
            while tryCount < 2:
                try:
                    self.log(news.title)
                    detailSoup = self.index_to_soup(u'http://www.oschina.net/action/api/news_detail?id=' + news.id.string)
                    url = detailSoup.find('url').string.strip()
                    article = {'title':news.title.string.strip(), 'url':url, 'description':news.title.string.strip()}
                    if article['title'].find(u'【每日一博】')>-1:
                         self.m_blogs.append(article) 
                    elif article['title'].find(u'#翻译#')>-1:
                        self.m_translates.append(article)       
                    elif len(detailSoup.find('softwarelink').string.strip())>1:
                        self.m_projects.append(article)                        
                    else:    
                        self.m_articles.append(article)
                    break
                except:
                    if tryCount == 1:
                        self.log("can not download:" + news.id.string)
                    tryCount += 1
                    time.sleep(10)
                
            
        return True
        
    def parse_index(self):
        running=True
        index=0
        while running:
            running=self.parse_page_data(index)
            index+=1
            time.sleep(10)
#        article = {'title':u'使用消息队列的 10 个理由', 'url':u'http://www.oschina.net/translate/top-10-uses-for-message-queue', 'description':u'使用消息队列的 10 个理由'}
#        self.m_articles.append(article)
        items=[(u'综合资讯(%i)'%(len(self.m_articles)), self.m_articles)]
        if len(self.m_blogs)>0:
            items.append((u'每日一博(%i)'%(len(self.m_blogs)),self.m_blogs))
        if len(self.m_translates)>0:
            items.append((u'翻译(%i)'%(len(self.m_translates)),self.m_translates))
        if len(self.m_projects)>0:
            items.append((u'项目(%i)'%(len(self.m_projects)),self.m_projects))
        return items

    def preprocess_html(self, soup):
#        self.log(soup)
        try:
            tag = soup.find(**{ 'class' : 'NewsEntity' })
            self.process_normal_news(tag)
        except:
            self.log("process_normal_news")
        # 翻译
        try:
            tag = soup.find(**{ 'class' : 'Article' })
            self.process_translate_news(tag)
        except:
            self.log("process_translate_news") 
        try:          
            tag = soup.find(**{ 'class' : 'BlogEntity' })
            self.process_blog_news(tag)
        except:
            self.log("process_blog_news")
        try:            
            tag = soup.find(**{ 'class' : 'Body' })
            self.process_normal_news2(tag)
        except:
            self.log("process_normal_news2")        
#        self.log("preprocess_html")
#        self.log(soup)        
        return soup
    def process_normal_news2(self,tag):
         if tag is not None:
            detail=tag.find('div',{'class':'detail'})
            if detail is None:
                detail=tag.find('div',{'class':'detail TextContent'})
            self.remove_beyond(detail, 'nextSibling')
            self.remove_beyond(detail, 'previousSibling')
                   
    def process_normal_news(self,tag):
         if tag is not None:
            self.remove_beyond(tag, 'nextSibling')
            self.remove_beyond(tag, 'previousSibling')
            removed = tag.find('div', {'class':'NewsLinks'})
            if not removed is None:
               self.remove_beyond(removed, 'nextSibling')                 
                       
    def process_blog_news(self,tag):
        if tag is not None:
            self.remove_beyond(tag, 'nextSibling')
            self.remove_beyond(tag, 'previousSibling')
            removed = tag.find('div', {'class':'BlogLinks'})
            if not removed is None:
                removed.extract()   
            removed = tag.find('div', {'class':'BlogCopyright'})
            if not removed is None:
                removed.extract()                   
            
    def process_translate_news(self, tag):
            if tag is not None:
                self.remove_beyond(tag, 'nextSibling')
                self.remove_beyond(tag, 'previousSibling')
                removed = tag.find('div', {'class':'Vote'})
                if not removed is None:
                    removed.extract()
                removed = tag.find('div', {'class':'toolbar'})
                if not removed is None:
                    removed.extract()
                removed = tag.find('div', {'class':'Bottom'})
                if not removed is None:
                    removed.extract()
                for p in tag.findAll(attrs={"class": "translate_chs"}):
                    table = p.find('table')
                    if table is None:
                        continue
                    content = str(table.find('div', {'class':'TextContent'}))
                    [child.extract() for child in p.findAll(True)]
                    s = BeautifulSoup(content)
                    p.append(s)    
        
    def remove_beyond(self, tag, next):
        while tag is not None and getattr(tag, 'name', None) != 'body':
             after = getattr(tag, next)
             while after is not None:
                  ns = getattr(tag, next)
                  after.extract()
                  after = ns
             tag = tag.parent        
