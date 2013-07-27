from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from college.models import *
from scrapers.ranking import load_rankings_for_teams

class Command(BaseCommand):
    args = '<week>'

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

    help = 'Load rankings for all teams flagged updated=True using the passed week argument. We will use the default season in settings unless otherwise set.'

    def handle(self, *args, **options):
        if args:
            week = args[0]
        else:
            week = 19

        # if week has a hyphen, then it's a range of weeks


        if options['division']:
            teams = CollegeYear.objects.filter(division=options['division'], season=options['season'])
        else:
            teams = CollegeYear.objects.filter(season=options['season'], college__updated=True).order_by('id')

        self.stdout.write('Running load_rankings_for_teams() to get team-level rankings for season %s, week %s for %s teams: %s\n' % (options['season'], week, len(teams), teams))
        load_rankings_for_teams(teams, week)
