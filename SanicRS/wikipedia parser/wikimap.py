import requests
 
# insert data
data = []
mapped = {
    "ID": [],
    "Query" : [],
    "Mapped Article" : [],
    "Article link" : []
}
counter = 0
for item in data:

    searchable = str(item)
    params = {
        "action" : "query",
        "format" : "json",
        "list" : "allpa",
        "srsearch" : searchable
    }
    response = requests.Session().get("https://en.wikipedia.org/w/api.php", params)
    mapped["ID"].append(counter)
    mapped["Query"].append(item)
    mapped["Mapped Article"].append(response.json()['query']['search'][0]['title'])
    mapped["Article link"].append(response.json)