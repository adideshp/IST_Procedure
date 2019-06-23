from crontab import CronTab
import datetime
import csv

import os
dir_path = os.path.dirname(os.path.realpath(__file__))

DAY = {
    "SU": 0,
    "M": 1,
    "T": 2,
    "W": 3,
    "TH": 4,
    "F": 5,
    "SA": 6,
}



def gen_exec_cron(freq, day, cron, command):
    if day.upper() in DAY.keys():
        day = DAY[day.upper()]
        if freq.upper() == "WEEKLY":
            job = cron.new(command=command)
            job.dow.on(day)
            job.minute.on(0)
            job.hour.on(0)
            cron.write()
            return [job]
        elif freq.upper() == "FORTNIGHTLY":
            """
            Get the date for the next day. 
            calculate 5 values that are each 15 days apart (each being on the same day of the week)
            """
            # in python datetime monday:0 sunday:6
            schedule = []
            if day == 0:
                day = 6
            else:
                day -= 1
            d = datetime.date.today()
            while d.weekday() != day:
                d += datetime.timedelta(1)
            #we have the first day now, lets increment the day by 15 to get the fortnightly day
            #find next 5 dates
            for i in range(5):
                job = cron.new(command=command)
                job.day.on(d.day)
                job.minute.on(0)
                job.hour.on(0)
                job.month.on(d.month)
                cron.write()
                d += datetime.timedelta(14)
                schedule.append(job)
            return schedule
        else:
            return []
                

def schedule(username, prob_filename, python_path):
    jobs = []
    with open(prob_filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count +=1
                continue
            else:
                jobs.append(row)

    print(jobs)
    cron = CronTab(user=username)  
    #Clear all the previous cron-tabs
    cron.remove_all()
    cron.write()
    for job in jobs:
        command = python_path + " " + dir_path + '/main.py --perform_ist ' + job[0]
        schedules = gen_exec_cron(job[1], job[2], cron, command)
    return schedules
    