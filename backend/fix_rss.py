pib = open('collectors/pib_news.py', encoding='utf-8').read()
rss = pib.replace('PibNewsCollector','GenericRssCollector').replace('rss_pib','rss').replace('PIB News Collector','Generic RSS Collector').replace('district="All"','district=source.district')
open('collectors/rss.py','w',encoding='utf-8').write(rss)
