import urllib
import datetime
import time
import re

from BeautifulSoup import BeautifulSoup

from django.template.defaultfilters import slugify

from rankings.models import Ranking, RushingSummary, PassEfficiency, RankingType
from college.models import College, CollegeYear, Week, Player, Position
from utils import _retrieve_remote_content

def load_rankings_for_teams(teams, week):
    for t in teams:
        get_team_ranking(t.college, t.season, week)

def ranking_loader(season, week):
    teams = College.objects.filter(updated=True).order_by('id')
    for team in teams:
        get_team_ranking(team, season, week)

def get_team_ranking(team, season, week):
    cy = CollegeYear.objects.get(college=team, season=season)
    w = Week.objects.get(season=season, week_num=week)
    url = cy.get_ncaa_week_url()+str(week)
    #print "retrieving %s" % url
    print "retrieving team rankings for %s in week %s" % (cy,w)

    #html = urllib.urlopen(cy.get_ncaa_week_url()+str(week)).read()
    html = _retrieve_remote_content(url)
    soup = BeautifulSoup(html)

    try:
        #rankings = soup.findAll('table')[4]
        rankings = soup.find('table', id="teamRankings")
    except:
        rankings = None
    
    if rankings:
        rows = rankings.findAll('tr')[5:22]
        for row in rows:
            cells = row.findAll('td')
            #print str(cells[0].find("a").contents[0])
            rt = RankingType.objects.get(name=str(cells[0].find("a").contents[0]))
            try:
                rk =int(cells[1].contents[0])
                i_t = False
            except ValueError:
                rk = int(cells[1].contents[0].split('T-')[1])
                i_t = True
    
            try:
                cr = int(cells[5].contents[0])
                ic_t = False
            except ValueError:
                cr = int(cells[5].contents[0].split('T-')[1])
                ic_t = True
    
            r, created = Ranking.objects.get_or_create(ranking_type=rt, collegeyear=cy, season=season, week=w, rank=rk, is_tied = i_t, actual=float(cells[2].contents[0]), conference_rank=cr, is_conf_tied=ic_t, division = cy.division)

def player_rushing(season):
    url = "http://web1.ncaa.org/mfb/natlRank.jsp?year=%s&div=B&rpt=IA_playerrush&site=org" % season
    html = urllib.urlopen(url).read()
    print "retrieving %s" % url

    soup = BeautifulSoup(html)

    # find thru date for presented rankings
    td = soup.findAll('td', text = re.compile('Thru'))
    date_string = re.match( r'Thru: (.*) Minimum Pct. of Games Played (\d+)', td[0]).group(1)
    d = time.strptime(date_string, "%m/%d/%y")

    #d = datetime.date.today()
    if season == d.tm_year:
        w = Week.objects.filter(end_date__lte=d, season=season).order_by('-week_num')[0]
    else:
        w = Week.objects.filter(season=season).order_by('-week_num')[0]

    rankings = soup.find('table', {'class': 'statstable'})
    rows = rankings.findAll('tr')[1:]

    for row in rows:
        rank = int(row.findAll('td')[0].contents[0])
        name = row.findAll('td')[1].find('a').contents[0]
        year = int(row.findAll('td')[1].find('a')['href'].split('=')[1][:4])
        team_id = int(row.findAll('td')[1].find('a')['href'].split('=')[2].split('&')[0])
        p_num = str(row.findAll('td')[1].find('a')['href'].split('=')[3])
        pos = Position.objects.get(abbrev=str(row.findAll('td')[2].contents[0]))
        carries = int(row.findAll('td')[5].contents[0])
        net = int(row.findAll('td')[6].contents[0])
        td = int(row.findAll('td')[7].contents[0])
        avg = float(row.findAll('td')[8].contents[0])
        ypg = float(row.findAll('td')[9].contents[0])


        team = CollegeYear.objects.get(college__id=team_id, season=season)

        print "Seeking player team %s, number %s, season %s, position %s" % (team, p_num, season, pos)
        player, created = Player.objects.get_or_create(
            name = name,
            slug = slugify(name),
            team = team, 
            season = season, 
            position = pos,
            number = p_num, 
        )

        print "player %s, team %s, rank %s, yr %s, pos %s, carries %s, net %s, td %s, avg %s, ypg %s" % (player, team, rank, year, pos, carries, net, td, avg, ypg)
        prs, created = RushingSummary.objects.get_or_create(
            player=player,
            season=season, 
            week=w, 
            rank=rank, 
            carries=carries, 
            net=net, 
            td=td, 
            average=avg, 
            yards_per_game=ypg
        )

def pass_efficiency(season):
    url = "http://web1.ncaa.org/mfb/natlRank.jsp?year=%s&div=B&rpt=IA_playerpasseff&site=org" % season
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html)
    rankings = soup.find('table', {'class': 'statstable'})
    rows = rankings.findAll('tr')[1:]
    d = datetime.date.today()
    if season == d.year:
        w = Week.objects.filter(end_date__lte=d, season=season).order_by('-week_num')[0]
    else:
        w = Week.objects.filter(season=season).order_by('-week_num')[0]
    for row in rows:
        rank = int(row.findAll('td')[0].contents[0])
        team_id = int(row.findAll('td')[1].find('a')['href'].split('=')[2].split('&')[0])
        p_num = str(row.findAll('td')[1].find('a')['href'].split('=')[3])
        pos = Position.objects.get(abbrev=str(row.findAll('td')[2].contents[0]))
        team = CollegeYear.objects.get(college__id=team_id, season=season)
        att = int(row.findAll('td')[5].contents[0])
        comp = int(row.findAll('td')[6].contents[0])
        comp_pct = float(row.findAll('td')[7].contents[0])
        intercept = int(row.findAll('td')[8].contents[0])
        int_pct = float(row.findAll('td')[9].contents[0])
        yards = int(row.findAll('td')[10].contents[0])
        yds_per_att = float(row.findAll('td')[11].contents[0])
        tds = int(row.findAll('td')[12].contents[0])
        td_pct = float(row.findAll('td')[13].contents[0])
        rating = float(row.findAll('td')[14].contents[0])
        player = Player.objects.get(team=team, number=p_num, season=season, position=pos)
        pass_eff, created = PassEfficiency.objects.get_or_create(player=player, season=season, week=w, rank=rank, attempts=att,completions=comp, completion_pct=comp_pct, interceptions=intercept, attempts_per_interception=int_pct, yards=yards, yards_per_attempt=yds_per_att, touchdowns=tds, attempts_per_touchdown=td_pct, rating=rating)
