import requests, feedparser, datetime, json, os

data = json.load(open(os.path.dirname(__file__)+'/ptrss.json'))
hash_list = data.get("hash_list", [])
data.update({"hash_list": []})

for i in data["rss_list"]:
    r = feedparser.parse(i)
    if not r.entries[0].guid in hash_list:
        torrent_link = r.entries[0].enclosures[0].href
    data["hash_list"].extend(list(i.guid for i in r.entries))

json.dump(data, open(os.path.dirname(__file__)+'/ptrss.json', 'w'), indent=2)

url = data.get("rpc_url")
username = data.get("username", '')
passwd = data.get("passwd", '')
headers = {"Authorization": "Basic {}".format(base64.b64encode('{}:{}'.format(username, passwd).encode("ascii")).decode("ascii"))}
r = requests.get(url, headers=headers)
headers.update({"X-Transmission-Session-Id": r.headers['X-Transmission-Session-Id']})

payload = '{"arguments": {"fields": ["id", "status", "doneDate"]}, "method": "torrent-get"}'
r = requests.post(url, data=payload, headers=headers).json()
ids = []
for i in r['arguments']['torrents']:
    if i['status'] == 4:
        exit()
    if i['status'] == 0:
        continue
    if (datetime.datetime.now().timestamp() - i["doneDate"]) > 3600 * 24 * data["seeding_days"]:
        ids.append(i['id'])
if ids:
    payload = json.dumps({"arguments": {"ids": ids, "delete-local-data": true}, "method": "torrent-remove"})
    r = requests.post(url, data=payload, headers=headers)

payload = json.dumps({"arguments": {"path": data["path"]}, "method": "free-space"})
r = requests.post(url, data=payload, headers=headers).json()
if r['arguments']['size-bytes']/1024/1024/1024 <= data["disk_free"]:
    exit()

if torrent_link:
    torrentAdd = json.dumps({"arguments": {"filename": torrent_link, "download-dir": data["path"]}, "method": "torrent-add"})
    r = requests.post(url, data=torrentAdd, headers=headers)
