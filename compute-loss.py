import click
import pandas as pd
import sys

@click.command()
@click.argument(
    'rcvcsv'
)
@click.argument(
    'sndcsv'
)
def main(rcvcsv, sndcsv):
    rcv = pd.read_csv(rcvcsv, sep=",", skipinitialspace=True)
    snd = pd.read_csv(sndcsv, sep=",", skipinitialspace=True)

    sent = snd['pktSent'].sum()
    rexmits = snd['pktRetrans'].sum()
    droped = rcv['pktRcvDrop'].sum()
    print(f"{(rexmits / sent) * 100: .3f} {(droped / sent) * 100: .3f}")
    print(f"{(rexmits / sent) * 100: .3f} {(droped / sent) * 100: .3f}", file=sys.stderr)
    return

if __name__ == '__main__':
	main()