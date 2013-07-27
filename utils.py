import re
import csv
import urllib
import datetime
from time import strptime, strftime
import time

from urlparse import urljoin
from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_unicode, force_unicode
from django.db.models import Avg, Sum, Min, Max, Count
from django.db.models import F, Q
from django.db import IntegrityError

from college.models import *
from rankings.models import *

"""
The functions here are a collection of utilities that help with data loading 
or otherwise populate records that are not part of the scraping process.
"""

def _retrieve_remote_content(url):
    """
    Take the url and return the content of the page after first checking the cache.
    """
    myObject = cache.get(url)
    if (myObject == None):
        myObject = urllib.urlopen(url).read()
        print "retrieving remote file and caching"
        cache.set(url, myObject, settings.URL_CACHE_TIME*60) # Will cache the object for 1440*60 seconds or 1 day.
    else:
        print "pulling file from cache"
    return myObject

def _check_college(name, id, season):
    """
    Take a name string id number and season and return the collegeyear object, creating one if necessary
    """
    name = "%s" % name
    id = int(id)
    season = int(season)
    slug = slugify(name)

    c, created = College.objects.get_or_create(id=id, defaults={'name':name, 'slug':slug, 'drive_slug':slug, 'updated':False})
    cy, created = CollegeYear.objects.get_or_create(college=c, season=season)

    return cy
    #try:
    #    c = College.objects.get(id=number, name=collegename, slug=collegeslug, drive_slug=collegeslug)
    #except College.DoesNotExist:
    #    c = College.objects.create(id=number, name=collegename, slug=collegeslug, drive_slug=collegeslug, updated=False)
    
def _check_college_year(season, id=None, name=None, drive_slug=None):
    """
    This will be a workhorse of a function. The function assumes we are working with at minimum a season. 
    Option 1: Only have ID. Look up an existing college and grab or create the collegeyear (team).
    Option 2: ID and name. Look up or create college and grab or create the collegeyear.
    Option 3: ID and drive_slug. Look up college and grab or create the collegeyear.
    Option 4: No ID but just a name. Look up or create college and grab or create the college year, using dummyid if necessary.  
    
    Return the collegeyear object after creating one if necessary.
    """
    season = int(season)
    if name:
        name = "%s" % name
    created = False

    if id: # if provided an id, then by all means use it.
        if name:
            c, created = College.objects.get_or_create(id=int(id), defaults={'name':name, 'slug':slugify(name), 'drive_slug':slugify(name), 'updated':False})
        elif drive_slug:
            c = College.objects.get(drive_slug=drive_slug)
        else:
            c = College.objects.get(id=int(id))
    elif name: # without an id, first check whether a college exists by that name
        try:
            c = College.objects.get(slug=slugify(name))
        except College.DoesNotExist:
            c, created = College.objects.get_or_create(id=_get_dummy_id(), defaults={'name':name, 'slug':slugify(name), 'drive_slug':slugify(name), 'updated':False})

        if re.findall("[a-z]", name): # sometimes colleges get created with uppercase names. this will fix some of those when we get a lowercase version later
            c.name = name
            c.save()
    elif drive_slug:    
        try:
            c = College.objects.get(drive_slug=drive_slug)
        except College.DoesNotExist:
            return False
    if c:
        cy, created = CollegeYear.objects.get_or_create(college=c, season=season)
    else:
        return False

    return cy

def _get_dummy_id():
    di = NextDummyId.objects.get(pk=1)
    print di.next_id

    di.next_id = di.next_id + 1
    di.save()
    return di.next_id

def _clean_name(name):
    return name.replace('@','').replace('*','').replace('^','').strip()
    
def _extract_date(stringdate):
    return datetime.date(*(time.strptime(stringdate, '%m/%d/%Y')[0:3]))

def _extract_plays(soup, game):
    drive_table = soup.find(text='Drive #').findParents('table')[0]
    drive_rows = drive_table.findAll('tr')[2:]
    drives = [t for t in drive_rows if t.findAll('a')]

    for r in drives:
        plays = r.findNext('tr').findAll('li')
        for row in plays:
            down_and_distance = re.search('\A\(.{8,11}\)', row.text).group(0)
            down = int(down_and_distance[1])
            distance = int(re.search('and (\d{1,2})', down_and_distance).group(1))
            description = re.search('\(\d\w{2} and \d{1,2}\) (.*)', row.text).group(1)
            drive_cells = row.parent.parent.parent.findPreviousSibling().findAll('td')
            drive_slug = slugify(drive_cells[2].contents[0])
            team = _check_college_year(season=game.season, drive_slug=drive_slug)

            drive_number = int(drive_cells[0].find("a").contents[0])
            try:
                drive = GameDrive.objects.get(drive=drive_number, team=team, game=game)

                quarter = int(drive_cells[1].contents[0])
                play, created = GamePlay.objects.get_or_create(
                    game=game, 
                    offensive_team=team, 
                    drive=drive,
                    quarter=quarter,
                    description=description,
                    down=down,
                    distance=distance
                )
            except GameDrive.DoesNotExist:
                print "Skipping drive because it doesn't already exist in db"
                pass

    return True

def _extract_drives(soup, game):

    drive_table = soup.find(text='Drive #').findParents('table')[0]
    drive_rows = drive_table.findAll('tr')[2:]
    #print drive_rows[0]
    
    drives = [t for t in drive_rows if t.findAll('a')]

    for r in drives:
        start_side = "O"
        start_position = None
        end_side = "O"
        end_position = None

        try:
            drive_number = r.find('a').string

            #http://web1.ncaa.org/mfb/driveSummary.jsp?acadyr=%s&h=%s&v=%s&date=%s&game=%s
            reg_link = re.search( r'driveSummary\.jsp\?expand=(\d*)&acadyr=(\d{4})&h=(\d*)&v=(\d*)&date=(.*)&game=(\d*)', r.find('a')['href'] )
            season_year = reg_link.group(2)
            home_id = reg_link.group(3)
            visitor_id = reg_link.group(4)
            game_date = time.strptime(reg_link.group(5), '%d-%b-%y')
            game_id = reg_link.group(6)

            drive_details = r.findAll('td')
            drive_quarter = drive_details[1].string

            # drive team
            drive_team = drive_details[2].string
            drive_slug = slugify(drive_team)
            team = _check_college_year(season=game.season, drive_slug=drive_slug)
            
            start_on = drive_details[5].string
            start_possession = drive_details[3].string
            start_clock = datetime.time(0, int(drive_details[4].string.split(":")[0]), int(drive_details[4].string.split(":")[1][:2]))
            #start_clock = time.strptime(drive_details[4].string, "%M:%S")

            end_on = drive_details[8].string
            end_possession = drive_details[6].string
            if drive_quarter == '4' and end_possession == 'HALF': # fix for ncaa using HALF when game ends
                end_possession = 'GAME OVER'

            end_clock = datetime.time(0, int(drive_details[7].string.split(":")[0]), int(drive_details[7].string.split(":")[1][:2]))
            #end_clock = time.strptime(drive_details[7].string, "%M:%S")
            
            end_result_instance, end_result_created = DriveOutcome.objects.get_or_create(abbrev=end_possession)

            drive_number_plays = drive_details[9].string
            drive_yards = drive_details[10].string
            drive_time_possession = datetime.time(0, int(drive_details[11].string.split(":")[0]), int(drive_details[11].string.split(":")[1][:2]))
            #drive_time_possession = time.strptime(drive_details[11].string, "%M:%S")

            if start_on:
                starting = re.search(r'(\D*)([0-9]+)', start_on)
                if starting.group(1) == "opp ":
                    start_side = "P" 
                start_position = int(starting.group(2))

            if end_on:
                try:
                    ending = re.search(r'(\D*)([0-9]+)', end_on)
                    if ending.group(1) == "opp ":
                        end_side = "P"
                    end_position = int(ending.group(2))
                except:
                    pass

            #print "%s - %s" % (start_on, start_position)
            #print "%s - %s" % (end_on, end_position)

            '''
            print "game: %s" % game
            print "drive_number: %s" % drive_number
            print "team: %s" % team
            print "game.season: %s" % game.season
            print "drive_quarter: %s" % drive_quarter
            print "start_possession: %s" % start_possession
            print "start_clock: %s" % start_clock
            print "start_on: %s" % start_on
            print "start_side: %s" % start_side
            print "end_possession: %s" % end_possession
            print "end_clock: %s" % end_clock
            print "end_on: %s" % end_on
            print "end_side: %s" % end_side
            print "drive_number_plays: %s" % drive_number_plays
            print "drive_yards: %s" % drive_yards
            print "drive_time_possession: %s" % drive_time_possession
            '''

            game_drive, created = GameDrive.objects.get_or_create(
                game=game, 
                end_result=end_result_instance,
                drive=drive_number, 
                team=team,
                season=game.season,
                defaults={
                    'quarter':drive_quarter,
                    'start_how':str(start_possession), 
                    'start_time':start_clock, 
                    'start_position':start_position, 
                    'start_side':start_side, 
                    'end_time':end_clock, 
                    'end_position':end_position, 
                    'end_side':end_side, 
                    'plays':drive_number_plays, 
                    'yards':drive_yards,
                    'time_of_possession':drive_time_possession
                } 
            )
        except IndexError:
            print "IndexError exception at drive number %s for game %s" % (drive_number, game)
            pass

    return True

def _parse_skedtable_row(row, team1, year):
    """
    Take the passed string scraped from a table row and return a game object after creating any necessary College and CollegeYear objects
    Doing this in one place should make it easier to handle changes by the ncaa
    """

    try: # take a crack at finding the url to the game xml
        xml_link = re.search( r'.*game=(\d*).*', row.findAll('td')[0].find('a')['href'] )
        gamexml = xml_link.group(1)
    except:
        gamexml = ''
     
    gamedate = _extract_date(row.findAll('td')[0].text.split(' ')[1])    

    try: # determine whether the opponent name is clickable
        t2_td = row.findAll('td')[1].find('a').contents[0]
        t2_id = int(row.findAll('td')[1].find('a')['href'].split('=')[1].split('&')[0])
    except AttributeError:
        t2_td = row.findAll('td')[1].contents[0]
        t2_id = None

    t2_clean_name = _clean_name(t2_td)
    team2 = _check_college_year(year, id=t2_id, name=t2_clean_name)

    # determine the game label type
    if "@" in t2_td:
        t1_game_type = 'A'
    else:
        t1_game_type = 'H'
    if "^" in t2_td:
        t1_game_type = 'N'
    
    # attempt to sort out the final score, ot status and team1_result if available
    #try:
        #team1_score, team2_score = [int(x) for x in row.findAll('td')[2].split(' - ')]
        #if len(game_results[3].contents[0].strip().split(' ')) == 2:
        #    t1_result, ot = row.findAll('td')[3].contents[0].strip().split(' ')
        #else:
        #   t1_result = row.findAll('td')[3].contents[0].strip()
        #    ot = None
    if len(row.findAll('td')[3].string) > 1:
        #print ".%s." % row.findAll('td')[2].contents[0]
        team1_score, team2_score =  row.findAll('td')[2].contents[0].split(' - ')
        #score_string  = re.search( r'(\d+)(\D+)(\d+)', row.findAll('td')[2].contents[0] )
        #team1_score = score_string.group(1)
        #team2_score = score_string.group(2)
        team1_result_string = re.search( r'([WL]{1})\s*([234OT]*)', row.findAll('td')[3].contents[0] )
        t1_result = team1_result_string.group(1)
        ot = team1_result_string.group(2)
    else:
        team1_score = None
        team2_score = None
        t1_result = None
        ot = None

    #team1_score, team2_score = [int(x) for x in row.findAll('td')[2].contents[0].split(' - ')]
    #if len(row[3].contents[0].strip().split(' ')) == 2:
    #    t1_result, ot = row.findAll('td')[3].contents[0].strip().split(' ')
    #else:
    #    t1_result = row.findAll('td')[3].contents[0].strip()
    #    ot = None

    # all that college and collegeyear crap out of the way
    # let's create the game objects
    print "yr:%s t1:%s t2:%s d:%s - xml:%s t1s:%s t2s:%s t1r:%s t1gt:%s ot:%s" % (year,team1.id,team2.id,gamedate,gamexml,team1_score,team2_score,t1_result,t1_game_type,ot)
    g, new_game = Game.objects.get_or_create(
        season=year, 
        team1=team1, 
        team2=team2, 
        date=gamedate
    )
    g.ncaa_xml = gamexml
    g.team1_score = team1_score
    g.team2_score = team2_score
    g.t1_result = t1_result
    g.t1_game_type = t1_game_type
    g.overtime = ot
    g.save()

    #print "created? %s: %s %s (%s-%s %s) vs %s %s on %s" % (new_game, g.team1.college.name, team1_score, t1_result, ot, t1_game_type, g.team2.college.name, team2_score, g.date)    
    return g

def _parse_roster_row(row, team, year):
    cells = row.findAll("td")
    unif = cells[0].contents[0].strip()
    name = cells[1].a.contents[0].strip()
    if cells[2].contents[0].strip() == '-':
        pos = Position.objects.get(id=11)
    else:
        pos, created = Position.objects.get_or_create(abbrev=cells[2].contents[0].strip())
    cl = cells[3].contents[0].strip()
    gp = int(cells[4].contents[0].strip())
    print "%s (%s) %s, %s, %s, %s" % (name, slugify(name), team, year, pos, cl)
    py, created = Player.objects.get_or_create(name=name, slug=slugify(name), team=team, season=year, position=pos, status=cl)
    py.number=unif
    py.games_played=gp
    py.save()

def create_missing_collegeyears(year):
    """
    Create collegeyears where they are missing (legacy data only).
    >>> create_missing_collegeyears(2009)
    """
    games = Game.objects.filter(season=year)
    for game in games:
        try:
            game.team1
        except CollegeYear.DoesNotExist:
            try:
                c = College.objects.get(pk=game.team1_id)
                cy, created = CollegeYear.objects.get_or_create(college=c, season=year)
                if created:
                    print "created CollegeYear for %s in %s" % (c, year)
            except:
                print "Could not find a college for %s" % game.team1_id

def opposing_coaches(coach):
    coach_list = Coach.objects.raw("SELECT college_coach.id, college_coach.slug, count(college_game.*) as games from college_coach inner join college_game on college_coach.id = college_game.coach2_id where coach1_id = %s group by 1,2 order by 3 desc", [coach.id])
    return coach_list

def calculate_team_year(year, month):
    if int(month) < 8:
        team_year = int(year)-1
    else:
        team_year = int(year)
    return team_year

def calculate_record(totals):
    """
    Given a dictionary of game results, calculates the W-L-T record from those games.
    Used to calculate records for team vs opponent and coach vs coach views.
    """
    d = {}
    for i in range(len(totals)):
        d[totals[i]['t1_result']] = totals[i]['count']
    try:
        wins = d['W']
    except KeyError:
        wins = 0
    try:
        losses = d['L'] or None
    except KeyError:
        losses = 0
    try:
        ties = d['T']
    except KeyError:
        ties = 0
    return wins, losses, ties

def last_home_loss_road_win(games):
    """
    Given a list of games, returns the most recent home loss and road win.
    """    
    try:
        last_home_loss = games.filter(t1_game_type='H', t1_result='L')[0]
    except:
        last_home_loss = None
    try:
        last_road_win = games.filter(t1_game_type='A', t1_result='W')[0]
    except:
        last_road_win = None
    return last_home_loss, last_road_win
    
    
def set_head_coaches():
    """
    One-time utility to add a boolean value to college coach records. Used to prepare
    the populate_head_coaches function for games. 
    """
    CollegeCoach.objects.select_related().filter(jobs__name='Head Coach').update(is_head_coach=True)

def populate_head_coaches(game):
    """
    Given a game, tries to find and save the head coaches for that game. 
    If it cannot, it leaves the head coaching fields as 0. Can be run on
    an entire season or as part of the game loader. As college coach data
    grows, will need to be run periodically on games without head coaches:
    
    >>> games = Game.objects.filter(coach1__id=0, coach2__id=0)
    >>> for game in games:
    ...     populate_head_coaches(game)
    ...
    """
    try:
        hc = game.team1.collegecoach_set.filter(is_head_coach=True).order_by('-start_date')
        if hc.count() > 0:
            if hc.count() == 1:
                game.coach1 = hc[0].coach
            else:
                coach1, coach2 = [c for c in hc]
                if coach1.end_date:
                    if game.date < coach1.end_date:
                        game.coach1 = coach1.coach
                    elif game.date >= coach2.start_date:
                        game.coach1 = coach2.coach
                    else:
                        game.coach1_id = 0                
        else:
            game.coach1_id = 0
    except:
        game.coach1_id = 0
    game.save()
    
    try:
        hc2 = game.team2.collegecoach_set.filter(is_head_coach=True).order_by('-start_date')
        if hc2.count() > 0:
            if hc2.count() == 1:
                game.coach2 = hc2[0].coach
            else:
                coach1, coach2 = [c for c in hc2]
                if coach1.end_date:
                    if game.date < coach1.end_date:
                        game.coach2 = coach1.coach
                    elif game.date >= coach2.start_date:
                        game.coach2 = coach2.coach
                    else:
                        game.coach2_id = 0                
        else:
            game.coach2_id = 0
    except:
        game.coach2_id = 0
    game.save()

def next_coach_id():
    """
    Generates the next id for newly added coaches, since their slugs (which combine the id and name fields) 
    are added post-commit.
    """
    c = Coach.objects.aggregate(Max("id"))
    return c['id__max']+1

def update_conference_membership(year):
    # check prev year conference and update current year with it, then mark conf games.
    previous_year = year-1
    teams = CollegeYear.objects.filter(season=previous_year, conference__isnull=False)
    for team in teams:
        cy = CollegeYear.objects.get(season=year, college=team.college)
        cy.conference = team.conference
        cy.save()
    

def update_conf_games(year):
    """
    Marks a game as being a conference game if teams are both in the same conference.
    Does not affect conference record tabulations. Once the games in the season schedule are marked as conference, update_college_year will handle the season and conference records.
    """
    games = Game.objects.filter(season=year, team1__college__updated=True, team2__college__updated=True, team1__conference__isnull=False)

    for game in games:
        try:
            if game.team1.conference == game.team2.conference:
                game.is_conference_game = True
                game.save()
        except:
            pass

def update_drive_outcomes(collegeyear):
    """
    Updates GameDriveSeason records for a CollegeYear instance.
    """
    do = DriveOutcome.objects.select_related().filter(gamedrive__season=collegeyear.season, gamedrive__team=collegeyear)
    outcomes = do.annotate(Count('gamedrive')).order_by('-gamedrive__count')
    for outcome in outcomes:
        gds, created = GameDriveSeason.objects.get_or_create(season=collegeyear.season, team=collegeyear, outcome=outcome)
        gds.total = outcome.gamedrive__count
        gds.drives_total = do.count()
        gds.save()
    

def update_quarter_scores(game):
    """
    Utility to update quarter scores for existing games. New games handled via ncaa_loader.
    """
    url = game.get_ncaa_xml_url()
    html = _retrieve_remote_content(url)
    soup = BeautifulSoup(html)

    quarters = len(soup.findAll('score')[1:])/2
    t2_quarters = soup.findAll('score')[1:quarters+1] #visiting team
    t1_quarters = soup.findAll('score')[quarters+1:] #home team
    for i in range(quarters):
        vqs, created = QuarterScore.objects.get_or_create(game = game, team = game.team2, season=game.season, quarter = i+1, points = int(t2_quarters[i].contents[0]))
        hqs, created = QuarterScore.objects.get_or_create(game = game, team = game.team1, season=game.season, quarter = i+1, points = int(t1_quarters[i].contents[0]))
        
    

def update_college_year(year):
    """
    Updates season and conference records for teams. Run at the end of a game loader.
    """
    teams = CollegeYear.objects.select_related().filter(season=year, college__updated=True).order_by('college_college.id')
    for team in teams:
        games = Game.objects.filter(team1=team, season=year, t1_result__isnull=False).values("t1_result").annotate(count=Count("id")).order_by('t1_result')
        d = {}
        for i in range(games.count()):
            d[games[i]['t1_result']] = games[i]['count']
        try:
            wins = d['W']
        except KeyError:
            wins = 0
        try:
            losses = d['L']
        except KeyError:
            losses = 0
        try:
            ties = d['T']
        except KeyError:
            ties = 0
        if team.conference:
            conf_games = Game.objects.select_related().filter(team1=team, season=year, is_conference_game=True, t1_result__isnull=False).values("t1_result").annotate(count=Count("id")).order_by('t1_result')
            if conf_games:
                c = {}
                for i in range(conf_games.count()):
                    c[conf_games[i]['t1_result']] = conf_games[i]['count']
                try:
                    conf_wins = c['W']
                except KeyError:
                    conf_wins = 0
                try:
                    conf_losses = c['L']
                except KeyError:
                    conf_losses = 0
                try:
                    conf_ties = c['T']
                except KeyError:
                    conf_ties = 0
                team.conference_wins=conf_wins
                team.conference_losses=conf_losses
                team.conference_ties=conf_ties
        team.wins=wins
        team.losses=losses
        team.ties=ties
        team.save()

def add_college_years(year):
    """
    Creates college years for teams. Used at the beginning of a new season or to backfill.
    """
    teams = College.objects.filter(updated=True).order_by('id')
    for team in teams:
        cy, created = CollegeYear.objects.get_or_create(season=year, college=team)

def create_weeks(year):
    """
    Given a year with games in the db, creates weeks for that year.
    """
    
    min = Game.objects.filter(season=year).aggregate(Min('date'))['date__min']
    max = Game.objects.filter(season=year).aggregate(Max('date'))['date__max']
    date = min
    week = 1
    while date <= max:
        if date.weekday() < 5:
            dd = 5 - date.weekday()
            end_date = date + datetime.timedelta(days=dd)
        else:
            end_date = date
        new_week, created = Week.objects.get_or_create(season=min.year, week_num = week, end_date = end_date)
        date += datetime.timedelta(days=7)
        week += 1      

def game_weeks(year):
    """
    Populates week foreign key for games.
    """
    weeks = Week.objects.filter(season=year).order_by('week_num')
    for week in weeks:
        games = Game.objects.filter(season=year, date__lte=week.end_date, week__isnull=True)
        for game in games:
            game.week = week
            game.save()

def update_pre_2000_games(season):
    games = Game.objects.filter(season=season)
    for game in games:
        try:
            c1 = College.objects.get(id=game.team1_id)
            cy1, created = CollegeYear.objects.get_or_create(college=c1, season=season)
            c2 = College.objects.get(id=game.team2_id)
            cy2, created = CollegeYear.objects.get_or_create(college=c2, season=season)
            game.team1 = cy1
            game.team2 = cy2
            game.save()
        except:
            print game.id
            raise

def advance_coaching_staff(team, year):
    """
    Takes an existing coaching staff, minus any who have an end_date value,
    and creates new CollegeCoach records for them in the provided year.

    Usage:    
    >>> from utils import advance_coaching_staff
    >>> from college.models import *
    >>> team = College.objects.get(id = 8)
    >>> advance_coaching_staff(team, 2012)
    """
    previous_year = int(year)-1
    college = College.objects.get(id=team.id)
    old_cy = CollegeYear.objects.get(college=college, season=previous_year)
    new_cy = CollegeYear.objects.get(college=college, season=year)
    old_staff = CollegeCoach.objects.filter(collegeyear=old_cy, end_date__isnull=True)
    for coach in old_staff:
        cc, created = CollegeCoach.objects.get_or_create(collegeyear=new_cy, coach=coach.coach)
        for job in coach.jobs.all():
            cc.jobs.add(job)

def remove_bad_player_stat_instances(season):
    """
    Should the player game stat loader create objects that refer to the wrong game (the opponent's), this function
    will delete them from the db.
    """
    objs = [PlayerGame, PlayerRush, PlayerPass, PlayerReceiving, PlayerScoring, PlayerTackle, PlayerTacklesLoss, PlayerPassDefense, PlayerFumble, PlayerReturn]
    for obj in objs:
        obj.objects.filter(game__season=season).select_related(depth=1).exclude(game__team1=F('player__team')).delete()

def update_player_games_played(season):
    players = Player.objects.filter(season=season)
    for player in players:
        player.games_played = player.playergame_set.all().count()
        player.save()

def populate_drive_slugs(season='2012', division='2'):
    from django.db import connection, transaction
    cursor = connection.cursor()
    url = "http://web1.ncaa.org/mfb/%s/Internet/ranking_summary/DIVISION%s.HTML" % (season, division)
    #html = urllib.urlopen(url).read()
    html = _retrieve_remote_content(url)
    soup = BeautifulSoup(html)

    links = soup.findAll('a')[1:]
    for link in links:
        query = "UPDATE college_college set drive_slug = %s where id = %s"
        params = (str(link.contents[0]), int(link["href"].split('org=')[1]))
        cursor.execute(query, params)

def populate_divisions(season=2012, division='2'):
    divs = { "2": "D", "3": "T", "B": "B", "C":"C"} # note that these use the same translations as DIVISION_CHOICES in the college models.
    url = "http://web1.ncaa.org/mfb/%s/Internet/ranking_summary/DIVISION%s.HTML" % (str(season), division)
    #html = urllib.urlopen(url).read()
    html = _retrieve_remote_content(url)
    soup = BeautifulSoup(html)

    links = soup.findAll('a')[1:]
    for link in links:
        college_id = int(link["href"].split('org=')[1])
        college_name = link.string
        div_value = divs[division]

        print "%s, %s - %s" % (college_name, college_id, div_value) 

        #print link.contents[0]
        #state = State.objects.all()[0]
        
        cy = _check_college_year(season=season, id=college_id, name=college_name)
        cy.division = div_value
        cy.save()

        #try:
        #    college = College.objects.get(id=college_id)
        #    cy, created = CollegeYear.objects.get_or_create(college__id=college.id , season = season)
        #    cy.division = div_value
        #    cy.save()
        #except:
        #    print "can't find college for %s" % str(college_id)
        #    pass


