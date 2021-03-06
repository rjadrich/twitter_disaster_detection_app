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
from gensim import corpora, models

from bokeh.models.widgets import RadioButtonGroup, Paragraph
from bokeh.layouts import column, row
from bokeh.models import CustomJS #NOT NEEDED?

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
        plot = Bar(data, label='Certainty', values='Counts', stack = 'Top_Keywords', tools='hover', toolbar_location="above", 
                   legend = False, color = '#3288bd', width = 600, height = 600, title = 'Mined Disaster Tweet Statistics')
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
        plot = figure(tools="save,pan,wheel_zoom,box_zoom,reset,hover", toolbar_location="above",
                   width = 600, height = 600, title="Top 50 keywords by median certainty", 
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
        
        
@app.route('/about', methods=['GET'])
def about():    
    #load in the topics and extract text
    lsi = models.LsiModel.load('./models/model.lsi')
    n_topics = 10
    n_words = 10
    topics = lsi.print_topics(n_topics, num_words = n_words)
    
    #read in the topic data and plot it
    df_plot_features_and_tweets = pd.read_csv('./data/tweet_topics.csv', index_col = 0)
                            
    ######################                        
                            
    source = ColumnDataSource(
        data=dict(
            color = df_plot_features_and_tweets['color'].tolist(),
            topic0 = df_plot_features_and_tweets['0'].tolist(),
            topic1 = df_plot_features_and_tweets['1'].tolist(),
            topic2 = df_plot_features_and_tweets['2'].tolist(),
            topic3 = df_plot_features_and_tweets['3'].tolist(),
            topic4 = df_plot_features_and_tweets['4'].tolist(),
            topic5 = df_plot_features_and_tweets['5'].tolist(),
            topic6 = df_plot_features_and_tweets['6'].tolist(),
            topic7 = df_plot_features_and_tweets['7'].tolist(),
            topic8 = df_plot_features_and_tweets['8'].tolist(),
            topic9 = df_plot_features_and_tweets['9'].tolist(),
            x = df_plot_features_and_tweets['0'].tolist(),
            y = df_plot_features_and_tweets['1'].tolist(),
        )
    )

    plot = figure(title='2D topic space', tools='box_zoom,wheel_zoom,pan,reset', 
                  plot_width=600, plot_height=600, toolbar_location="above", x_range=(-0.8, 0.8), y_range=(-0.8, 0.8))
    plot.scatter('x', 'y', fill_color = 'color', fill_alpha=0.6, line_color=None, source = source)
    plot.scatter([-100.0], [-100.0], fill_color = '#d53e4f', fill_alpha=0.6, line_color=None, legend = 'Disaster')
    plot.scatter([-100.0], [-100.0], fill_color = '#3288bd', fill_alpha=0.6, line_color=None, legend = 'Not Disaster')

    plot.xaxis.axis_label = 'Topic x'
    plot.yaxis.axis_label = 'Topic y'


    callback_1 = CustomJS(args=dict(source=source, plot=plot), code="""
            var data = source.get('data');
            var f = cb_obj.get('active');

            if (f === 0)
            {data['x'] = data['topic0'];}
            else if (f === 1)
            {data['x'] = data['topic1'];}
            else if (f === 2)
            {data['x'] = data['topic2'];}
            else if (f === 3)
            {data['x'] = data['topic3'];}
            else if (f === 4)
            {data['x'] = data['topic4'];}
            else if (f === 5)
            {data['x'] = data['topic5'];}
            else if (f === 6)
            {data['x'] = data['topic6'];}
            else if (f === 7)
            {data['x'] = data['topic7'];}
            else if (f === 8)
            {data['x'] = data['topic8'];}
            else if (f === 9)
            {data['x'] = data['topic9'];}

            source.trigger('change');
            plot.trigger('change');
        """)

    callback_2 = CustomJS(args=dict(source=source, plot=plot), code="""
            var data = source.get('data');
            var f = cb_obj.get('active')

            if (f === 0)
            {data['y'] = data['topic0'];}
            else if (f === 1)
            {data['y'] = data['topic1'];}
            else if (f === 2)
            {data['y'] = data['topic2'];}
            else if (f === 3)
            {data['y'] = data['topic3'];}
            else if (f === 4)
            {data['y'] = data['topic4'];}
            else if (f === 5)
            {data['y'] = data['topic5'];}
            else if (f === 6)
            {data['y'] = data['topic6'];}
            else if (f === 7)
            {data['y'] = data['topic7'];}
            else if (f === 8)
            {data['y'] = data['topic8'];}
            else if (f === 9)
            {data['y'] = data['topic9'];}

            source.trigger('change');
            plot.trigger('change');
        """)

    radio_button_topic_1 = RadioButtonGroup(
            labels=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], active=0, width = 600, callback=callback_1)
    radio_button_topic_2 = RadioButtonGroup(
            labels=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], active=1, width = 600, callback=callback_2)

    #hover tool for the plot
    #hover = plot.select(dict(type=HoverTool))
    #hover.tooltips = [('Tweet', '@tweets')]

    text_topic_1 = Paragraph(text="Topic x:", width = 60)
    text_topic_2 = Paragraph(text="Topic y:", width = 60)

    options_1 = row(text_topic_1, radio_button_topic_1)
    options_2 = row(text_topic_2, radio_button_topic_2)

    layout = column(options_1, options_2, plot)                        
    
    topics_script, topics_div = components(layout)                                          
                            
    ######################                        
    
    return render_template('about.html', 
                           github=github, 
                           topic_0_text=topics[0][1],
                           topic_1_text=topics[1][1], 
                           topic_2_text=topics[2][1], 
                           topic_3_text=topics[3][1], 
                           topic_4_text=topics[4][1], 
                           topic_5_text=topics[5][1], 
                           topic_6_text=topics[6][1], 
                           topic_7_text=topics[7][1], 
                           topic_8_text=topics[8][1], 
                           topic_9_text=topics[9][1], 
                           topics_script = topics_script,
                           topics_div = topics_div,)
    
        

if __name__ == '__main__':
    app.debug = True
    app.run(port=33507)