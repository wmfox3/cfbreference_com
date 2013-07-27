import urllib
import re
import time

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from utils import populate_divisions

class Command(BaseCommand):
    args = '<season>'

    option_list = BaseCommand.option_list + (
        make_option('--divisions',
            action='store_true',
            dest='populate_divisions',
            default=False,
            help='Populate divisions.'),
    )

    help = 'Routine maintenance tasks.'

    def handle(self, *args, **options):

        season = settings.CURRENT_SEASON
        if args:
            season = args[0]

        if options['populate_divisions']:
            #from college.models import DIVISION_CHOICES
            divs = { "2": "D", "3": "T", "B": "B", "C":"C"}
            #t = tuple(x[0] for x in DIVISION_CHOICES)
            #for d in t:
            #    print d

            for k, v in divs.iteritems():
                self.stdout.write('Populating divisions for div %s, season %s\n' % (k,season))
                populate_divisions(season=season, division=k)

