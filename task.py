from celery import Celery
import Celery01


app=Celery('task',backend='redis://localhost:6379/0', broker='amqp://guest@localhost//')

@app.task
def picasso(pick_fm,n_min,n_current,n_max,divisions_id,numberDivisions,max_time):
    return Celery01.main(pick_fm,n_min,n_current,n_max,divisions_id,numberDivisions,max_time)
