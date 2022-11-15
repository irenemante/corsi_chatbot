import sanic
from sanic.response import html, text
from sanic.response import json as sjson
import json
import pandas as pd
import numpy as np


app = sanic.Sanic("test")

@app.post("/test")
async def test(request: sanic.Request):
    query = request.json
    newdf = pd.DataFrame(np.array([[1, query['duration'], 3], [4, query['keywords'], 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
    result = newdf.to_json(orient='values')
    parsd = json.loads(result)
    return sjson(parsd)
    

if __name__ == "__main__":
    app.run(port=8080, debug=True)
