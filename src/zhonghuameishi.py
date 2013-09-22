#coding=utf-8
__author__ = 'Jacky'
class ZhongHuaMeiShi(BasicNewsRecipe):
    title = u'中华美食网'
    remove_tags_before = { 'class' : 'vcl-top' }
    remove_tags_after  = { 'class' : 'vcl-top' }
    publication_type = 'newspaper'
    articles=[]
    caishi={"粤菜系":"http://www.zhms.cn/Ms_menu/yue/cate",
            "川菜系":"http://www.zhms.cn/Ms_menu/chuan/cate",
            "湘菜系":"http://www.zhms.cn/Ms_menu/xiang/cate",
            "闽菜系":"http://www.zhms.cn/Ms_menu/min/cate",
            "鲁菜系":"http://www.zhms.cn/Ms_menu/shandong/cate",
            "浙菜系":"http://www.zhms.cn/Ms_menu/zhe/cate",
            "苏菜系":"http://www.zhms.cn/Ms_menu/shu/cate",
            "徽菜系":"http://www.zhms.cn/Ms_menu/hui/cate",
            "客家菜":"http://www.zhms.cn/Ms_menu/kejia/cate",
            "淮扬菜":"http://www.zhms.cn/Ms_menu/huai/cate",
            "潮州菜":"http://www.zhms.cn/Ms_menu/chaozhou/cate",
            "东北菜":"http://www.zhms.cn/Ms_menu/dongbei/catm"}
    def get_menus(self,soup):
        list=soup.findAll('ul',{'class':'vl-mlist'})[0].findAll('li')
        menus=[]
        for l in list:
            a=l.find('a')
            menu={'title':a['title'],'url':'http://www.zhms.cn'+a['href']}
            menus.append(menu)
            print(menu)
        return menus
    def get_index_by_url(self,key,url):
        soup=self.index_to_soup(url+".htm")
        pages= soup.findAll('cite')
        print pages
        for p in pages:
            fonts=p.findAll('font')
            if not fonts:
                print 'Nothing'
            else:
                pageSize=int(fonts[0].find('b').string)
                pageCount=int(fonts[1].find('b').string)
        print pageCount
        print pageSize
        print (pageCount+pageSize-1)//pageSize
        menus= self.get_menus(soup)
        for i in range(2,(pageCount+pageSize-1)//pageSize+1):
            soup=self.index_to_soup( url+'_'+str(i)+'.htm')
            menus.extend(self.get_menus(soup))
        self.articles.append(('%s(%i)'%(key,len(menus)),menus))
        print self.articles

    def parse_index(self):
        for key in self.caishi.keys():
            try:
                self.get_index_by_url(key,self.caishi[key])
            except Exception:
                  print Exception.message
        return self.articles




