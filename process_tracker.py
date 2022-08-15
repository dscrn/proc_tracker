import psutil
import pandas as pd
import time
import sqlite3
from os.path import exists
from pathlib import Path
import signal, sys


def get_processes():
    process_list = []
    for proc in psutil.process_iter():
        process_list.append(proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 'create_time', 'memory_percent', 'memory_info']))

    processes = pd.DataFrame(columns=['pid', 'name', 'cpu_percent', 'create_time', 'memory_percent', 'memory_info'])
    for each in process_list:
        processes = pd.concat([processes, pd.DataFrame.from_dict(each)], ignore_index=True)

    processes = processes.groupby('name').sum().sort_values(by=['cpu_percent', 'memory_percent'], ascending=False)
    return processes


def sigint_handler(signal, frame):
    sys.exit(0)


# loops until keyboard interrupt, in each loop it reads the current running processes and then queries for the
# previously detected processes. It diffs the two and adds newly detected processes to a "new processes" table
# and also then the previously detected processes table
def driver(cursor):
    while True:
        # produces current processes as tuple for sqlite insertion
        procs = get_processes()
        procs.reset_index(inplace=True)
        procs = procs[['name']]
        procs = list(procs.itertuples(index=False, name=None))
        print('CURRENT PROCESSES: \n', procs)

        # query previously written processes, diffs them to the ones currently running
        prev_processes = query_processes(cursor, select_processes)
        # first loop adds current processes if there are no previously detected processes for the first run
        if len(prev_processes) == 0:
            cursor.executemany(insert_processes, procs)
            con.commit()
        else:
            # compares results of query with current processes, append un-seen processes to list
            new_proc_list = []
            for each in range(len(procs)):
                matched = False
                for proc in range(len(prev_processes)):
                    if procs[each] == prev_processes[proc]:
                        matched = True
                if not matched:
                    new_proc_list.append(procs[each])
            print('NEW PROCESSES DETECTED: \n', new_proc_list)
            print('PROCESSES IN DB: \n', prev_processes)

            # add new processes into both the processes and new processes table and commit changes to database
            cursor.executemany(insert_processes, new_proc_list)
            cursor.executemany(insert_new_processes, new_proc_list)
            con.commit()

        # poll processes every 30 seconds
        time.sleep(30)

        # end main loop on keyboard interrupt
        signal.signal(signal.SIGINT, sigint_handler)


def query_processes(cursor, sql):
    p_list = []
    for row in cur.execute(sql):
        p_list.append(row)
    return p_list


if __name__ == '__main__':

    # set up pandas display options for testing
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.max_rows', None)

    # setup SQLITE database connection for inserting new processes into the tables as they are detected
    # also setting up cursor object for queries of the DB
    con = sqlite3.connect('process.db')
    cur = con.cursor()

    # set different queries as strings for readability
    insert_processes = "INSERT INTO processes VALUES(?)"
    insert_new_processes = "INSERT INTO new_procs VALUES(?)"
    select_processes = 'SELECT name FROM processes'

    if not Path('process.db').exists():
        cur.execute('''CREATE TABLE processes (name text)''')
        con.commit()
    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='new_procs' ''')
    if cur.fetchone()[0] == 0:
        cur.execute(''' CREATE TABLE new_procs (name text)''')
        con.commit()

    driver(cur)



