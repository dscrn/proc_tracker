import psutil
import pandas as pd
import time

def get_processes():
    process_list = []
    for proc in psutil.process_iter():
        process_list.append(proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 'create_time', 'memory_percent', 'memory_info']))

    # print(process_list)
    processes = pd.DataFrame(columns=['pid', 'name', 'cpu_percent', 'create_time', 'memory_percent', 'memory_info'])
    for each in process_list:
        processes = pd.concat([processes, pd.DataFrame.from_dict(each)], ignore_index=True)

    processes = processes.groupby('name').sum().sort_values(by=['cpu_percent', 'memory_percent'], ascending=False)
    return processes


def driver():
    while True:
        procs = get_processes()
        time.sleep(30)
        return procs


if __name__ == '__main__':

    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.max_rows', None)

    stats = driver()
    print(stats)


