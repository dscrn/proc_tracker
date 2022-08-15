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


def driver(cursor):
    while True:
        procs = get_processes()
        procs.reset_index(inplace=True)
        procs = procs[['name']]
        procs = list(procs.itertuples(index=False, name=None))

        print('CURRENT PROCESSES: \n', procs)
        prev_processes = query_processes(cursor, sql_query)
        if len(prev_processes) == 0:
            cursor.executemany(cmd, procs)
            con.commit()
        else:
            new_proc_list = []
            for each in range(len(procs)):
                matched = False
                for proc in range(len(prev_processes)):
                    if procs[each] == prev_processes[proc]:
                        matched = True
                if not matched:
                    new_proc_list.append(procs[each])
            print('NEW PROCESSES DETECTED: \n', new_proc_list)
            cursor.executemany(cmd, new_proc_list)
            cursor.executemany(cmd_new, new_proc_list)
            con.commit()

        time.sleep(30)
        signal.signal(signal.SIGINT, sigint_handler)
        print('PROCESSES IN DB: \n', prev_processes)


def query_processes(cursor, sql):
    p_list = []
    for row in cur.execute(sql):
        p_list.append(row)
    return p_list


if __name__ == '__main__':

    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.max_rows', None)

    con = sqlite3.connect('process.db')
    cur = con.cursor()
    cmd = "INSERT INTO processes VALUES(?)"
    cmd_new = "INSERT INTO new_procs VALUES(?)"
    sql_query = 'SELECT name FROM processes'

    if not Path('process.db').exists():
        cur.execute('''CREATE TABLE processes (name text)''')
        con.commit()
    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='new_procs' ''')
    if cur.fetchone()[0] == 0:
        cur.execute(''' CREATE TABLE new_procs (name text)''')
        con.commit()

    driver(cur)



    # print(results[2][0])

