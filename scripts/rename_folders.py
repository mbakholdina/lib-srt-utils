import os
import shutil
import sys

import click


def _subfolder_to_list(ctx, param, value):
    return list(value)


@click.command()
@click.argument(
    'root_folder',
    type=click.Path(exists=True)
)
@click.option(
    '--subfolder',
    help =  'Subfolder name',
    required=True,
    multiple=True,
    callback=_subfolder_to_list
)
def main(root_folder, subfolder):
    """
    Script-helper designed to move experiment results from subfolders to a root
    folder corresponding to a particular experiment,
    e.g., from subfolders haivision@10.129.128.51 and haivision@10.129.128.52

    _rtt20_loss0_sendrate10_latency10/haivision@10.129.128.51/2-srt-xtransmit-stats-snd.csv
    _rtt20_loss0_sendrate10_latency10/haivision@10.129.128.52/1-srt-xtransmit-stats-rcv.csv

    to a root folder _rtt20_loss0_sendrate10_latency10

    _rtt20_loss0_sendrate10_latency10/2-srt-xtransmit-stats-snd.csv
    _rtt20_loss0_sendrate10_latency10/1-srt-xtransmit-stats-rcv.csv

    This is done for all the experiment folders under path specified

    _send_buffer_datasets_12.06.20/_rtt20_loss0_sendrate10_latency10
    _send_buffer_datasets_12.06.20/_rtt20_loss0_sendrate10_latency20
    ...

    where path is _send_buffer_datasets_12.06.20/.

    To run the script use the following command:

    venv/bin/python -m scripts.rename_folders _send_buffer_datasets_12.06.20/
    --subfolder haivision@10.129.128.51 --subfolder haivision@10.129.128.52
    """
    for src_dir, dirs, files in os.walk(root_folder):
        if (not dirs) & (not files):
            print(f'ERROR: There are no directories or files in {src_dir}')

        for fldr in subfolder:
            if src_dir.find(fldr) == -1:
                continue

            dst_dir = src_dir.replace(fldr, '', 1)

            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)

                if os.path.exists(src_file) == False:
                    print(f"ERROR: Source file does not exist {src_file}")
                    continue

                if os.path.exists(dst_file):
                    os.remove(dst_file)

                try:
                    shutil.move(src_file, dst_dir)
                except:
                    pass

                if os.path.exists(src_dir):
                    os.rmdir(src_dir)


if __name__ == '__main__':
    main()
