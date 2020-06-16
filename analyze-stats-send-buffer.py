import pathlib
import re

import matplotlib.pyplot as plt
import pandas as pd


def load_csv_stats(rcvcsv, sndcsv):
    rcv = pd.read_csv(rcvcsv, sep=",", skipinitialspace=True)
    snd = pd.read_csv(sndcsv, sep=",", skipinitialspace=True)
    return rcv, snd


def extract_features(rcv, snd):
    sent = snd['pktSent'].sum()
    rexmits = snd['pktRetrans'].sum()
    droped = rcv['pktRcvDrop'].sum()

    rcv_buffer_size = rcv['byteAvailRcvBuf'].iloc[0]
    fullness = rcv_buffer_size - rcv['byteAvailRcvBuf']
    max_fullness = fullness.max()

    return (rexmits / sent) * 100, (droped / sent) * 100, max_fullness


def create_dataframe():
    # TODO: add 'alg' column
    columns = ['lossratio', 'rtt', 'sendrate', 'algo', 'latency', "rexmits", "drops", "rcvbuffill"]
    db = pd.DataFrame(columns = columns)

    path_prefix = '_stats_nak/_loss8_latency_'
    rcv_suffix = 'msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv'
    snd_suffix = 'local/2-srt-xtransmit-stats-snd.csv'

    for algo in ['nak', 'tango']:
        path_prefix = '_stats_nak/_loss8_latency_' if algo == 'nak' else '_stats_nak_tango/_loss8_latency_'
        for latency in range(25, 160, 5):
            path = path_prefix + str(latency) + '/'
            rcv, snd = load_csv_stats(path + rcv_suffix, path + snd_suffix)
            rex, drop, rcvbuffill = extract_features(rcv, snd)
            row = pd.DataFrame([[8, 54, 7, algo, latency, rex, drop, rcvbuffill]], columns = columns)
            db = db.append(row)

    db['latenxyxrtt'] = db.latency / db.rtt

    f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    f.canvas.set_window_title('Test')
    
    indexer_nak   = db['algo'] == 'nak'
    indexer_tango = db['algo'] == 'tango'

    db[indexer_nak].plot(x='latenxyxrtt',y='drops', kind="line", linestyle='-', marker='o', ax=ax1)
    db[indexer_tango].plot(x='latenxyxrtt',y='drops', kind="line", linestyle='-', marker='o', ax=ax1)
    ax1.set_title('Drops')
    ax1.legend(["Periodic NAK", "Tango 2"])
    ax1.set_ylabel("%")
    ax1.set_xlabel("Latency (times RTT)")

    db[indexer_nak].plot(x='latenxyxrtt',y='rexmits', kind="line", linestyle='-', marker='x', ax=ax2)
    db[indexer_tango].plot(x='latenxyxrtt',y='rexmits', kind="line", linestyle='-', marker='x', ax=ax2)
    ax2.set_title('Rexmits')
    ax2.legend(["Periodic NAK", "Tango 2"])
    ax2.set_ylabel("%")
    ax2.set_xlabel("Latency (times RTT)")
    plt.show()

    print(db)


def plot_rexmit_drops(db, sendrate, loss, rtt, algs):
    db['latenxyxrtt'] = db.latency / db.rtt

    f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    f.canvas.set_window_title('Test')

    for alg in algs:
        indexer_alg = db.algo == alg
        indexer = indexer_alg & (db.lossratio == loss) & (db.sendrate == sendrate) & (db.rtt == rtt)
        if db[indexer].empty:
            print(f"ERROR! No data for {alg}.")
            continue

        db[indexer].plot(x='latenxyxrtt', y='drops',   kind="line", linestyle='-', marker='o', ax=ax1)
        db[indexer].plot(x='latenxyxrtt', y='rexmits', kind="line", linestyle='-', marker='x', ax=ax2)

    f.suptitle('Loss {}%, RTT {}ms, Sendrate {} Mbps'.format(loss, rtt, sendrate))

    ax1.set_title('Drops')
    ax1.legend(algs)
    ax1.set_ylabel("Dropped packets, %")
    ax1.set_xlabel("Latency (times RTT)")

    ax2.set_title('Rexmits')
    ax2.legend(algs)
    ax2.set_ylabel("Resent packets, %")
    ax2.set_xlabel("Latency (times RTT)")
    plt.show()


def calc_rcv_buf_bytes(rtt_ms, bps, latency_ms):
    return (latency_ms + rtt_ms / 2) * bps / 1000 / 8


def plot_buffer_fullness(db, sendrate, loss, rtt, algs):
    db['latencyxrtt'] = db.latency / db.rtt

    f, (ax1) = plt.subplots(1, 1, sharex=True)
    f.canvas.set_window_title('Test')

    expected = pd.DataFrame()

    for alg in algs:
        indexer_alg = db.algo == alg
        indexer = indexer_alg & (db.lossratio == loss) & (db.sendrate == sendrate) & (db.rtt == rtt)

        if db[indexer].empty:
            print(f"ERROR! No data for {alg}.")
            continue

        db[indexer].plot(x='latencyxrtt', y='rcvbuffill', kind="line", linestyle='-', marker='o', ax=ax1)
        if expected.empty:
            expected = db[indexer][['latency', 'latencyxrtt', 'rcvbuffill']].copy()

    # TODO: This can be improved
    for _, row in expected.iterrows():
        latency_ms = row['latency']
        row['rcvbuffill'] = calc_rcv_buf_bytes(rtt, sendrate * 1_000_000, latency_ms)

    expected.plot(x='latencyxrtt', y='rcvbuffill', kind="line", linestyle='--', marker='o', ax=ax1)

    f.suptitle('Loss {}%, RTT {}ms, Sendrate {} Mbps'.format(loss, rtt, sendrate))

    ax1.set_title('Receiver buffer fullness')
    ax1.legend(algs + ['Prediction'])
    ax1.set_ylabel("Bytes")
    ax1.set_xlabel("Latency (times RTT)")

    plt.show()


# def load_dataset(desc, root_dir):
#     columns = ['lossratio', 'rtt', 'sendrate', 'algo', 'latency', "rexmits", "drops", "rcvbuffill"]
#     db = pd.DataFrame(columns = columns)

#     path_prefix = root_dir + desc['path']
#     print(path_prefix)
#     algo         = desc['name']
#     loss         = desc['loss']
#     rtt          = desc['rtt']
#     rate         = desc['rate']
#     latency_min  = desc['latency_min']
#     latency_max  = desc['latency_max']
#     latency_step = desc['latency_step']

#     for latency in range(latency_min, latency_max + latency_step, latency_step):
#         path = path_prefix + desc['fldr'].format(desc['loss'], desc['rate'], latency)
#         print(f"Load {path}")
#         rcvcsv = path + '/'+ desc['rcvcsv']
#         sndcsv = path + '/'+ desc['sndcsv']
#         rcv, snd = load_csv_stats(rcvcsv, sndcsv)
#         rex, drop, rcvbuf = extract_features(rcv, snd)
#         row = pd.DataFrame([[loss, rtt, rate, algo, latency, rex, drop, rcvbuf]], columns = columns)
#         db = db.append(row)

#     return db


def load_datasets():
    # root_path = 'd:\\tests\\srt\\Periodic-NAK-DataSet-1\\'
    root_path = '/Users/msharabayko/projects/srt/lib-srt-utils/_periodic_nak_datasets_27.02.20/'

    # TODO: Load datasets for several folders
    # TODO: Define a set of path + description (algo as a start)
    path = 'periodic_nak/'
    algo = 'Periodic NAK'

    schema = 'loss{}_rate{}_latency_{}'
    rcvcsv = '1-srt-xtransmit-stats-rcv.csv'
    sndcsv = '2-srt-xtransmit-stats-snd.csv'

    results_dir = pathlib.Path(root_path + path)

    # Find all directories with experiments results in results_dir
    exper_res_dirs = [f for f in results_dir.iterdir() if f.is_dir()]
    # print(exper_res_dirs)

    columns = ['lossratio', 'rtt', 'sendrate', 'algo', 'latency', "rexmits", "drops", "rcvbuffill"]
    db = pd.DataFrame(columns = columns)

    for dirpath in exper_res_dirs:
        print(f'Extracting metrics for : {dirpath}')
        rcvcsv_path = dirpath / rcvcsv
        sndcsv_path = dirpath / sndcsv

        dirname = dirpath.relative_to(results_dir)

        # TODO: Check that directory name corresponds to defined schema
        # If not, skip metrics extraction

        # Parse directory name in order to extract params values
        params = [int(s) for s in re.findall(r'\d+', str(dirname))]

        # TODO: Improve this
        loss = params[0]
        rate = params[1]
        latency = params[2]
        rtt = 54
        
        rcv, snd = load_csv_stats(rcvcsv_path, sndcsv_path)
        rex, drop, rcvbuf = extract_features(rcv, snd)
        row = pd.DataFrame([[loss, rtt, rate, algo, latency, rex, drop, rcvbuf]], columns = columns)
        db = db.append(row)

    
    # periodic_nak_loss8 = {
    #     'name': 'Periodic NAK',
    #     'path': 'periodic_nak/',
    #     'loss': 8,
    #     'rate': 7,
    #     'rtt': 54,
    #     'latency_min': 25,
    #     'latency_max': 250,
    #     'latency_step': 5,
    #     'fldr': 'loss{}_rate{}_latency_{}',
    #     'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
    #     'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    # }

    # periodic_nak_loss4 = periodic_nak_loss8.copy()
    # periodic_nak_loss4['loss'] = 4

    # periodic_nak_loss0 = periodic_nak_loss8.copy()
    # periodic_nak_loss0['loss'] = 0

    # periodic_nak_off_loss8 = {
    #     'name': 'Periodic NAK Off',
    #     'path': 'periodic_nak_off/',
    #     'loss': 8,
    #     'rate': 7,
    #     'rtt': 54,
    #     'latency_min': 25,
    #     'latency_max': 250,
    #     'latency_step': 5,
    #     'fldr': 'loss{}_rate{}_latency_{}',
    #     'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
    #     'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    # }

    # periodic_nak_off_loss4 = periodic_nak_off_loss8.copy()
    # periodic_nak_off_loss4['loss'] = 4
    # periodic_nak_off_loss4['latency_max'] = 190

    # periodic_nak_off_loss0 = periodic_nak_off_loss8.copy()
    # periodic_nak_off_loss0['loss'] = 0

    # periodic_nak_tango2_loss8 = {
    #     'name': 'Periodic NAK Tango2',
    #     'path': 'periodic_nak_tango_2/',
    #     'loss': 8,
    #     'rate': 7,
    #     'rtt': 54,
    #     'latency_min': 25,
    #     'latency_max': 250,
    #     'latency_step': 5,
    #     'fldr': 'loss{}_rate{}_latency_{}',
    #     'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
    #     'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    # }

    # periodic_nak_tango2_loss4 = periodic_nak_tango2_loss8.copy()
    # periodic_nak_tango2_loss4['loss'] = 4

    # periodic_nak_tango2_loss0 = periodic_nak_tango2_loss4.copy()
    # periodic_nak_tango2_loss0['loss'] = 0
    
    
    # db = load_dataset(periodic_nak_loss8, root_path) \
    #     .append(load_dataset(periodic_nak_loss4, root_path)) \
    #     .append(load_dataset(periodic_nak_loss0, root_path))
    # db = db.append(load_dataset(periodic_nak_off_loss8, root_path)) \
    #     .append(load_dataset(periodic_nak_off_loss4, root_path)) \
    #     .append(load_dataset(periodic_nak_off_loss0, root_path))
    # db = db.append(load_dataset(periodic_nak_tango2_loss8, root_path))
    # db = db.append(load_dataset(periodic_nak_tango2_loss4, root_path))
    # db = db.append(load_dataset(periodic_nak_tango2_loss0, root_path))
    # print(db)
    # print(periodic_nak_tango2_loss8)

    #algs = [periodic_nak_loss8['name'], periodic_nak_off_loss8['name'], periodic_nak_tango2_loss8['name']]
    #plot_rexmit_drops(db, 7, 8, 54, algs)

    algs = [algo]
    #plot_rexmit_drops(db, 7, 8, 54, algs)

    plot_buffer_fullness(db, 7, 8, 54, algs)


def main():
    #create_dataframe()
    load_datasets()

if __name__ == '__main__':
    main()