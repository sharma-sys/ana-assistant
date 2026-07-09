pib = open('collectors/pib_news.py', encoding='utf-8').read()

nat = pib.replace('PibNewsCollector','NationalNewsCollector').replace('rss_pib','rss_national').replace('PIB News Collector','National News Collector')
open('collectors/national_news.py','w',encoding='utf-8').write(nat)

state = pib.replace('PibNewsCollector','StateNewsCollector').replace('rss_pib','rss_state').replace('PIB News Collector','State News Collector').replace('district="All"','state=source.state')
open('collectors/state_news.py','w',encoding='utf-8').write(state)

# For Google News, we'll just use a basic one that filters for google_news
goog = pib.replace('PibNewsCollector','GoogleNewsCollector').replace('rss_pib','google_news').replace('PIB News Collector','Google News Collector')
open('collectors/google_news.py','w',encoding='utf-8').write(goog)
