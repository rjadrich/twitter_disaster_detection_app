import time
import pandas as pd
import tweepy
import boto3
import os
import twitter_parser
import dill
from gensim import corpora, models
from sklearn.linear_model import LogisticRegression
import re
import numpy as np

#offset the percentiles by a small amount to make sure it plots something 
def per_10(x):
    return np.percentile(x, 9.99)
def per_90(x):
    return np.percentile(x, 90.01)

def binDisasters(certainty):
    if certainty < 0.1:
        return 0.05
    elif certainty < 0.2:
        return 0.15
    elif certainty < 0.3:
        return 0.25
    elif certainty < 0.4:
        return 0.35
    elif certainty < 0.5:
        return 0.45
    elif certainty < 0.6:
        return 0.55
    elif certainty < 0.7:
        return 0.65
    elif certainty < 0.8:
        return 0.75
    elif certainty < 0.9:
        return 0.85
    else:
        return 0.95
    
def getCertaintyKeywords(df):
    df_grouped = df.groupby(['Certainty_Binned','Keyword']).apply(len)
    df['Keyword'].unique().tolist()
    certainty_keywords = []
    for certainty in [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]:
        keywords = df_grouped[certainty].index.tolist()
        counts = df_grouped[certainty].tolist()
        counts_keywords = sorted(zip(counts, keywords))
        num_keywords = len(counts_keywords)
        n = 3
        if num_keywords >= n:
            certainty_keywords.append(', '.join(zip(*counts_keywords)[1][-n-1:]))
        else:
            certainty_keywords.append(','.join(zip(*counts_keywords)[1][-num_keywords-1:]))
            
    return certainty_keywords
    
def make_lsi(tokenized_text, dictionary, tfidf, lsi):
    lsi_vec = zip(*lsi[tfidf[dictionary.doc2bow(tokenized_text)]])
    if lsi_vec:
        return lsi_vec[1]
    else:
        return [0.0 for i in range(lsi.num_topics)]
    
def predict(lsi_vec, model):
    return model.predict_proba(lsi_vec)[0][1]

def fetch_tweets():

    #keywords to search for
    keywords = ['ablaze', 'accident', 'aftershock', 'airplane accident', 'ambulance', 'annihilated', 'annihilation', 'apocalypse', 'armageddon', 'army', 'arson', 'arsonist', 'attack', 'attacked', 'avalanche', 'battle', 'bioterror', 'bioterrorism', 'blaze', 'blazing', 'bleeding', 'blew up', 'blight', 'blizzard', 'blood', 'bloody', 'blown up', 'body bag', 'body bagging', 'body bags', 'bomb', 'bombed', 'bombing', 'bridge collapse', 'buildings burning', 'buildings on fire', 'burned', 'burning', 'burning buildings', 'bush fires', 'casualties', 'casualty', 'catastrophe', 'catastrophic', 'chemical emergency', 'cliff fall', 'collapse', 'collapsed', 'collide', 'collided', 'collision', 'crash', 'crashed', 'crush', 'crushed', 'curfew', 'cyclone', 'damage', 'danger', 'dead', 'death', 'deaths', 'debris', 'deluge', 'deluged', 'demolish', 'demolished', 'demolition', 'derail', 'derailed', 'derailment', 'desolate', 'desolation', 'destroy', 'destroyed', 'destruction', 'detonate', 'detonation', 'devastated', 'devastation', 'disaster', 'displaced', 'drought', 'drown', 'drowned', 'drowning', 'dust storm', 'earthquake', 'electrocute', 'electrocuted', 'emergency', 'emergency plan', 'emergency services', 'engulfed', 'epicentre', 'evacuate', 'evacuated', 'evacuation', 'explode', 'exploded', 'explosion', 'eyewitness', 'famine', 'fatal', 'fatalities', 'fatality', 'fear', 'fire', 'fire truck', 'first responders', 'flames', 'flattened', 'flood', 'flooding', 'floods', 'forest fire', 'forest fires', 'hail', 'hailstorm', 'harm', 'hazard', 'hazardous', 'heat wave', 'hellfire', 'hijack', 'hijacker', 'hijacking', 'hostage', 'hostages', 'hurricane', 'injured', 'injuries', 'injury', 'inundated', 'inundation', 'landslide', 'lava', 'lightning', 'loud bang', 'mass murder', 'mass murderer', 'massacre', 'mayhem', 'meltdown', 'military', 'mudslide', 'natural disaster', 'nuclear disaster', 'nuclear reactor', 'obliterate', 'obliterated', 'obliteration', 'oil spill', 'outbreak', 'pandemonium', 'panic', 'panicking', 'police', 'quarantine', 'quarantined', 'radiation emergency', 'rainstorm', 'razed', 'refugees', 'rescue', 'rescued', 'rescuers', 'riot', 'rioting', 'rubble', 'ruin', 'sandstorm', 'screamed', 'screaming', 'screams', 'seismic', 'sinkhole', 'sinking', 'siren', 'sirens', 'smoke', 'snowstorm', 'storm', 'stretcher', 'structural failure', 'suicide bomb', 'suicide bomber', 'suicide bombing', 'sunk', 'survive', 'survived', 'survivors', 'terrorism', 'terrorist', 'threat', 'thunder', 'thunderstorm', 'tornado', 'tragedy', 'trapped', 'trauma', 'traumatised', 'trouble', 'tsunami', 'twister', 'typhoon', 'upheaval', 'violent storm', 'volcano', 'war zone', 'weapon', 'weapons', 'whirlwind', 'wild fires', 'wildfire', 'windstorm', 'wounded', 'wounds', 'wreck', 'wreckage', 'wrecked']
    
    #key information to access the twitter api
    consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
    consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)

    #get the tweets and store in a list
    new_tweets = []
    for keyword in keywords: #cleaned_keywords:
        results = api.search(q = keyword)
        for result in results:
            #new_tweets.append([keyword, result.text]) 
            new_tweets.append([keyword, result.text.encode('utf-8', errors ="ignore")])
    
    #write a csv file with utf8 encoded tweets 
    new_tweets_df = pd.DataFrame(data = new_tweets, columns = ["Keyword", "Tweet"])
    #new_tweets_df.to_csv(path_or_buf = 'data/tweets.csv')
    
    #classify the tweets using a gensim model persisted to file
    tokenize_it = twitter_parser.Tokenizer()
    new_tweets_df['Tokenized'] = new_tweets_df['Tweet'].apply(tokenize_it.tweet_to_tokens)
    
    #load bow, tfidf, and lsi to transform for classification
    dictionary = corpora.Dictionary.load('./models/model.dict')
    tfidf = models.TfidfModel.load('./models/model.tfidf')
    lsi = models.LsiModel.load('./models/model.lsi')
    make_lsi_wrapper = lambda tokenized_text: make_lsi(tokenized_text, dictionary, tfidf, lsi)
    new_tweets_df['LSI'] = new_tweets_df['Tokenized'].apply(make_lsi_wrapper)
    
    #predict the probability that it is a disaster
    with open("./models/log_reg_model.dill") as model_file:
        model = dill.load(model_file)  
    predict_wrapper = lambda lsi_vec: predict(lsi_vec, model)
    new_tweets_df['Certainty'] = new_tweets_df['LSI'].apply(predict_wrapper)
    
    #write a csv file with utf8 encoded tweets 
    #new_tweets_df = pd.DataFrame(data = new_tweets, columns = ["Keyword", "Tweet"])
    new_tweets_df = new_tweets_df[['Keyword', 'Tweet', 'Certainty']].sort(['Certainty'], ascending = False).reset_index(drop=True)
    new_tweets_df.to_csv(path_or_buf = 'data/tweets.csv')
    new_tweets_df[0:20].to_csv(path_or_buf = 'data/tweets_truncated.csv')
    
    #create a small dataset for plotting in bokeh on front end
    new_tweets_df['Certainty_Binned'] = new_tweets_df['Certainty'].apply(binDisasters)
    certainty_bins_keywords = [''] + getCertaintyKeywords(new_tweets_df) + ['']
    certainty_bins =  [0.0] + new_tweets_df[['Certainty_Binned']].groupby(['Certainty_Binned']).apply(len).index.tolist() + [1.0]
    counts_bins = [0.0] + new_tweets_df[['Certainty_Binned']].groupby(['Certainty_Binned']).apply(len).tolist() + [0.0]
    df_stats = pd.DataFrame(data = zip(certainty_bins, counts_bins, certainty_bins_keywords), columns = ['Certainty', 'Counts', 'Top_Keywords'])
    df_stats.to_csv(path_or_buf = 'data/tweets_stats.csv')
    
    #create a small dataset of keyword stats
    df_keyword_stats = new_tweets_df.groupby('Keyword').agg({'Certainty':[len, np.median, per_10, per_90, 'min', 'max']})['Certainty']
    df_keyword_stats = df_keyword_stats[df_keyword_stats['len'] >= 10].sort(['median'], ascending = False)
    df_keyword_stats = df_keyword_stats[0:50]
    df_keyword_stats.to_csv(path_or_buf = 'data/tweets_keyword_stats.csv')
    
    ###################################################################################################################################
    
    #establish s3 client
    s3client = boto3.client('s3')
    
    #the heroku filesystem is ephermeral so this file must be moved to amazon web services s3 hosting
    time_index = int(time.time())
    bucket_name = os.environ["S3_BUCKET_NAME"]
    
    object_key = '%i.csv' % time_index
    s3client.upload_file('data/tweets.csv', Bucket=bucket_name, Key=object_key)
    s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
    
    object_key = '%i_truncated.csv' % time_index
    s3client.upload_file('data/tweets_truncated.csv', Bucket=bucket_name, Key=object_key)
    s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
    
    object_key = '%i_stats.csv' % time_index
    s3client.upload_file('data/tweets_stats.csv', Bucket=bucket_name, Key=object_key)
    s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
    
    object_key = '%i_keyword_stats.csv' % time_index
    s3client.upload_file('data/tweets_keyword_stats.csv', Bucket=bucket_name, Key=object_key)
    s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
    
    #now perform a little bucket cleaning (only keep 10 most recent)
    file_list = []
    for entry in s3client.list_objects(Bucket=bucket_name)['Contents']:
        search = re.search(r'([0-9]+).csv', entry['Key'])
        if search:
            file_list.append(int(search.group(1)))
    file_list.sort()
    file_list_delete = file_list[:-10] #this will not ever generate an index out of range issue
    
    for time_index in file_list_delete:
        object_key = '%i.csv' % time_index
        s3client.delete_object(Bucket=bucket_name, Key=object_key)
        object_key = '%i_truncated.csv' % time_index
        s3client.delete_object(Bucket=bucket_name, Key=object_key)
        object_key = '%i_stats.csv' % time_index
        s3client.delete_object(Bucket=bucket_name, Key=object_key)
        object_key = '%i_keyword_stats.csv' % time_index
        s3client.delete_object(Bucket=bucket_name, Key=object_key)
            
    return new_tweets

if __name__ == "__main__":
    fetch_tweets()