import torch
import json
from sentence_transformers import SentenceTransformer
import pandas as pd
from sanic.response import html
from sanic.response import text
from sanic.response import json as sjson
from sanic.request import Request
import re
import sanic
import os
import requests

app = sanic.Sanic("RSapp")

app.static(
    "/csv",
    "D:\dataset\SanicRS",
    name="csv",
)

@app.before_server_start
async def startup(self, app):
    #pre generate corpus encodings with bert saved to a dataframe
    global tensordf
    global embedder
    global queryable_df
    global merlot_df
    global format_mapping
    dir = os.getcwd()
    embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
    merlot_df = pd.read_csv(f'{dir}/merlot.csv', sep=';')
    merlot_df.drop_duplicates(subset='link')

    queryable_df = merlot_df[['disciplines', 'duration', 'keywords', 'language', 'public', 'type']]
    merlot_df = merlot_df[['link', 'title', 'language', 'public']]

    durations = [str(x) for x in queryable_df['duration'].to_list()]

    discipline_encoding = embedder.encode(queryable_df['disciplines'].to_list(), convert_to_tensor=True)
    duration_encoding = embedder.encode(durations, convert_to_tensor=True)
    keywords_encoding = embedder.encode(queryable_df['keywords'].to_list(), convert_to_tensor=True)

    tuples = list(zip(discipline_encoding, keywords_encoding, duration_encoding))

    tensordf = pd.DataFrame(tuples, columns=['discipline_en', 'keywords_en', 'duration_en'])

    format_mapping = {
        "videolezioni": ["presentation", "animation", "online course", "online course module", "tutorial", "simulation"],
        "esercizi": ["drill and practice", "assessment tool", "assignment", "workshop and training material"],
        "quiz": ["quiz/test"],
        "documenti": ["reference material", "open (access) textbook", "case study", "open (access) journal-article"]
        }
    print("Server Online")
    return

@app.get("/online")
async def online(request):
    return text("Online")



@app.route("/recommend", methods=["POST"])
async def recommend_handler(request):
    query = request.json
    query["language"] = query["language"].capitalize()
    if query["request_type"] == "recommend":
        #generate user query encoding with bert
        user_discipline_encoding = embedder.encode(query['discipline'], convert_to_tensor=True)
        user_keywords_encoding = embedder.encode(', '.join(query['keywords']), convert_to_tensor=True)
        user_duration_encoding = embedder.encode(query['duration'], convert_to_tensor=True)

        
        #calculate cosine similarity between metadata
        cossim = torch.nn.CosineSimilarity(0, 1e-6)
        queryable_df['cos_sim_disc'] = tensordf['discipline_en'].apply(lambda x: cossim(x, user_discipline_encoding))
        queryable_df['cos_sim_keyw'] = tensordf['keywords_en'].apply(lambda x: cossim(x, user_keywords_encoding))
        queryable_df['cos_sim_dur'] = tensordf['duration_en'].apply(lambda x: cossim(x, user_duration_encoding))
        #filter for language since it should be definitive not similar, also account for format
        merlot_df_ln_filtered = queryable_df.loc[queryable_df['language'].str.contains(query['language'])]
        merlot_df_ln_filtered['public'] = queryable_df['public']
        merlot_df_ln_filtered['type'] = queryable_df['type']
        #filter for public not implemented in chatbot yet
        merlot_df_ln_filtered = merlot_df_ln_filtered.loc[merlot_df_ln_filtered['public'].str.contains(query['public'])]
        print(merlot_df_ln_filtered.head(10))
        #4 if to filter for format type
        if query['type'] == "videolezioni":
            merlot_df_ln_filtered = merlot_df_ln_filtered.loc[merlot_df_ln_filtered['type'].str.contains("presentation|animation|online courses|online course module|tutorial|simulation", flags=re.IGNORECASE, regex=True)]
        elif query['type'] == "quiz":
            merlot_df_ln_filtered = merlot_df_ln_filtered.loc[merlot_df_ln_filtered['type'].str.contains("quiz/test", flags=re.IGNORECASE, regex=True)]
        elif query['type'] == "esercizi":
            merlot_df_ln_filtered = merlot_df_ln_filtered.loc[merlot_df_ln_filtered['type'].str.contains("drill and practice|assessment tool|assignment|workshop and training material", flags=re.IGNORECASE, regex=True)]
        elif query['type'] == "documenti":
            merlot_df_ln_filtered = merlot_df_ln_filtered.loc[merlot_df_ln_filtered['type'].str.contains("reference material|open (access) textbook|case study|open (access) journal-article", flags=re.IGNORECASE, regex=True)]
        print(merlot_df_ln_filtered.head(10))





        merlot_df['SCORE'] = merlot_df_ln_filtered[['cos_sim_disc', 'cos_sim_keyw', 'cos_sim_dur']].mean(axis=1)

        #sort the results
        printable_df = merlot_df[['title', 'link', 'language', 'public', 'SCORE']]
        printable_df= printable_df.sort_values(by=['SCORE'], ascending=False)

        #format the results 
        global result
        result = printable_df[['title', 'link', 'SCORE']].head(15)
        result = result.to_json(orient='values')
        parsed = json.loads(result)
    return sjson(parsed)




@app.route("/frontpage", methods=['GET'])
def index(request):
    dir = os.getcwd()
    template = open(f'{dir}/jwt.html')
    return html(template.read())
    
    





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True, auto_reload=True)

