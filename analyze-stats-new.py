import pathlib
import re

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


######### Loading datasets #########
def load_csv_stats(rcvcsv, sndcsv):
    print('load csv stats')
    rcv = pd.read_csv(rcvcsv, sep=",", skipinitialspace=True)
    snd = pd.read_csv(sndcsv, sep=",", skipinitialspace=True)
    return rcv, snd


def extract_features(rcv, snd):
    print('extract features')

    sent = snd['pktSent'].sum()
    rexmits = snd['pktRetrans'].sum()
    drops = rcv['pktRcvDrop'].sum()

    rexmits_ratio = rexmits * 100 / sent
    drops_ratio = drops * 100 / sent

    rcv_buffer_size = rcv['byteAvailRcvBuf'].iloc[0]
    rcv_buffer_fullness = rcv_buffer_size - rcv['byteAvailRcvBuf']
    rcv_buffer_max_fullness = rcv_buffer_fullness.max()

    snd_buffer_size = snd['byteAvailSndBuf'].iloc[0]
    snd_buffer_fullness = snd_buffer_size - snd['byteAvailSndBuf']
    snd_buffer_max_fullness = snd_buffer_fullness.max()

    # Drop the first row where msSndBuf=0
    snd_buffer_timespan = snd['msSndBuf'].iloc[1:]
    snd_buffer_min_timespan = snd_buffer_timespan.min()
    snd_buffer_max_timespan = snd_buffer_timespan.max()
    snd_buffer_mean_timespan = snd_buffer_timespan.mean()

    return {
        'rexmits_ratio': rexmits_ratio,
        'drops_ratio': drops_ratio,
        'snd_buffer_max_fullness': snd_buffer_max_fullness,
        'rcv_buffer_max_fullness': rcv_buffer_max_fullness,
        'snd_buffer_min_timespan': snd_buffer_min_timespan,
        'snd_buffer_max_timespan': snd_buffer_max_timespan,
        'snd_buffer_mean_timespan': snd_buffer_mean_timespan,
    }


# @st.cache
def load_datasets(root_path):
    print('load datasets')

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

    cols = [
        'rtt',
        'loss',
        'sendrate',
        'latency',
        'algo',
        'rexmits_ratio',
        'drops_ratio',
        'snd_buffer_max_fullness',
        'rcv_buffer_max_fullness',
        'snd_buffer_min_timespan',
        'snd_buffer_max_timespan',
        'snd_buffer_mean_timespan',
    ]
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
        features = extract_features(rcv, snd)

        row = pd.DataFrame(
            [
                [
                    rtt,
                    loss,
                    sendrate,
                    latency,
                    algo,
                    features['rexmits_ratio'],
                    features['drops_ratio'],
                    features['snd_buffer_max_fullness'],
                    features['rcv_buffer_max_fullness'],
                    features['snd_buffer_min_timespan'],
                    features['snd_buffer_max_timespan'],
                    features['snd_buffer_mean_timespan'],
                ]
            ],
            columns=cols
        )
        df = df.append(row)

    df.sort_values(['rtt', 'loss', 'sendrate', 'latency'], inplace=True)
    df.reset_index(drop=True, inplace=True)

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

    # plt.show()
    st.pyplot()


def plot_snd_buffer_timespan(df):
    # TODO: Loop through algos

    # TODO: Move to load_datasets
    df['latencyxrtt'] = df.latency / df.rtt

    f, (ax1) = plt.subplots(1, 1, sharex=True)
    f.canvas.set_window_title('Test')
    

    df.plot(x='latencyxrtt', y='snd_buffer_max_timespan', kind="line", linestyle='-', marker='o', ax=ax1)
    # df.plot(x='latencyxrtt', y='snd_buffer_min_timespan', kind="line", linestyle='-', marker='o', ax=ax1)

    loss = df.loss.iloc[0]
    rtt = df.rtt.iloc[0]
    sendrate = df.sendrate.iloc[0]
    f.suptitle('Loss {}%, RTT {}ms, Sendrate {} Mbps'.format(loss, rtt, sendrate))

    ax1.set_title('Sender buffer timespan')
    # ax1.legend(algs + ['Prediction'])
    ax1.set_ylabel("Milliseconds (ms)")
    ax1.set_xlabel("Latency (times RTT)")

    # TODO: Prediction

    plt.show()


def confidence_interval(series):
    return (series.quantile(0.025), series.quantile(0.975))


def main():
    root_path_30secs = '/Users/msharabayko/projects/srt/lib-srt-utils/_send_buffer_datasets_12.06.20_30secs/'

    ### For debugging ###
    df = load_datasets(root_path_30secs)
    print(df)

    tmp_df = df.groupby(['rtt', 'loss', 'sendrate', 'algo'])[['snd_buffer_min_timespan', 'snd_buffer_max_timespan', 'snd_buffer_mean_timespan']].agg(confidence_interval)
    print(tmp_df)

    # TODO: Remove from here aggregation by algos
    plot_dfs = df.groupby(['rtt', 'loss', 'sendrate', 'algo'])
    for group_name, group in plot_dfs:
        print(group_name)
        print(group)
        plot_snd_buffer_timespan(group)



    return

    ### End of debugging ###

    st.title('My first app')

    df = load_datasets(root_path_30secs)
    st.subheader('Result dataframe, 30 secs datasets')
    st.write(df)

    st.subheader('Receiver buffer fullness, 30 secs datasets')
    algs = ['Periodic NAK']
    # TODO: There is a bug when plotting multiple plots
    # https://github.com/streamlit/streamlit/issues/1440
    # Error message: MediaFileManager: Missing file 1c836691489ae0c9bb858e79fd64a7767687f879e06cad7a4eed5cea
    # plot_rcv_buffer_fullness(df, 20, 0, 10, algs)
    # plot_rcv_buffer_fullness(df, 20, 4, 10, algs)
    # plot_rcv_buffer_fullness(df, 20, 8, 10, algs)


if __name__ == '__main__':
    main()