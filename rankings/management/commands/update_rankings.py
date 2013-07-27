from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from scrapers.ranking import player_rushing, pass_efficiency 

class Command(BaseCommand):

    args = '<season>'
    help = 'Optionally provide a season. If no season is specified, command will use CURRENT_SEASON.'

    def handle(self, *args, **options):
        season = settings.CURRENT_SEASON
        try:
            season = args[0]
        except:
            pass

        self.stdout.write('Running update for rankings for season %s\n' % (season))
        player_rushing(season)

