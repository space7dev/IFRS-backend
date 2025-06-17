import argparse
import datetime
import os
import sys

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Makes a postgres DB backup'

    """
    Command format:
    python3 manage.py backup --host=localhost --db_name=test \
    --db_username=rescalante --db_password=lightandreason --file_output=backup.sql --local_dir="/home/raquel/Documents
    """

    def add_arguments(self, parser):
        # parser = argparse.ArgumentParser()

        # Parsing arguments for pg_dump command
        parser.add_argument("-ho", "--host", action="store", type=str)
        parser.add_argument("-d", "--db_name", action="store", type=str)
        parser.add_argument("-du", "--db_username", action="store", type=str)
        parser.add_argument("-dp", "--db_password", action="store", type=str)
        parser.add_argument("-fo", "--file_output", action="store", type=str)
        parser.add_argument("-ld", "--local_dir", action="store", type=str)

    # def download_file_path(self, *args, **options):
    #     if not os.path.exists (options['local_dir']):
    #         os.mkdir (options['local_dir'])
    #     d = datetime.datetime.now()

    #     #create filepath with datetime for the backup file
    #     download_file_path= os.path.join(options['local_dir'], ('%s-%s'%(d.strftime('%Y%m%d%H%M'), options['file_output'])))
    #     return download_file_path

    def handle(self, *args, **options):

        # filepath
        if not os.path.exists(options['local_dir']):
            os.mkdir(options['local_dir'])

        d = datetime.datetime.now()

        # create filepath with datetime for the backup file
        download_file_path = os.path.join(
            options['local_dir'], ('%s-%s' % (d.strftime('%Y%m%d%H%M'), options['file_output'])))

        # setting default values
        if not options['file_output']:
            options['file_output'] = options['db_name']

        file_path = download_file_path

        backup_command = "export PGPASSWORD='%s' && pg_dump -h %s -U %s %s -w --clean > %s" % \
            (options['db_password'], options['host'],
             options['db_username'], options['db_name'], file_path)
        self.stdout.write("Creating DB backup...")
        os.system(backup_command)
