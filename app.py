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
from update_tweets import fetch_tweets 
from rq import Queue
from worker import conn

#establish the app and logging for app
app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.vars={}

#establish the queue
q = Queue(connection = conn)

@app.route('/')
def main():
    return render_template('ticker_input.html')

@app.route('/ticker_input', methods=['GET','POST'])
def index():
    github = 'https://github.com/rjadrich/flask-demo'
    
    if request.method == 'GET':
        return render_template('ticker_input.html', message="Please enter a stock ticker (e.g. GOOG).", github=github)
    else:
        app.vars['ticker'] = request.form['ticker']
        app.vars['ticker_options'] = request.form.getlist('ticker_options')
        
    #error check 
    if  app.vars['ticker'] == '':
        return render_template('ticker_input.html', message="Nothing entered.", github=github)
    
    #error check 
    if  len(app.vars['ticker_options']) == 0:
        return render_template('ticker_input.html', message="No choices selected for %s." % app.vars['ticker'].upper(), github=github)

    #get the data
    api_url = 'https://www.quandl.com/api/v1/datasets/WIKI/%s.json' % app.vars['ticker']
    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    raw_data = session.get(api_url)
    aapl_stock = raw_data.json()
    
    #error check again
    if "error" in aapl_stock.keys():
        return render_template('ticker_input.html', message="Stock %s does not exist." % app.vars['ticker'].upper(), github=github)

    #make a datetime dataset
    stock_df = pd.DataFrame(data = aapl_stock["data"], columns = aapl_stock["column_names"])[['Date','Open','Adj. Open','Close','Adj. Close']]
    convert_to_dt = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
    stock_df['Date_dt'] = stock_df['Date'].apply(convert_to_dt)

    #make the plot
    TOOLS = 'box_zoom,box_select,crosshair,resize,reset'
    plot = figure(tools=TOOLS, title='Data from Quandle WIKI set', x_axis_label='date', x_axis_type='datetime', width=700, height=400)
    iteration = 0
    for entry in app.vars['ticker_options']:
        plot.line(stock_df['Date_dt'], stock_df[entry], line_width=3, color=Spectral6[iteration], legend=entry)
        iteration = iteration + 1
    script, div = components(plot)
    header_text = "Stock data for %s" % app.vars['ticker'].upper()
    
    #return render_template('graph_ticker.html', script=script, div=div, header_text=header_text)
    return render_template('ticker_input.html', script=script, div=div, message="Plotted stock %s below." % app.vars['ticker'].upper(), github=github)

@app.route('/get_tweets')
def get_tweets():
    job = q.enqueue(fetch_tweets)
    time.sleep(2)
    return job.get_id()

if __name__ == '__main__':
    app.debug = True
    app.run(port=33507)
