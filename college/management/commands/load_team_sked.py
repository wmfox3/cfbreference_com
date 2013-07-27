import re
import csv
import urllib
import datetime
from time import strptime, strftime
import time

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.encoding import smart_unicode, force_unicode
from django.template.defaultfilters import slugify

from BeautifulSoup import BeautifulSoup

from college.models import College, Game, CollegeYear, Player, Position
from scrapers.teams import load_skeds
from utils import create_weeks, update_conf_games

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--season',
            action='store',
            dest='season',
            default=settings.CURRENT_SEASON,
            help='Pass specific season. Defaults to CURRENT_SEASON in settings.'),
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help='Retrieve all teams.'),
    )
    
    args = '<team_id team_id...>'
    help = 'Build the schedule for team ids specified by the passed argument. If no teams are passed, we will use all teams flagged updated=True. We will use the default season in settings.'

    def handle(self, *args, **options):

        if args:
            teams = College.objects.filter(id__in=(args))
        elif options['all']:
            teams = College.objects.filter(id__lt=100000).order_by('id')
        else: 
            #teams = CollegeYear.objects.filter(season=season, college__updated=True).order_by('id')
            teams = College.objects.filter(updated=True).exclude(id__gt=100000).order_by('id')

        print "Seeking %s season schedule data for %s colleges - %s." % (options['season'], len(teams), teams)
        load_skeds(options['season'], teams)

        print "Creating week objects."
        create_weeks(options['season'])

        print "Flagging conference match-ups."
        update_conf_games(options['season'])