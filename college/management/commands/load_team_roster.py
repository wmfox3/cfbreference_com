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
from scrapers.teams import load_rosters, load_rosters_for_teams

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--season',
            action='store',
            dest='season',
            default=settings.CURRENT_SEASON,
            help='Pass specific season. Defaults to CURRENT_SEASON in settings.'),
        make_option('--division',
            action='store',
            dest='division',
            default=None,
            help='Passed a division and we will grab rosters for every team in that division. Bowl Subdivison = B, Championship Subdivision = C, Div II = D, Div III = T'),
    )
    

    args = '<team_id team_id...>'
    help = 'Build the roster for teams specified by the passed argument. If no teams are passed, we will use all teams flagged updated=True. We will use the default season in settings. Use the --division option to build rosters for all teams in the division.'

    def handle(self, *args, **options):

        '''
        The correct way to do this is to pass a list of collegeyear objects, teams, rather than colleges/schools.
        '''

        if args:
            teams = CollegeYear.objects.filter(college__id__in=(args), season=options['season'])
        else: 
            if options['division']:
                teams = CollegeYear.objects.filter(division=options['division'], season=options['season'])
            else:
                teams = CollegeYear.objects.filter(season=options['season'], college__updated=True).order_by('id')

        print "Seeking %s season roster data for %s\n\n" % (options['season'], teams)
        load_rosters_for_teams(teams)
        
