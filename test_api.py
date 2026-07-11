import urllib.request, urllib.error

req = urllib.request.Request('https://ana-assistant.onrender.com/api/news/fetch', method='POST')
req.add_header('X-API-Key', 'ana_secure_dev_key_2026')
try:
    res = urllib.request.urlopen(req)
    print('SUCCESS', res.read().decode())
except urllib.error.HTTPError as e:
    print('ERROR', e.code, e.read().decode())
