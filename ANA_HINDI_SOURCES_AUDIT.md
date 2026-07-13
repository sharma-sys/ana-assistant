# ANA Hindi News Sources Audit Report

## Overview
- **Total sources before execution:** 52
- **Total sources after execution:** 62
- **Net sources added:** 10

## Newly Added Sources
- **Live Hindustan** (National - National)
  - Config Type: `scraper_national`
  - URL: https://www.livehindustan.com/
- **Navbharat Times** (National - National)
  - Config Type: `rss_national`
  - URL: https://navbharattimes.indiatimes.com/langapi/sitemap/gstandrssfeed/1217647547.xml
- **Jansatta Hindi** (National - National)
  - Config Type: `scraper_national`
  - URL: https://www.jansatta.com/
- **Punjab Kesari** (National - National)
  - Config Type: `scraper_national`
  - URL: https://www.punjabkesari.in/
- **Prabhat Khabar** (National - National)
  - Config Type: `scraper_national`
  - URL: https://www.prabhatkhabar.com/
- **Haribhoomi** (National - National)
  - Config Type: `scraper_national`
  - URL: https://www.haribhoomi.com/
- **ETV Bharat Hindi** (Regional - Multiple)
  - Config Type: `scraper_regional`
  - URL: https://www.etvbharat.com/hindi/national
- **Khabar Lahariya** (Regional - Uttar Pradesh)
  - Config Type: `scraper_regional`
  - URL: https://khabarlahariya.org/
- **First Bihar Jharkhand** (Regional - Bihar)
  - Config Type: `rss_regional`
  - URL: https://firstbihar.com/feed.xml
- **Chhattisgarh Today** (Regional - Chhattisgarh)
  - Config Type: `scraper_regional`
  - URL: https://chhattisgarhtoday.in/

## Skipped Duplicate Sources
- **Amar Ujala** (https://www.amarujala.com/)
- **News18 Hindi** (https://hindi.news18.com/)
- **ABP News Hindi** (https://www.abplive.com/)
- **Aaj Tak** (https://www.aajtak.in/)
- **TV9 Bharatvarsh** (https://www.tv9hindi.com/)
- **Zee News Hindi** (https://zeenews.india.com/hindi)
- **India TV Hindi** (https://www.indiatv.in/)
- **Webdunia Hindi** (https://hindi.webdunia.com/)
- **MP Breaking News** (https://mpbreakingnews.in/)

## Sources Skipped Due to Restrictions (No RSS & Blocked Scraper)
- **NDTV India** (https://ndtv.in/)
  - Reason: `403 Client Error: Forbidden for url: https://ndtv.in/`
- **Rajasthan Tak** (https://rajasthan.tak.live/)
  - Reason: `HTTPSConnectionPool(host='rajasthan.tak.live', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='rajasthan.tak.live', port=443): Failed to resolve 'rajasthan.tak.live' ([Errno 11001] getaddrinfo failed)"))`
- **Bihar Tak** (https://bihar.tak.live/)
  - Reason: `HTTPSConnectionPool(host='bihar.tak.live', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='bihar.tak.live', port=443): Failed to resolve 'bihar.tak.live' ([Errno 11001] getaddrinfo failed)"))`
- **UP Tak** (https://up.tak.live/)
  - Reason: `HTTPSConnectionPool(host='up.tak.live', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='up.tak.live', port=443): Failed to resolve 'up.tak.live' ([Errno 11001] getaddrinfo failed)"))`
