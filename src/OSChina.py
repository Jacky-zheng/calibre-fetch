#coding=utf-8
'''
Created on 2013-8-21

@author: Jacky.Zheng
'''
import re
import time
class OSChina(BasicNewsRecipe):
    title = u'开源中国'
    auto_cleanup = True
    remove_tags_before = { 'class' : 'NewsBody' }
    remove_tags_after  = { 'class' : 'NewsBody' }
#    no_stylesheets = True
    publication_type = 'magazine'
    m_articles=[]
    m_maxPages=10
    def __init__(self, options, log, progress_reporter):
        BasicNewsRecipe.__init__(self, options, log, progress_reporter)
        options.max_recursions=0
        
    def parse_page_data(self,index):
        if index>self.m_maxPages:
            return False
        
        soup=self.index_to_soup(u'http://www.oschina.net/action/api/news_list?pageSize=50&catalog=2&pageIndex='+str(index))
        newslist=soup.findAll('news')
        size=len(newslist)
        if size==0:
            return False
        for news in newslist:
            tryCount=0;
            while tryCount<2:
                try:
                    self.log(news.title)
                    detailSoup=self.index_to_soup(u'http://www.oschina.net/action/api/news_detail?id='+news.id.string)
                    url=detailSoup.find('url').string.strip()
                    article={'title':news.title.string.strip(),'url':url,'description':news.title.string.strip()}
                    self.m_articles.append(article)
                    break
                except:
                    if tryCount==1:
                        self.log("can not download:"+news.id.string)
                    tryCount+=1
                    time.sleep(10)
                
            
        return True
        
    def parse_index(self):
        running=True
        index=0
        while running:
            running=self.parse_page_data(index)
            index+=1
        return [(u'综合资讯',self.m_articles)]


