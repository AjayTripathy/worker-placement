import urllib.request, json, sys

hdr = {'User-Agent': 'ajay research 4tripathy@gmail.com'}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30).read()

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'index':
        for cik, acc in [(1032220, '000103222026000033'), (1794669, '000179466926000042')]:
            url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json'
            d = json.loads(get(url))
            print('=====', cik)
            for it in d['directory']['item']:
                print(it['name'], it.get('last-modified', ''))
    elif mode == 'fetch':
        url = sys.argv[2]
        out = sys.argv[3]
        with open(out, 'wb') as f:
            f.write(get(url))
        print('saved', out)
