from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

import urllib
import re
import time
from BeautifulSoup import BeautifulSoup
from college.models import *
from django.template.defaultfilters import slugify

from scrapers.models import NCAAGame
from scrapers.games import game_updater
from utils import update_college_year, populate_head_coaches, update_drive_outcomes, update_college_year

class Command(BaseCommand):
    args = '<week>'

    option_list = BaseCommand.option_list + (
        make_option('--season',
            action='store',
            dest='season',
            default=settings.CURRENT_SEASON,
            help='Pass specific season. Defaults to CURRENT_SEASON in settings.'),
        make_option('--nostats',
            action='store_true',
            dest='nostats',
            default=False,
            help='Run update with no-stats=True flag in order to not collect statistical information.'),
    )

    help = 'Update game outcomes for all teams flagged updated=True using the passed week argument. To pull a full season pass the week argument of 19. See help for --season and --nostats options.'

    def handle(self, *args, **options):

        teams = CollegeYear.objects.filter(season=options['season'], college__updated=True).order_by('college__name')
        week = args[0]

        self.stdout.write('Running update for season %s, week %s for %s nostats=%s\n' % (options['season'], week, teams, options['nostats']))
        
        game_updater(options['season'], teams, week, nostats=options['nostats'])
        
        self.stdout.write('Finished update for season %s, week %s for %s nostats=%s\n' % (options['season'], week, teams, options['nostats']))
