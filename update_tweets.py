import pandas as pd
import tweepy
import os

def fetch_tweets():
    #get absolute path
    #MYDIR = os.path.dirname(__file__)
    
    #key information to access the twitter api
    consumer_key = "IUZ7bZtjQmhtbh36FY4RtIqY4"
    consumer_secret = "fEYROmCU5WTInSQOYoqLLo2x5CiagQnMNu2oLEPVoUraIfh4Cq"
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)

    #keywords to search for
    keywords = ['ablaze', 'accident', 'aftershock', 'airplane accident', 'ambulance', 'annihilated', 'annihilation', 'apocalypse', 'armageddon', 'army', 'arson', 'arsonist', 'attack', 'attacked', 'avalanche', 'battle', 'bioterror', 'bioterrorism', 'blaze', 'blazing', 'bleeding', 'blew up', 'blight', 'blizzard', 'blood', 'bloody', 'blown up', 'body bag', 'body bagging', 'body bags', 'bomb', 'bombed', 'bombing', 'bridge collapse', 'buildings burning', 'buildings on fire', 'burned', 'burning', 'burning buildings', 'bush fires', 'casualties', 'casualty', 'catastrophe', 'catastrophic', 'chemical emergency', 'cliff fall', 'collapse', 'collapsed', 'collide', 'collided', 'collision', 'crash', 'crashed', 'crush', 'crushed', 'curfew', 'cyclone', 'damage', 'danger', 'dead', 'death', 'deaths', 'debris', 'deluge', 'deluged', 'demolish', 'demolished', 'demolition', 'derail', 'derailed', 'derailment', 'desolate', 'desolation', 'destroy', 'destroyed', 'destruction', 'detonate', 'detonation', 'devastated', 'devastation', 'disaster', 'displaced', 'drought', 'drown', 'drowned', 'drowning', 'dust storm', 'earthquake', 'electrocute', 'electrocuted', 'emergency', 'emergency plan', 'emergency services', 'engulfed', 'epicentre', 'evacuate', 'evacuated', 'evacuation', 'explode', 'exploded', 'explosion', 'eyewitness', 'famine', 'fatal', 'fatalities', 'fatality', 'fear', 'fire', 'fire truck', 'first responders', 'flames', 'flattened', 'flood', 'flooding', 'floods', 'forest fire', 'forest fires', 'hail', 'hailstorm', 'harm', 'hazard', 'hazardous', 'heat wave', 'hellfire', 'hijack', 'hijacker', 'hijacking', 'hostage', 'hostages', 'hurricane', 'injured', 'injuries', 'injury', 'inundated', 'inundation', 'landslide', 'lava', 'lightning', 'loud bang', 'mass murder', 'mass murderer', 'massacre', 'mayhem', 'meltdown', 'military', 'mudslide', 'natural disaster', 'nuclear disaster', 'nuclear reactor', 'obliterate', 'obliterated', 'obliteration', 'oil spill', 'outbreak', 'pandemonium', 'panic', 'panicking', 'police', 'quarantine', 'quarantined', 'radiation emergency', 'rainstorm', 'razed', 'refugees', 'rescue', 'rescued', 'rescuers', 'riot', 'rioting', 'rubble', 'ruin', 'sandstorm', 'screamed', 'screaming', 'screams', 'seismic', 'sinkhole', 'sinking', 'siren', 'sirens', 'smoke', 'snowstorm', 'storm', 'stretcher', 'structural failure', 'suicide bomb', 'suicide bomber', 'suicide bombing', 'sunk', 'survive', 'survived', 'survivors', 'terrorism', 'terrorist', 'threat', 'thunder', 'thunderstorm', 'tornado', 'tragedy', 'trapped', 'trauma', 'traumatised', 'trouble', 'tsunami', 'twister', 'typhoon', 'upheaval', 'violent storm', 'volcano', 'war zone', 'weapon', 'weapons', 'whirlwind', 'wild fires', 'wildfire', 'windstorm', 'wounded', 'wounds', 'wreck', 'wreckage', 'wrecked']

    #get the tweets
    new_tweets = []
    for keyword in keywords:
        results = api.search(q = keyword)
        for result in results:
            new_tweets.append(result.text.encode('utf-8'))
           
        
    #place into a dataframe and write a csv file with utf8 encoded tweets 
    #new_tweets_df = pd.DataFrame(data = new_tweets, columns = ["text"])
    #new_tweets_df.to_csv(path_or_buf = os.path.join(MYDIR, 'data/tweets.csv'))        
        
    return new_tweets

if __name__ == '__main__':
    fetch_tweets()