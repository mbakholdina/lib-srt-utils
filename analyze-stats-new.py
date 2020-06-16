import pathlib
import re

import matplotlib.pyplot as plt
import pandas as pd


######### Loading datasets #########
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


def load_datasets():
    root_path = '/Users/msharabayko/projects/srt/lib-srt-utils/_send_buffer_datasets_12.06.20/'

    # TODO: Load datasets for several folders, 1 folder corresponds to 1 algo
    # TODO: Define a set of path + description (algo as a start)
    algo = 'Periodic NAK'
    algo_path = 'periodic_nak/'
    schema = '_rtt{}_loss{}_sendrate{}_latency{}'
    rcvcsv = '1-srt-xtransmit-stats-rcv.csv'
    sndcsv = '2-srt-xtransmit-stats-snd.csv'

    algo_dir = pathlib.Path(root_path + algo_path)

    # Find all directories with experiments results in algo_dir
    expers_dirs = [f for f in algo_dir.iterdir() if f.is_dir()]

    cols = ['rtt', 'loss', 'sendrate', 'latency', 'algo', 'rexmits', 'drops', 'rcvbuffill']
    df = pd.DataFrame(columns=cols)

    for dirpath in expers_dirs:
        print(f'Extracting metrics for : {dirpath}')
        rcvcsv_path = dirpath / rcvcsv
        sndcsv_path = dirpath / sndcsv

        dirname = dirpath.relative_to(algo_dir)

        # TODO: Check that directory name corresponds to the defined schema
        # If not, skip metrics extraction

        # Parse directory name in order to extract params values
        params = [int(s) for s in re.findall(r'\d+', str(dirname))]

        # TODO: This is hard-coded with regards to defined schema. Improve this.
        # As a start check that dirname corresponds to a defined schema will be enough.
        rtt = params[0]
        loss = params[1]
        sendrate = params[2]
        latency = params[3]
        
        rcv, snd = load_csv_stats(rcvcsv_path, sndcsv_path)
        rex, drop, rcvbuf = extract_features(rcv, snd)
        row = pd.DataFrame([[rtt, loss, sendrate, latency, algo, rex, drop, rcvbuf]], columns=cols)
        df = df.append(row)

    df.sort_values(['rtt', 'loss', 'sendrate', 'latency'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(df)
    return df


######### Analysis #########

def calc_rcv_buf_bytes(rtt_ms, bps, latency_ms):
    return (latency_ms + rtt_ms / 2) * bps / 1000 / 8


def plot_rcv_buffer_fullness(df, rtt, loss, sendrate, algs):
    df['latencyxrtt'] = df.latency / df.rtt

    f, (ax1) = plt.subplots(1, 1, sharex=True)
    f.canvas.set_window_title('Test')

    expected = pd.DataFrame()

    for alg in algs:
        indexer_alg = df.algo == alg
        indexer = indexer_alg & (df.loss == loss) & (df.sendrate == sendrate) & (df.rtt == rtt)

        if df[indexer].empty:
            print(f"ERROR! No data for {alg}.")
            continue

        df[indexer].plot(x='latencyxrtt', y='rcvbuffill', kind="line", linestyle='-', marker='o', ax=ax1)
        if expected.empty:
            expected = df[indexer][['latency', 'latencyxrtt', 'rcvbuffill']].copy()

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


def main():
    #create_dataframe()
    df = load_datasets()

    rtt = 20
    loss = 4
    sendrate = 10
    algs = ['Periodic NAK']
    plot_rcv_buffer_fullness(df, rtt, loss, sendrate, algs)


if __name__ == '__main__':
    main()