'''
Created on 2013-8-19

@author: Jacky Zheng
'''
import re
from calibre.ebooks.BeautifulSoup import NavigableString
from calibre.web.fetch.simple import RecursiveFetcher
import sys, socket, os, urlparse, re, time, copy, urllib2, threading, traceback
from urllib import url2pathname, quote
from httplib import responses
from base64 import b64decode

from calibre import browser, relpath, unicode_path, fit_image
from calibre.constants import filesystem_encoding, iswindows
from calibre.utils.filenames import ascii_filename
from calibre.ebooks.BeautifulSoup import BeautifulSoup, Tag
from calibre.ebooks.chardet import xml_to_unicode
from calibre.utils.config import OptionParser
from calibre.utils.logging import Log
from calibre.utils.magick import Image
from calibre.utils.magick.draw import identify_data, thumbnail
from calibre.utils.imghdr import what

def save_soup(soup, target):
    ns = BeautifulSoup('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />')
    nm = ns.find('meta')
    metas = soup.findAll('meta', content=True)
    added = False
    for meta in metas:
        if 'charset' in meta.get('content', '').lower():
            meta.replaceWith(nm)
            added = True
    if not added:
        head = soup.find('head')
        if head is not None:
            head.insert(0, nm)

    selfdir = os.path.dirname(target)

    for tag in soup.findAll(['img', 'link', 'a']):
        for key in ('src', 'href'):
            path = tag.get(key, None)
            if path and os.path.isfile(path) and os.path.exists(path) and os.path.isabs(path):
                tag[key] = unicode_path(relpath(path, selfdir).replace(os.sep, '/'))

    html = unicode(soup)
    with open(target, 'wb') as f:
        f.write(html.encode('utf-8'))
        
class InspiredFetcher(RecursiveFetcher):
    extra_css = '''
.posts {
min-height: 650px;
}
    
.posts .post {
display: inline-block;
vertical-align: top;
margin: 0px 22px 50px 0px;
}
    
.post .post-frame {
position: relative;

border-bottom-width: 0px;
height: 480px;
width: 320px;

}
.post .post-frame .post-img {
margin: 0;
padding: 0;
max-width: 100%;
max-height: 100%;
}
    '''
    def __init__(self, options, log, image_map={}, css_map={}, job_info=None):
        RecursiveFetcher.__init__(self, options, log, image_map, css_map, job_info)

    def process_articles(self, title, article, baseurl, into_dir='links'):
          res = ''
          diskpath = os.path.join(self.current_dir, into_dir)
          '''
          必须添加Elemnt 的 Class ,否则框架会自动添加
          '''
          html = "<html><head><title>" + title + "</title><style type='text/css'>" + self.extra_css + "</style></head><body><div class='posts'>"
          for a in article:
              if self.show_progress:
                  print '.',
                  sys.stdout.flush()
              sys.stdout.flush()
#              self.log("article:"+str(a))
              html += "<div class='post'><div class='post-frame'><img src='" + a['href'] + "' class='post-img'></img><span>"+a['tags']+"</span></div>"
              html += "</div>"
          html += "</div></body></html>"
          soup = BeautifulSoup(html)
          self.log.debug('Processing images...')
          try:
              self.process_images(soup, baseurl)
          except Exception:
              self.lof('Exception')
          finally:    
             self.log('end processing images')
          _fname = title
          if not isinstance(_fname, unicode):
              _fname.decode('latin1', 'replace')
          _fname = _fname.encode('ascii', 'replace').replace('%', '').replace(os.sep, '')
          _fname = ascii_filename(_fname)
          _fname = os.path.splitext(_fname)[0] + '.xhtml'
          res = os.path.join(diskpath, _fname)
          self.downloaded_paths.append(res)
          nurl = baseurl + title
          self.filemap[nurl] = res      
          save_soup(soup, res)  
          self.downloaded_paths.append(res)
          return res 

    def start_fetch(self, url, title, article):
       self.log.debug('Downloading')
       res = self.process_articles(title, article, url, into_dir='')
       self.log.debug(url, 'saved to', res)
       return res              
   
    def _absurl(self, baseurl, url , filter=True):
        iurl = url
        parts = urlparse.urlsplit(iurl)
        if not parts.netloc and not parts.path and not parts.query:
            return None
        if not parts.scheme:
            iurl = urlparse.urljoin(baseurl, iurl, False)
        if not self.is_link_ok(iurl):
            self.log.debug('Skipping invalid link:', iurl)
            return None
        if filter and not self.is_link_wanted(iurl, tag):
            self.log.debug('Filtered link: ' + iurl)
            return None
        return iurl   

class Inspired(BasicNewsRecipe):
    title = u'Inspired'
    auto_cleanup = True 
    m_tags = {}
    m_apps = {}
    max_pages = 300
    def parse_tag(self, tags, href, itune):
        self.log("parse_tag:" + tags)
        for tag in tags.split("|"):
            tag = tag.strip()
            index = tag.find('app ')
            if len(tag) > 0:
                if index > -1:
                    if not self.m_apps.has_key(tag):
                        self.m_apps[tag] = []
                    self.m_apps[tag].append({'href':href, 'itune':itune, 'tags':tags})    
                else:                        
                    if not self.m_tags.has_key(tag):
                        self.m_tags[tag] = []      
                    self.m_tags[tag].append({'href':href, 'itune':itune, 'tags':tags})
                    
    def parse_page_data(self, index):
        if index >= self.max_pages:
            return False
        self.log("start parse article index"+str(index)) 
        soup = self.index_to_soup(u'http://inspired-ui.com/page/' + str(index))
        self.title = soup.html.head.title.string.strip()
        maincontent = soup.find('section', {'class':'posts'})
        for link in maincontent.findAll('div', {'class':'post'}):
            image = link.find('img', {'id':'post-img'})
            tag = link.findAll('span')[0]
            a = link.find('div', {'class':'caption'}).findAll('a')
            itune = ''
            if len(a) > 0:
                itune = a[0]['href']
            if not tag.string:
              self.log.debug("can not process:"+str(index)+" "+str(link))
            else:  
                self.parse_tag(tag.string, image['src'], itune)
       
        pagination = soup.find('div', {'class':'pagination'})
        if not pagination:
            return False
        if index==1:
            return len(pagination.findAll('a')) ==1 
        return len(pagination.findAll('a')) > 1 
                                 
    def parse_index(self):
        '''
        生成文章列表
        '''
        running = True
        index = 1
        while running:
            running = self.parse_page_data(index)
            index += 1
        self.log(self.m_tags)
        self.log("start generat article index") 
        self.log(self.m_apps)
        removed = [] 
        for tag in self.m_tags.keys():
            if self.m_apps.has_key('app ' + tag):
                removed.append(tag)
        for tag in removed:
            del self.m_tags[tag]        
        article_list = []
        for key in self.m_tags.keys():
            a = {'title':key + '(' + str(len(self.m_tags[key])) + ')', 'url':key, 'description':key}
            article_list.append(a)
        
        app_list=[]
        for key in self.m_apps.keys():
            a = {'title':key + '(' + str(len(self.m_apps[key])) + ')', 'url':key, 'description':key}
            app_list.append(a)
        self.log("end parse_index")  
        self.log(self.m_apps) 
        self.log("app list:"+str(app_list)) 
        return [('tags', article_list),('Applications:',app_list)]
    
    def fetch_article(self, url, dir, f, a, num_of_feeds):
        '''
        生成文章
        '''
        br = self.browser
        if self.get_browser.im_func is BasicNewsRecipe.get_browser.im_func:
            # We are using the default get_browser, which means no need to
            # clone
            br = BasicNewsRecipe.get_browser(self)
        else:
            br = self.clone_browser(self.browser)
        self.web2disk_options.browser = br
        fetcher = InspiredFetcher(self.web2disk_options, self.log,
                self.image_map, self.css_map,
                (url, f, a, num_of_feeds))
        fetcher.browser = br
        fetcher.base_dir = dir
        fetcher.current_dir = dir
        fetcher.show_progress = False
        fetcher.image_url_processor = self.image_url_processor
        self.log("start fetch article")
#        self.log("url:" + url)
#        self.log("f:"+str(f))
#        self.log("a:"+str(a))
#        self.log("num:"+str(num_of_feeds))
        if f==0:
            article=self.m_tags[url]
        else:
           article=self.m_apps[url]
        res, path, failures = fetcher.start_fetch('http://inspired-ui.com/', url, article), fetcher.downloaded_paths, fetcher.failed_links
        if not res or not os.path.exists(res):
            msg = _('Could not fetch article.') + ' '
            if self.debug:
                msg += _('The debug traceback is available earlier in this log')
            else:
                msg += _('Run with -vv to see the reason')
            raise Exception(msg)
        return res, path, failures
        

