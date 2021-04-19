from requests import get, post, put, delete


stat = "http://127.0.0.1:5000" + '/api/v2/shops/2'


s = get(stat)
print(s.json())