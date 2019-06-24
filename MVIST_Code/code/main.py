#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
from algorithm import Algorithm
from csp_algorithm import CSP
from csp_prob import CSP_Prob
from setup_cron import schedule
from datetime import datetime

import csv
import numpy as np
from numpy import zeros
import settings as setting


def generate_skuwise_csv(report):
    report_list = [['IST Date', 'SKU', 'From Store', ' To Store',
                   'IST Qty']]

    for source_shop in report:
        for dest_shop in report[source_shop]:
            for sku in report[source_shop][dest_shop]:
                date = datetime.date(datetime.now()).strftime('%d/%m/%Y'
                        )
                report_list.append([date, sku, source_shop, dest_shop,
                                   str(report[source_shop][dest_shop][sku])])

    with open(setting.IST_DETAIL_FILE, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(report_list)


def generate_summary_csv(report):
    report_list = [['IST Date', 'From Store', ' To Store', 'IST Qty']]
    #report.insert(0, header)
    for source_shop in report:
        for dest_shop in report[source_shop]:
            qty = 0
            for sku in report[source_shop][dest_shop]:
                qty += report[source_shop][dest_shop][sku]
            date = datetime.date(datetime.now()).strftime('%d/%m/%Y')
            report_list.append([date, source_shop, dest_shop, str(qty)])
    with open(setting.IST_SUMMARY_FILE, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(report_list)
    return


def perform_ist(
    cluster_name,
    cluster_info_filename,
    inventory_filename,
    bsq_filename,
    prob_filename,
    ):
    csp = CSP_Prob(cluster_name, cluster_info_filename,
                   inventory_filename, bsq_filename, prob_filename)
    ist_algorithm = Algorithm(csp)
    ist_algorithm.execute()
    generate_skuwise_csv(ist_algorithm._strategy.report_skuwise)
    generate_summary_csv(ist_algorithm._strategy.report_skuwise)


def update_cron(user, schedule_file, python_path):
    schedules = schedule(user, schedule_file, python_path)
    print('Total Schedules Created:' + str(len(schedules)))


if __name__ == '__main__':
    cluster_name = ''
    argv = sys.argv[1:]
    if not argv:
        print('USAGE : main.py --perform_ist <cluster_name>    OR    main.py --update_cron <python_exe_path>')

    try:
        (opts, args) = getopt.getopt(argv, 'he:u:', ['perform_ist=',
                'update_cron='])
    except getopt.GetoptError:
        print('USAGE : main.py --perform_ist <cluster_name>    OR    main.py --update_cron <python_exe_path>')
        sys.exit(2)
    for (opt, arg) in opts:
        if opt == '-h':
            print('USAGE : main.py --perform_ist <cluster_name>    OR    main.py --update_cron <python_exe_path>')
            sys.exit()
        elif opt in ('-e', '--perform_ist'):
            cluster_name = arg

            # Start IST

            perform_ist(cluster_name, setting.STORE_CLUSTER_MAP,
                        setting.CURRENT_STORE_INVENTORY_FILE,
                        setting.BSQ_FILE,
                        setting.PROJECTED_PROBABILITY_FILE)
        elif opt in ('-u', '--update_cron'):

            print(arg)
            python_path = arg
            update_cron(setting.CRON_USER,
                        setting.CLUSTER_IST_FREQ_FILE, python_path)
