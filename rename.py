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

where path is _send_buffer_datasets_12.06.20/
"""
import os
import shutil
import sys

# import click


def main():
    # TODO: Command line
    path = '/Users/msharabayko/projects/srt/lib-srt-utils/_tmp/'
    subfolders = ['haivision@10.129.128.51', 'haivision@10.129.128.52']

    for src_dir, dirs, files in os.walk(path):
        print(src_dir)
        print(dirs)
        print(files)

        for subfolder in subfolders:
            if src_dir.find(subfolder) == -1:    
                continue

            dst_dir = src_dir.replace(subfolder, '', 1)

            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)

                if os.path.exists(src_file) == False:
                    print(f"ERROR source file does not exist {src_file}")
                    continue

                if os.path.exists(dst_file):
                    os.remove(dst_file)

                print(f'Move {src_file} to {dst_file}')
                try:
                    shutil.move(src_file, dst_dir)
                except:
                    pass

                if os.path.exists(src_dir):
                    os.rmdir(src_dir)


if __name__ == '__main__':
    main()