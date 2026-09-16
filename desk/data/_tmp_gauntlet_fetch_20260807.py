import urllib.request, json, sys

hdr = {'User-Agent': 'ajay research 4tripathy@gmail.com'}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30).read()

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'index':
        for cik, acc in [(30697, '000119312526339132'), (2090312, '000209031226000013')]:
            url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json'
            try:
                d = json.loads(get(url))
                print('=====', cik, acc)
                for it in d['directory']['item']:
                    print(' ', it['name'], it.get('last-modified', ''))
            except Exception as e:
                print('ERR', cik, acc, repr(e))
    elif mode == 'fetch':
        url = sys.argv[2]
        out = sys.argv[3]
        with open(out, 'wb') as f:
            f.write(get(url))
        print('saved', out)
