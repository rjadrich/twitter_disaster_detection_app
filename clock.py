from apscheduler.schedulers.blocking import BlockingScheduler
from rq import Queue
from worker import conn
from tweet_miner import fetch_tweets

sched = BlockingScheduler()
q = Queue(connection=conn)

#this shchedules a twitter api call to fetch some new tweets every 5 minutes
@sched.scheduled_job('interval', minutes=5)
def job_fetch_tweets():
    result = q.enqueue(fetch_tweets)

sched.start()