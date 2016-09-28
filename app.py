from flask import Flask, render_template, request, redirect, jsonify
from bokeh.plotting import figure
from bokeh.embed import components 
from bokeh.palettes import Spectral6
import requests
import pandas as pd
import datetime
import sys
import logging
import time
import boto3
import os
import re

from tweet_miner import fetch_tweets 
#from rq import Queue
#from worker import conn

#establish the app and logging for app
app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.vars={}

#establish the s3 connection to get tweets
s3client = boto3.client('s3')

#get the bucket name
bucket_name = os.environ["S3_BUCKET_NAME"]

#establish the queue
#q = Queue(connection = conn)

#github link
github = 'https://github.com/rjadrich/disaster_detection_via_twitter/blob/master/disaster_detection_via_twitter_data_incubator.ipynb'

#make sure to display full data
pd.set_option('display.max_colwidth', 300)

@app.route('/')
def main():
    #df_tweets = pd.read_csv('https://s3.amazonaws.com/disasters-on-twitter/1468166721.csv')  
    return render_template('home.html', github=github)

@app.route('/home', methods=['GET','POST'])
def home():
    if request.method == 'GET':
        return render_template('home.html', github=github)
    else:
        #fetch the most recent tweet data set and store locally
        file_list = []
        for entry in s3client.list_objects(Bucket=bucket_name)['Contents']:
            search = re.search(r'([0-9]+).csv', entry['Key'])
            if search:
                file_list.append(int(search.group(1)))
        file_list.sort()
        time_index = file_list[-1] #this will not ever generate an index out of range issue
        
        #make sure everything is readable
        object_key = '%i.csv' % time_index
        s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        object_key = '%i_truncated.csv' % time_index
        s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        object_key = '%i_stats.csv' % time_index
        s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        
        #get addresses for the various data sets
        data_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i.csv' % time_index
        data_truncated_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i_truncated.csv' % time_index
        data_stats_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i_stats.csv' % time_index
        
        #object_key = '%i_truncated.csv' % time_index
        #full_address = './data/' + object_key
        #s3client.download_file(bucket_name, object_key, full_address)
        
#        #send the data to the html table
#        df_tweets = pd.read_csv(full_address, index_col = 0)
#        
#        #return "hello after csv read download %i" % len(df_tweets)
#        return render_template('home.html', 
#                               table=df_tweets.to_html(classes = 'tweets', index = False), 
#                               csv_link_text = 'Download full raw data',
#                               csv_link = 'https://s3.amazonaws.com/disasters-on-twitter/1473879560.csv',
#                               github=github)

        df_tweets = pd.read_csv('https://s3.amazonaws.com/disasters-on-twitter/1475037364_truncated.csv', index_col = 0)
        return render_template('home.html', 
                               table=df_tweets.to_html(classes = 'tweets', index = False), 
                               csv_link_text = 'Download full raw data',
                               csv_link = 'https://s3.amazonaws.com/disasters-on-twitter/1475037364.csv',
                               github=github)
    
    
    
#        df_tweets = pd.read_csv('https://s3.amazonaws.com/disasters-on-twitter/1475037364.csv', index_col = 0)
#        return render_template('home.html', 
#                               table=df_tweets.to_html(classes = 'tweets', index = False), 
#                               csv_link_text = 'Download raw data',
#                               csv_link = 'https://s3.amazonaws.com/disasters-on-twitter/1475037364.csv',
#                               github=github)
    
        
        
        #csv_link = 'https://s3.amazonaws.com/disasters-on-twitter/1473879560.csv',
        
        #csv_link = ('https://s3.amazonaws.com/disasters-on-twitter/%i.csv' % time_index),

if __name__ == '__main__':
    app.debug = True
    app.run(port=33507)