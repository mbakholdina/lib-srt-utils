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
    loss_reports = snd['pktSndLoss'].sum()
    lost = rcv['pktRcvLoss'].sum()
    retransm = snd['pktRetrans'].sum()
    drops = rcv['pktRcvDrop'].sum()

    loss_reports_ratio = loss_reports * 100 / sent
    retransm_ratio = retransm * 100 / sent
    loss_ratio = lost * 100 / sent
    drop_ratio = drops * 100 / sent

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
        'loss_reports_ratio': loss_reports_ratio,
        'retransm_ratio': retransm_ratio,
        'loss_ratio': loss_ratio,
        'drop_ratio': drop_ratio,
        'snd_buffer_max_fullness': snd_buffer_max_fullness,
        'rcv_buffer_max_fullness': rcv_buffer_max_fullness,
        'snd_buffer_min_timespan': snd_buffer_min_timespan,
        'snd_buffer_max_timespan': snd_buffer_max_timespan,
        'snd_buffer_mean_timespan': snd_buffer_mean_timespan,
    }


def load_datasets(root_path, algos):
    # TODO: Load datasets for several folders, 1 folder corresponds to 1 algo
    assert(len(algos) == 1)
    algo, algo_path = algos[0]

    # TODO: Make as function parameters
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
        'loss_reports_ratio',
        'retransm_ratio',
        'loss_ratio',
        'drop_ratio',
        'snd_buffer_max_fullness',
        'rcv_buffer_max_fullness',
        'snd_buffer_min_timespan',
        'snd_buffer_max_timespan',
        'snd_buffer_mean_timespan',
    ]
    df = pd.DataFrame(columns=cols)

    for dirpath in expers_dirs:
        # print(f'Extracting metrics for : {dirpath}')
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
                    features['loss_reports_ratio'],
                    features['retransm_ratio'],
                    features['loss_ratio'],
                    features['drop_ratio'],
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

    df['latencyxrtt'] = df.latency / df.rtt

    df = df.astype(
        {
            'rtt': 'int32',
            'loss': 'int32',
            'sendrate': 'int32',
            'latency': 'int32',
            'snd_buffer_max_fullness': 'float64',
            'rcv_buffer_max_fullness': 'float64',
            'snd_buffer_min_timespan': 'float64',
            'snd_buffer_max_timespan': 'float64',
            'latencyxrtt': 'float64',
        }
    )

    df.sort_values(['rtt', 'loss', 'sendrate', 'latency'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


######### Analysis #########

# TODO: Move receiver buffer logic to a separate file
def calc_rcv_buf_bytes(rtt_ms, bps, latency_ms):
    return (latency_ms + rtt_ms / 2) * bps / 1000 / 8


def plot_rcv_buffer_fullness(df, rtt, loss, sendrate, algs):
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


def plot_snd_buffer_timespan(df):
    """ Plot sender buffer timespan. """
    # TODO: Loop through algos

    # Calculating prediction
    df['snd_buffer_min_timespan_predict'] = df['rtt']
    df['snd_buffer_max_timespan_predict'] = df['rtt'] + 10

    f, ax = plt.subplots(figsize=(12,6))
    # f.canvas.set_window_title('Test')

    df.plot(x='latencyxrtt', y='snd_buffer_max_timespan', kind="line", linestyle='-', marker='o', ax=ax)
    df.plot(x='latencyxrtt', y='snd_buffer_min_timespan', kind="line", linestyle='-', marker='o', ax=ax)
    df.plot(x='latencyxrtt', y='snd_buffer_mean_timespan', kind="line", linestyle='-', marker='o', ax=ax)

    ax.fill_between(
        df['latencyxrtt'],
        df['snd_buffer_min_timespan_predict'],
        df['snd_buffer_max_timespan_predict'],
        color='green',
        alpha=0.3,
        label='prediction'
    )

    loss = df.loss.iloc[0]
    rtt = df.rtt.iloc[0]
    sendrate = df.sendrate.iloc[0]
    f.suptitle(f'RTT {rtt}ms, Loss Ratio {loss}%, Sendrate {sendrate} Mbps')

    ax.set_title('Sender buffer timespan')
    ax.set_ylabel('Milliseconds (ms)')
    ax.set_xlabel('Latency (times RTT)')
    ax.legend(loc='upper right')

    plt.show()


def confidence_interval_95(series):
    """ Return 95% confidence interval for series. """
    return (
        round(series.quantile(0.025), 2),
        round(series.quantile(0.975), 2)
    )


def confidence_interval_99(series):
    """ Return 99% confidence interval for series. """
    return (
        round(series.quantile(0.005), 2),
        round(series.quantile(0.995), 2)
    )


def define_percentage(algo_dir: str, starts_with: str, sndcsv: str, rtt):
    """ Define percentage of data out of [RTT, RTT + 10] ms boundaries. """
    series = pd.Series([])

    algo_dir = pathlib.Path(algo_dir)
    # Find all directories with experiments results in algo_dir
    expers_dirs = [f for f in algo_dir.iterdir() if f.is_dir()]

    for dirpath in expers_dirs:
        dirname = dirpath.relative_to(algo_dir)

        if not str(dirname).startswith(starts_with):
            continue

        sndcsv_path = dirpath / sndcsv

        single_df = pd.read_csv(sndcsv_path, sep=",", skipinitialspace=True)
        to_append = single_df['msSndBuf']
        # Drop the first row where msSndBuf=0
        to_append = to_append.iloc[1:]
        series = series.append(to_append)

    # Sort the values and calculate percentage
    series.sort_values(inplace=True)

    n = series.count()
    perc_below = series[lambda x: x < rtt].count() * 100 / n
    perc_higher = series[lambda x: x > rtt + 10].count() * 100 / n
    perc_total = perc_below + perc_higher

    # Plot histogram
    f, ax = plt.subplots()
    f.suptitle(f'Starts with {starts_with}')
    series.hist()

    ax.axvline(x=rtt, color='r', label='RTT')
    ax.axvline(x=rtt+10, color='r', label='RTT+10')
    ax.legend(loc='upper right')

    plt.show()

    return (
        round(perc_total, 2),
        round(perc_below, 2),
        round(perc_higher, 2),
        confidence_interval_95(series),
        confidence_interval_99(series)
    )


if __name__ == '__main__':
    main()