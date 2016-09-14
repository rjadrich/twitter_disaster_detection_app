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

from tweet_miner import fetch_tweets 
from rq import Queue
from worker import conn

#establish the app and logging for app
app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.vars={}

#establish the s3 connection to get tweets
s3client = boto3.client('s3')

#establish the queue
q = Queue(connection = conn)

#github link
github = 'https://github.com/rjadrich/flask-demo'

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
        #df_tweets = pd.read_csv('https://s3.amazonaws.com/disasters-on-twitter/1468166721.csv')  
        
        df_tweets = pd.read_csv('https://s3.amazonaws.com/disasters-on-twitter/1473879560.csv', index_col = 0)
        return render_template('home.html', 
                               table=df_tweets.to_html(classes = 'tweets', index = False), 
                               csv_link_text = 'Download raw data',
                               csv_link = 'https://s3.amazonaws.com/disasters-on-twitter/1473879560.csv',
                               github=github)
        

if __name__ == '__main__':
    app.debug = True
    app.run(port=33507)