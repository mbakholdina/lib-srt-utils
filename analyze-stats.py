import pandas as pd
import matplotlib.pyplot as plt



def load_csv_stats(rcvcsv, sndcsv):
    rcv = pd.read_csv(rcvcsv, sep=",", skipinitialspace=True)
    snd = pd.read_csv(sndcsv, sep=",", skipinitialspace=True)
    return rcv, snd

def extract_features(rcv, snd):
    sent = snd['pktSent'].sum()
    rexmits = snd['pktRetrans'].sum()
    droped = rcv['pktRcvDrop'].sum()
    return (rexmits / sent) * 100, (droped / sent) * 100

def create_dataframe_take_1():
    columns = ['lossratio', 'rtt', 'sendrate', 'df']
    db = pd.DataFrame(columns = columns)

    path_prefix = '_stats_nak/_loss8_latency_'
    rcv_suffix = 'msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv'
    snd_suffix = 'local/2-srt-xtransmit-stats-snd.csv'

    df_experiment = pd.DataFrame(columns = ["REXMITS", "DROPS"])
    df_experiment.index.name = 'latency'
    for latency in range(25, 160, 5):
        path = path_prefix + str(latency) + '/'
        rcv, snd = load_csv_stats(path + rcv_suffix, path + snd_suffix)
        rex, drop = extract_features(rcv, snd)
        df_experiment.loc[latency] = [rex, drop]
        
    print(df_experiment)
    db = db.append({8, 54, 7, df_experiment}, ignore_index=True)
    print(db)

def create_dataframe():
    # TODO: add 'alg' column
    columns = ['lossratio', 'rtt', 'sendrate', 'algo', 'latency', "rexmits", "drops"]
    db = pd.DataFrame(columns = columns)

    path_prefix = '_stats_nak/_loss8_latency_'
    rcv_suffix = 'msharabayko@10.129.10.165/1-srt-xtransmit-stats-rcv.csv'
    snd_suffix = 'local/2-srt-xtransmit-stats-snd.csv'

    for algo in ['nak', 'tango']:
        path_prefix = '_stats_nak/_loss8_latency_' if algo == 'nak' else '_stats_nak_tango/_loss8_latency_'
        for latency in range(25, 160, 5):
            path = path_prefix + str(latency) + '/'
            rcv, snd = load_csv_stats(path + rcv_suffix, path + snd_suffix)
            rex, drop = extract_features(rcv, snd)
            row = pd.DataFrame([[8, 54, 7, algo, latency, rex, drop]], columns = columns)
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

def load_dataset(desc, root_dir):
    columns = ['lossratio', 'rtt', 'sendrate', 'algo', 'latency', "rexmits", "drops"]
    db = pd.DataFrame(columns = columns)

    path_prefix = root_dir + desc['path']
    print(path_prefix)
    algo         = desc['name']
    loss         = desc['loss']
    rtt          = desc['rtt']
    rate         = desc['rate']
    latency_min  = desc['latency_min']
    latency_max  = desc['latency_max']
    latency_step = desc['latency_step']

    for latency in range(latency_min, latency_max + latency_step, latency_step):
        path = path_prefix + desc['fldr'].format(desc['loss'], desc['rate'], latency)
        print(f"Load {path}")
        rcvcsv = path + '/'+ desc['rcvcsv']
        sndcsv = path + '/'+ desc['sndcsv']
        rcv, snd = load_csv_stats(rcvcsv, sndcsv)
        rex, drop = extract_features(rcv, snd)
        row = pd.DataFrame([[loss, rtt, rate, algo, latency, rex, drop]], columns = columns)
        db = db.append(row)

    return db


def load_datasets():
    periodic_nak_loss8 = {
        'name': 'Periodic NAK',
        'path': 'periodic_nak/',
        'loss': 8,
        'rate': 7,
        'rtt': 54,
        'latency_min': 25,
        'latency_max': 250,
        'latency_step': 5,
        'fldr': 'loss{}_rate{}_latency_{}',
        'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
        'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    }

    periodic_nak_off_loss8 = {
        'name': 'Periodic NAK Off',
        'path': 'periodic_nak_off/',
        'loss': 8,
        'rate': 7,
        'rtt': 54,
        'latency_min': 25,
        'latency_max': 250,
        'latency_step': 5,
        'fldr': 'loss{}_rate{}_latency_{}',
        'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
        'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    }

    periodic_nak_tango2_loss8 = {
        'name': 'Periodic NAK Tango2',
        'path': 'periodic_nak_tango_2/',
        'loss': 8,
        'rate': 7,
        'rtt': 54,
        'latency_min': 25,
        'latency_max': 250,
        'latency_step': 5,
        'fldr': 'loss{}_rate{}_latency_{}',
        'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
        'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    }

    periodic_nak_loss4 = {
        'name': 'Periodic NAK',
        'path': 'periodic_nak/',
        'loss': 4,
        'rate': 7,
        'rtt': 54,
        'latency_min': 25,
        'latency_max': 250,
        'latency_step': 5,
        'fldr': 'loss{}_rate{}_latency_{}',
        'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
        'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    }

    periodic_nak_tango2_loss4 = {
        'name': 'Periodic NAK Tango2',
        'path': 'periodic_nak_tango_2/',
        'loss': 4,
        'rate': 7,
        'rtt': 54,
        'latency_min': 25,
        'latency_max': 250,
        'latency_step': 5,
        'fldr': 'loss{}_rate{}_latency_{}',
        'rcvcsv': '1-srt-xtransmit-stats-rcv.csv',
        'sndcsv': '2-srt-xtransmit-stats-snd.csv'
    }
    
    root_path = '..\\Periodic-NAK-DataSet-1\\'
    db = load_dataset(periodic_nak_loss8, root_path)
    #db = db.append(load_dataset(periodic_nak_off_loss8, root_path))
    #db = db.append(load_dataset(periodic_nak_tango2_loss8, root_path))
    db = db.append(load_dataset(periodic_nak_loss4, root_path))
    db = db.append(load_dataset(periodic_nak_tango2_loss4, root_path))
    print(db)

    #algs = [periodic_nak_loss8['name'], periodic_nak_off_loss8['name'], periodic_nak_tango2_loss8['name']]
    #plot_rexmit_drops(db, 7, 8, 54, algs)

    algs = [periodic_nak_loss4['name'], periodic_nak_tango2_loss4['name']]
    plot_rexmit_drops(db, 7, 4, 54, algs)


def main():
    #create_dataframe()
    load_datasets()

if __name__ == '__main__':
	main()