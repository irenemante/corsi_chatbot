import torch
import json
from sentence_transformers import SentenceTransformer
import pandas as pd
from sanic.response import html
from sanic.response import text
from sanic.response import json as sjson
from sanic.request import Request
import sanic
import os
import re

app = sanic.Sanic("RSapp")


@app.before_server_start
async def startup(self, app):
    #pre generate corpus encodings with bert saved to a dataframe
    global agelist
    global tensordf
    global embedder
    global dataset
    global usable_df
    dir = os.getcwd()
    agelist = open(f"{dir}//actions//Dataset//età.txt", "r").readlines()
    print(agelist)
    embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
    dataset = pd.read_csv(f'{dir}//actions//Dataset//codeorg.csv')
    dataset.drop_duplicates(subset='Link')

    usable_df = dataset[['Titolo', 'Durata', 'Keywords', 'Lingua', 'Età', 'Tipo']]

    durations = [str(x) for x in usable_df['Durata'].to_list()]

    duration_encoding = embedder.encode(durations, convert_to_tensor=True)
    keywords_encoding = embedder.encode(usable_df['Keywords'].to_list(), convert_to_tensor=True)

    tuples = list(zip(keywords_encoding, duration_encoding))

    tensordf = pd.DataFrame(tuples, columns=['keywords_en', 'duration_en'])

    # format_mapping = {
    #     "videolezioni": ["presentation", "animation", "online course", "online course module", "tutorial", "simulation"],
    #     "esercizi": ["drill and practice", "assessment tool", "assignment", "workshop and training material"],
    #     "quiz": ["quiz/test"],
    #     "documenti": ["reference material", "open (access) textbook", "case study", "open (access) journal-article"]
    #     }
    print("Server Online")
    return

@app.get("/online")
async def online(request):
    return text("Online")

@app.route("/recommend", methods=["POST"])
async def recommend_handler(request):
    query = request.json
    query["Lingua"] = query["Lingua"].capitalize()
    if query["request_type"] == "recommend":
        #generate user query encoding with bert
        user_keywords_encoding = embedder.encode(', '.join(query['Keywords']), convert_to_tensor=True)
        user_duration_encoding = embedder.encode(query['Durata'], convert_to_tensor=True)

        cossim = torch.nn.CosineSimilarity(0, 1e-6)
        #Calculate cosine similarity between user inputs and Corpus items
        usable_df['cos_sim_keyw'] = tensordf['keywords_en'].apply(lambda x: cossim(x, user_keywords_encoding))
        usable_df['cos_sim_dur'] = tensordf['duration_en'].apply(lambda x: cossim(x, user_duration_encoding))
        
        new_df = usable_df.loc[usable_df['Lingua'].str.contains(query['Lingua'])]
        # new_df['cos_sim_keyw'] = new_df['cos_sim_keyw']
        # new_df['cos_sim_dur'] = new_df['cos_sim_dur']
        # new_df['Tipo'] = new_df['Tipo']
        # new_df['Titolo'] = new_df['Titolo']
        # new_df['Età'] = new_df	['Età']
        if query["type"] != "":
            if query["type"] == "videolezioni":
                filtered_df = new_df.query('Tipo == "Video"')
            if query["type"] == "quiz":
                filtered_df = new_df.query('Tipo == "Quiz"')
            if query["type"] == "esercizi":
                filtered_df = new_df.query('Tipo == "Esercizi"')
            if query["type"] == "documenti":
                filtered_df = new_df.query('Tipo == "Testo"')

        print(filtered_df.head(5))
        
        #filter for age, using a regex to infer age ranges, and assign them to a pandas query
        age_range_indexes = agerangefit(query['Età'])
        queryable_age = []
        for age_index in age_range_indexes:
            queryable_age.append(agelist[age_index])
        print("QUERYABLE AGE LIST :")
        print(queryable_age)
        dfquery = ''
        for item in queryable_age:
            dfquery += f'Età == "{item}" |'
        dfquery += 'Età == "0-99"'
        dfquery = dfquery.replace("\n", "")
        print(dfquery)
        filtered_df2 = filtered_df.query(dfquery)



        


        #Calculate mean score between cosine similarities
        dataset['SCORE'] =  new_df[['cos_sim_keyw', 'cos_sim_dur']].mean(axis=1)

        print(filtered_df2.head())


        #Create a dataframe that has all relevant information for user and debugging purpose, take only the lables that were filtered before from the global dataset
        printable_df = dataset[['Titolo', 'Link', 'Lingua', 'Tipo', 'SCORE']].loc[dataset.index.intersection(filtered_df2.index)]

        printable_df= printable_df.sort_values(by=['SCORE'], ascending=False)

        global result
        result = printable_df[['Titolo', 'Link', 'SCORE', 'Tipo']].head(5)
        print(result.head())
        result = result.to_json(orient='values')
        parsed = json.loads(result)
    return sjson(parsed)

@app.route("/frontpage", methods=["GET"])
async def frontpage_handle(request):
    dir = os.getcwd()
    template = open(f'{dir}/FrontEnd/jwt.html')
    return html(template.read())


def agerangefit(agequery):
    
    rangelist = []
    indexes = []
    counter = 0
    pattern = r"\d+"
    #Create a set of ranges based on the ages provided in the dataset with a regEx
    for item in agelist:
        if "-" in item:
            matches = re.findall(pattern=pattern, string = item)
            intrange = range(int(matches[0]), int(matches[1]))
            rangelist.append(intrange)
        else:
            rangelist.append(range(15, 99))
    
    #Iterate over the ranges and see in which the userquery falls, save the indexes and return them to the caller
    for ranges in rangelist:
        if int(agequery) in ranges:
            indexes.append(counter)
        counter += 1
    print(rangelist)
    print(indexes)
    return indexes



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True, auto_reload=True)
