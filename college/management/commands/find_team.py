from django.core.management.base import BaseCommand, CommandError
from college.models import *

class Command(BaseCommand):
    args = '<team_id team_id ...>'
    help = 'Looks up teams by id from the local database. SHOULD BE EXTENDED TO PULL NCAA DATA IF NOT FOUND LOCALLY.'

    def handle(self, *args, **options):
        for team_id in args:
            try:
                team = College.objects.get(pk=int(team_id))

                self.stdout.write('Name: "%s"\n' % team)
                self.stdout.write('Slug: "%s"\n' % team.slug)
                self.stdout.write('DriveSlug: "%s"\n' % team.drive_slug)
                self.stdout.write('State: "%s"\n' % team.state)
          
            except College.DoesNotExist:
                raise CommandError('College "%s" does not exist. Should look up NCAA data.' % team_id)

