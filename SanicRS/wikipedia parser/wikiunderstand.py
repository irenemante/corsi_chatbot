import requests
import json

searchable = "Nelson Mandela"
params = {
    "action" : "query",
    "format" : "json",
    "list" : "search",
    "srsearch" : searchable
}
response = requests.Session().get(url="https://en.wikipedia.org/w/api.php", params= params)

dict = response.json()
f = open("queryed.json", "w")
f.write(json.dumps(dict, indent=4))
