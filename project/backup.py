#!/usr/bin/env python3

import argparse
import datetime
import os
import sys

#######################################################################################################################################################################
# How script run:  /usr/bin/python3  script_dir/backup.py days_saved  -ho 127.0.0.1 -d database_name -du user_name -dp user_password -fo bkp.dump -ld your_directory  #
# How edit cron tab: run crontab -e (add or update jobs in crontab)                                                                                                   #
# Cron frequency map:                                                                                                                                                 #
#     *      *     *      *         *                                                                                                                                 #
#   minute  hour  day   month   day(week)                                                                                                                             #
# Example Cron job every night at midnight:                                                                                                                           #
# 0 0 * * * /usr/bin/python3  script_dir/backup.py days_saved  -ho 127.0.0.1 -d database_name -du user_name -dp user_password -fo bkp.dump -ld your_directory         #                                                                                                                                                          #
# #####################################################################################################################################################################


def get_arguments():
    parser = argparse.ArgumentParser()

    # Parsing arguments for pg_dump command
    parser.add_argument("-ho", "--host", action="store", type=str)
    parser.add_argument("-d", "--db_name", action="store", type=str)
    parser.add_argument("-du", "--db_username", action="store", type=str)
    parser.add_argument("-dp", "--db_password", action="store", type=str)
    parser.add_argument("-fo", "--file_output", action="store", type=str)
    parser.add_argument("-ld", "--local_dir", action="store", type=str)
    parser.add_argument("-ds", "--days_saved", action="store", type=int)
    return parser.parse_args(sys.argv[1:])


def download_file_path(args):
    if not os.path.exists(args.local_dir):
        os.mkdir(args.local_dir)
    d = datetime.datetime.now()

    list_of_files = os.listdir(args.local_dir)
    full_path = [args.local_dir+"/{0}".format(x) for x in list_of_files]

    # delete oldest file in directory when number of files reaches a threshold (5 for this case)
    if len(list_of_files) >= args.days_saved:
        oldest_file = min(full_path, key=os.path.getctime)
        os.remove(oldest_file)

    # create filepath with datetime for the backup file
    download_file_path = os.path.join(
        args.local_dir, ('%s-%s' % (d.strftime('%Y%m%d%H%M'), args.file_output)))
    return download_file_path


def backup(args):
    file_path = download_file_path(args)
    backup_command = "export PGPASSWORD='%s' && pg_dump -h %s -U %s %s -w --clean -F c -f %s.tar.gz" % \
        (args.db_password, args.host, args.db_username, args.db_name, file_path)

    print('Running backup process...')
    os.system(backup_command)


if __name__ == "__main__":
    args = get_arguments()

    # setting default values
    if not args.file_output:
        args.file_output = args.db_name

    backup(args)
    print('Database backup done at: ', args.local_dir)
