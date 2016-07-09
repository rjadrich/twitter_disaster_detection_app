from apscheduler.schedulers.blocking import BlockingScheduler
from rq import Queue
from worker import conn
from tweet_miner import fetch_tweets

#establish the scheduler and queue
sched = BlockingScheduler()
q = Queue(connection = conn)

#on startup of the clock we want to automatically find new tweets and place in job_id=0
job = q.enqueue(fetch_tweets, job_id = 0, result_ttl = -1)
job_id = 1

#this shchedules a twitter api call to fetch some new tweets every 30 minutes
#one job will be reserved with data and another for actively fetching new data
#20 min is allocated to each job just in case it takes a while to finish
@sched.scheduled_job('interval', minutes = 30)
def job_fetch_tweets():
    if job_id == 0:
        job = q.enqueue(fetch_tweets, job_id = job_id, result_ttl = -1, timeout = 1200)
        job_id = 1
    else:
        job = q.enqueue(fetch_tweets, job_id = job_id, result_ttl = -1, timeout = 1200)
        job_id = 0

sched.start()