1.API:http://manual.calibre-ebook.com/news_recipe.html#calibre.web.feeds.news.BasicNewsRecipe.download
2.https://github.com/JeffreyZhao/calibre-recipes/
3.http://blog.zhaojie.me/2013/06/calibre-recipe-infoq.html
4.流程：
a)获取要下载的文章列表，每一项要包括，url,title，description(必须，不然会报错)
b)调用 RecursiveFetcher 
    fetch_start
    process_links
    process_images
    global.save_soup
    