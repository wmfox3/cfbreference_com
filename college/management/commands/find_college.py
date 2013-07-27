import urllib
from optparse import make_option

from BeautifulSoup import BeautifulSoup

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from utils import _check_college

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='retrieve_all',
            default=False,
            help='Retrieve all schools.'),
        make_option('--season',
            action='store',
            dest='season',
            default=settings.CURRENT_SEASON,
            help='Pass specific season. Defaults to CURRENT_SEASON in settings.'),
        make_option('--test',
            action='store_false',
            dest='run',
            default=True,
            help='Retrieve without saving.'),
    )
    args = '<name>'
    help = 'Provide a school name, partial name or several names and we will create College and CollegeYear objects from the NCAA. Defaults to season in CURRENT_SEASON, but you can pass a season using the --season option. Make sure to put quote marks around names with spaces. Using the option --all will pull every school for the requested season. Using the option --test will pull the data without writing anything to the local database.'

    def handle(self, *args, **options):

        url = "http://web1.ncaa.org/mfb/%s/Internet/schedule/FBS_teams.html" % options['season']
        html = urllib.urlopen(url).read()
        soup = BeautifulSoup(html)
        print "retrieving %s" % url

        if options['retrieve_all']:
            elems = soup.findAll("li")
            for school in elems:
                print "%s %s %s" % (school.find('a').contents[0], school.find('a')['href'].split('#')[1], options['season'])
                if options['run']:
                    _check_college(school.find('a').contents[0], school.find('a')['href'].split('#')[1], options['season'])
        else:
            for arg in args:
                elems = [elem for elem in soup.findAll('li') if arg in str(elem.text)]
                for school in elems:
                    print "%s %s %s" % (school.find('a').contents[0], school.find('a')['href'].split('#')[1], options['season'])
                    if options['run']:
                        _check_college(school.find('a').contents[0], school.find('a')['href'].split('#')[1], options['season'])
