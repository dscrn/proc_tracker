import psutil
import pandas as pd


if __name__ == '__main__':

    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.max_rows', None)

    process_list = []
    for proc in psutil.process_iter():
        process_list.append(proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 'create_time', 'memory_percent', 'memory_info']))

    # print(process_list)
    processes = pd.DataFrame(columns=['pid', 'name', 'cpu_percent', 'create_time', 'memory_percent', 'memory_info'])
    for each in process_list:
        processes = pd.concat([processes, pd.DataFrame.from_dict(each)], ignore_index=True)

    processes = processes.groupby('name').sum().sort_values(by=['cpu_percent', 'memory_percent'], ascending=False)
    # processes = processes[processes['cpu_percent'] == 0]
    print(processes)

