import torch
import json
from sentence_transformers import SentenceTransformer
import pandas as pd
from sanic.response import html
from sanic.response import text
from sanic.request import Request
import sanic

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
    embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
    merlot_df = pd.read_csv('D:\dataset\SanicRS\merlot.csv', sep=';')
    merlot_df.drop_duplicates(subset='link')

    queryable_df = merlot_df[['disciplines', 'duration', 'keywords', 'language', 'public']]
    merlot_df = merlot_df[['link', 'title', 'public','language']]

    durations = [str(x) for x in queryable_df['duration'].to_list()]

    discipline_encoding = embedder.encode(queryable_df['disciplines'].to_list(), convert_to_tensor=True)
    duration_encoding = embedder.encode(durations, convert_to_tensor=True)
    keywords_encoding = embedder.encode(queryable_df['keywords'].to_list(), convert_to_tensor=True)

    tuples = list(zip(discipline_encoding, keywords_encoding, duration_encoding))

    tensordf = pd.DataFrame(tuples, columns=['discipline_en', 'keywords_en', 'duration_en'])
    print("Server Online")
    return

@app.get("/online")
async def online(request):
    return text("Online")



@app.route("/recommend", methods=["POST"])
async def recommend_handler(request):
    query = request.json
    if query["request_type"] == "recommend":
        #generate user query encoding with bert
        user_discipline_encoding = embedder.encode(query['discipline'], convert_to_tensor=True)
        user_keywords_encoding = embedder.encode(', '.join(query['keywords']), convert_to_tensor=True)
        user_duration_encoding = embedder.encode(query['duration'], convert_to_tensor=True)

        #filter for language since it should be definitive not similar
        merlot_df_ln_filtered = queryable_df.loc[queryable_df['language'].str.contains(query['language'])]
        print(merlot_df_ln_filtered.head)
        #filter for public
        merlot_df_ln_filtered = merlot_df_ln_filtered[merlot_df_ln_filtered['public'].str.contains(query['public'])]
        print(merlot_df_ln_filtered.head)

        #calculate cosine similarity between other things
        cossim = torch.nn.CosineSimilarity(0, 1e-6)
        merlot_df_ln_filtered['cos_sim_disc'] = tensordf['discipline_en'].apply(lambda x: cossim(x, user_discipline_encoding))
        merlot_df_ln_filtered['cos_sim_keyw'] = tensordf['keywords_en'].apply(lambda x: cossim(x, user_keywords_encoding))
        merlot_df_ln_filtered['cos_sim_dur'] = tensordf['duration_en'].apply(lambda x: cossim(x, user_duration_encoding))
        #add the score
        merlot_df['SCORE'] = merlot_df_ln_filtered[['cos_sim_disc', 'cos_sim_keyw', 'cos_sim_dur']].mean(axis=1)

        #sort the results
        printable_df = merlot_df[['title', 'link', 'public', 'language', 'SCORE']]
        printable_df= printable_df.sort_values(by=['SCORE'], ascending=False)

        #format the results 
        result = printable_df.head(10).style.to_html()

    return html(result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
