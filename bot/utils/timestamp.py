from datetime import datetime

def timestamp():
    time_now = datetime.utcnow()
    return(time_now.strftime("``[%H:%M:%S]``"))
