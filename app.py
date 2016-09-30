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
from bokeh.plotting import figure, ColumnDataSource
import numpy as np

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
        #object_key = '%i.csv' % time_index
        #s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        #object_key = '%i_truncated.csv' % time_index
        #s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        #object_key = '%i_stats.csv' % time_index
        #s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        #object_key = '%i_keyword_stats.csv' % time_index
        #s3client.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=object_key)
        
        #get addresses for the various data sets
        data_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i.csv' % time_index
        data_truncated_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i_truncated.csv' % time_index
        data_stats_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i_stats.csv' % time_index
        data_keyword_stats_address = 'https://s3.amazonaws.com/disasters-on-twitter/%i_keyword_stats.csv' % time_index
        
        #generate the stats data plot
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
        stats_script, stats_div = components(plot)
        df_stats = None
        
        #generate the keyword stats data plot
        df_keyword_stats = pd.read_csv(data_keyword_stats_address, index_col = 0)
        keywords = df_keyword_stats.index.tolist()
        q1 = np.array(df_keyword_stats['per_10'])
        q2 = np.array(df_keyword_stats['median'])
        q3 = np.array(df_keyword_stats['per_90'])
        df_keyword_stats = None
        source = ColumnDataSource(
                data=dict(
                    keywords = keywords,
                    q32m=(q3+q2)/2,
                    q32d=q3-q2,
                    q21m=(q2+q1)/2,
                    q21d=q2-q1,
                )
            )
        plot = figure(tools="save,pan,wheel_zoom,box_zoom,reset,hover", 
                   title="Top 50 keywords by median certainty", 
                   x_range=['','']+keywords+['',''])
        plot.rect('keywords', 'q32m', 0.7, 'q32d',
            fill_color="#d53e4f", line_width=1, line_color="black", source=source)
        plot.rect('keywords', 'q21m', 0.7, 'q21d',
            fill_color="#3288bd", line_width=1, line_color="black", source=source)
        plot.xaxis.major_label_orientation = 3.14/3
        plot.xaxis.axis_label = 'Keyword'
        plot.yaxis.axis_label = 'Certainty (10th, 50th and 70th percentiles)'
        hover = plot.select(dict(type=HoverTool))
        hover.tooltips = [('Keyword', '@keywords')]
        keyword_stats_script, keyword_stats_div = components(plot)           
        
        #send the data out
        stats_plot_summary = 'Summary of mined tweets organized by certainty'
        stats_plot_info = 'Mouseover shows dominant disaster keywords in each bin'
        keyword_stats_plot_summary = 'Statistical summary of top 50 keywords by median certainty'
        keyword_stats_plot_info = 'Keywords with less than 10 tweets have been neglected. Mouseover shows keyword'
        table_summary = 'Sample of tweets mined and sorted by certainty'
        table_info = 'The whole dataset in csv format can be downloaded via the link'
        

        df_tweets = pd.read_csv(data_truncated_address, index_col = 0)
        return render_template('home.html', 
                               table=df_tweets.to_html(classes = 'tweets', index = False), 
                               csv_link_text = 'Download full raw data',
                               csv_link = data_address,
                               github=github,
                               time_string = time_string,
                               stats_script = stats_script,
                               stats_div = stats_div,
                               stats_plot_summary = stats_plot_summary,
                               stats_plot_info = stats_plot_info,
                               keyword_stats_script = keyword_stats_script,
                               keyword_stats_div = keyword_stats_div,
                               keyword_stats_plot_summary = keyword_stats_plot_summary,
                               keyword_stats_plot_info = keyword_stats_plot_info,
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