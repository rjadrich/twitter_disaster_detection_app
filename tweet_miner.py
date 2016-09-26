import time
import pandas as pd
import tweepy
import boto3
import os
import twitter_parser
from gensim import corpora, models

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
    make_lsi = lambda tokenized_text: zip(*lsi[tfidf[dictionary.doc2bow(tokenized_text)]])[1]
    new_tweets_df['LSI'] = new_tweets_df['Tokenized'].apply(make_lsi)
    

    new_tweets_df['Certainty'] = 0
    
    #write a csv file with utf8 encoded tweets 
    #new_tweets_df = pd.DataFrame(data = new_tweets, columns = ["Keyword", "Tweet"])
    new_tweets_df.to_csv(path_or_buf = 'data/tweets.csv')
    
    #the heroku filesystem is ephermeral so this file must be moved to amazon web services s3 hosting
    s3client = boto3.client('s3')
    object_key = '%i.csv' % int(time.time())
    bucket_name = os.environ["S3_BUCKET_NAME"]
    s3client.upload_file('data/tweets.csv', Bucket=bucket_name, Key=object_key)
        
    return new_tweets

if __name__ == "__main__":
    fetch_tweets()