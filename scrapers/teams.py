import re
import csv
import urllib
import datetime
import time
from time import strptime, strftime

from django.utils.encoding import smart_unicode, force_unicode
from django.template.defaultfilters import slugify

from BeautifulSoup import BeautifulSoup

from college.models import College, Game, CollegeYear, Player, Position, State, Conference, DIVISION_CHOICES
from utils import _parse_skedtable_row, _parse_roster_row, _retrieve_remote_content

def load_skeds(year, teams=None):
    """
    Loads the game schedules for teams for a given year. Defaults to all teams where updated = True,
    but can be passed in a selection of teams.
    >>> teams = College.objects.filter(id__in=(123,345,435))
    >>> load_skeds(2009, teams)
    """
    
    if not teams:
        teams = College.objects.filter(updated=True).exclude(id__lt=100000).order_by('id')

    div_dict = dict(map(reversed, DIVISION_CHOICES))
    division = ''
    conference = ''
    
    for team in teams:
        print "Working on team %s" % team.id
        url = "http://web1.ncaa.org/football/exec/rankingSummary?year=%s&org=%s" % (year, team.id)
        print "Reading from %s" % url

        #html = urllib.urlopen(url).read()
        html = _retrieve_remote_content(url)
        soup = BeautifulSoup(html)

        # make an effort to find the team's conference and division information elsewhere on the page
        try:
            t = soup.find('table', id="teamRankings")
            rows = t.findAll('tr')[1:3]
            td = re.match( r'(.*) teams ranked in (.*)', rows[0].find('th').contents[0]).group(2).replace('the ','')
            tc = re.match( r'(.*) teams ranked in (.*)', rows[1].find('th').contents[0]).group(2).replace('the ','')
            division = div_dict[td]
        except:
            pass

        conference, created = Conference.objects.get_or_create(name=tc, defaults={'abbrev':''})
        team1, created = CollegeYear.objects.get_or_create(college=team, season=year, defaults={'conference':conference, 'division':division})
        if not created:
            team1.conference = conference
            team1.division = division
            team1.save()

        #t = soup.findAll('table')[2]
        t = soup.find('table', id="schedule")
        rows = t.findAll('tr')[2:] # starting at the third row
        
        for row in rows:
            game = _parse_skedtable_row(row, team1, year)
    
            
def load_rosters(year, teams=None):
    """
    Loader for NCAA roster information. Loops through all teams in the database and finds rosters for the given year, then populates Player table with
    information for each player for that year. Also adds aggregate class totals for team in CollegeYear model.
    """
    if not teams:
        teams = College.objects.filter(updated=True).order_by('id')
    for college in teams:
        load_team(college, year)

def load_rosters_for_teams(teams):
    for t in teams:
        load_team(t.college, t.season)

def load_team(college, year):
    """
    Loads information about a single team during a single year. Includes total number of players by class,
    and also gets/creates individual Player objects and updates with the number of games played.
    >>> college = College.objects.get(slug='florida')
    >>> load_team(college, 2009)
    """
    url = "http://web1.ncaa.org/football/exec/roster?year=%s&org=%s" % (year, college.id)
    print "retrieving %s" % url
    #html = urllib.urlopen(url).read()
    html = _retrieve_remote_content(url)
    soup = BeautifulSoup(html)
    
    t = soup.find('table', id="roster")

    try:
        classes = t.find("th").contents[0].split(":")[1].split(',') # retrieve class numbers for team
        fr, so, jr, sr = [int(c.strip()[0:2]) for c in classes] # assign class numbers
        print "%s freshman, %s sophomores, %s juniors, %s seniors" % (fr,so,jr,sr)

        team, created = CollegeYear.objects.get_or_create(college=college, season=year)

        team.freshmen = fr
        team.sophomores = so
        team.juniors = jr
        team.seniors = sr
        team.save()

        rows = soup.findAll("tr")[5:]
        for row in rows:
            player = _parse_roster_row(row, team, year)

    except:
        print "No roster for %s in %s" % (college.name, year)
        pass
