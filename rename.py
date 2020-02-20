import shutil, os
# files = ['file1.txt', 'file2.txt', 'file3.txt']
# for f in files:
#     shutil.copy(f, 'dest_folder')


import click
import sys

def main():
    path = 'c:\\Users\\maxlo\\Projects\\srt\\Periodic-NAK-DataSet-1\\periodic_nak\\'

    for src_dir, dirs, files in os.walk(path):
        print(src_dir)
        print(dirs)
        print(files)

        subfolders = ['msharabayko@10.129.10.165', 'local']
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