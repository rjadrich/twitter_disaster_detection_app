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
from bokeh.charts import Bar, show, save
from bokeh.models import HoverTool
from bokeh.io import output_file

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
    return render_template('home.html', github=github, time_string = 'Monitoring Twitter for disasters 24/7')

@app.route('/home', methods=['GET','POST'])
def home():
    if request.method == 'GET':
        return render_template('home.html', github=github, time_string = 'Monitoring Twitter for disasters 24/7')
    else:
        #fetch the most recent tweet data set and store locally
        file_list = []
        date_list = []
        for entry in s3client.list_objects(Bucket=bucket_name)['Contents']:
            search = re.search(r'([0-9]+).csv', entry['Key'])
            if search:
                file_list.append(int(search.group(1)))
                date_list.append(entry['LastModified'].strftime('%m/%d/%Y %H:%M %Z'))
        file_date_list = zip(file_list, date_list)
        file_date_list.sort()        
        time_index = file_date_list[-1][0]
        time_string = 'Extracted data mined on ' + file_date_list[-1][1]
        
        #file_list.sort()
        #time_index = file_list[-1] #this will not ever generate an index out of range issue
        
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
        
        #load in the stats for plotting
        df_stats = pd.read_csv(data_stats_address, index_col = 0)
        
        certainty = df_stats['Certainty'].tolist()
        counts = df_stats['Counts'].tolist()
        top_keywords = df_stats['Top_Keywords'].tolist()
        data = {'Certainty': certainty, 'Counts': counts, 'Top_Keywords': top_keywords}

        plot = Bar(data, label='Certainty', values='Counts', stack = 'Top_Keywords', tools='hover', legend = False, 
                   color = '#3288bd', width = 500, height = 500, title = 'Mined Disaster Tweet Statistics')
        plot.xaxis.axis_label = 'Certainty of Disaster'
        plot.yaxis.axis_label = 'Number of Tweets'

        hover = plot.select(dict(type=HoverTool))
        hover.tooltips = [('Top keywords', '@Top_Keywords')]
        
        script, div = components(plot)
        
        #send the data out
        plot_summary = 'Summary of mined tweets organized by certainty'
        plot_info = 'Mouseover shows dominant disaster keywords in each bin'
        table_summary = 'Sample of tweets mined and sorted by certainty'
        table_info = 'The whole dataset in csv format can be downloaded via the link'
        
        #df_tweets = pd.DataFrame(data = [[10, 45], [23, 45]])
        df_tweets = pd.read_csv(data_truncated_address, index_col = 0)
        return render_template('home.html', 
                               table=df_tweets.to_html(classes = 'tweets', index = False), 
                               csv_link_text = 'Download full raw data',
                               csv_link = data_address,
                               github=github,
                               script = script,
                               div = div,
                               time_string = time_string,
                               plot_summary = plot_summary,
                               plot_info = plot_info,
                               table_summary = table_summary,
                               table_info = table_info)
        
        
        
        
        
        #return data_truncated_address
        
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

        #df_tweets = pd.read_csv('https://s3.amazonaws.com/disasters-on-twitter/1475037364_truncated.csv', index_col = 0)
        #return render_template('home.html', 
        #                       table=df_tweets.to_html(classes = 'tweets', index = False), 
        #                       csv_link_text = 'Download full raw data',
        #                       csv_link = 'https://s3.amazonaws.com/disasters-on-twitter/1475037364.csv',
        #                       github=github)
    
    
    
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