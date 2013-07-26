from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Avg, Sum, Min, Max, Count
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.syndication.views import Feed
from django import forms
from django.utils import simplejson
from django.forms.models import modelformset_factory
from operator import itemgetter
from time import strptime
import datetime
from college.models import *
from rankings.models import *

if datetime.date.today().month < 8:
    CURRENT_SEASON = datetime.date.today().year-1
else:
    CURRENT_SEASON = datetime.date.today().year

def rankings_index(request):
    ranking_list = RankingType.objects.filter(typename='T').order_by('name')
    return render_to_response('rankings/rankings_index.html', {'ranking_list':ranking_list})

def rankings_season(request, rankingtype, season, div='B', week=None):
    rt = get_object_or_404(RankingType, slug=rankingtype)
    date = datetime.date.today()-datetime.timedelta(days=7)
    if week:
        latest_week = Week.objects.get(season=season, week_num=week)
    else:
        try:
            latest_week = Week.objects.filter(season=season, end_date__gte=date, end_date__lte=datetime.date.today()).order_by('end_date')[0]
        except:
            latest_week = Week.objects.filter(season=season).order_by('-end_date')[0]
    other_weeks = Week.objects.filter(season=season).exclude(week_num=latest_week.week_num).exclude(end_date__gte=datetime.date.today()).order_by('end_date')
    rankings_list = Ranking.objects.filter(season=season, ranking_type=rt, week=latest_week, division=div).select_related().order_by('rank')
    return render_to_response('rankings/rankings_season.html', {'ranking_type': rt, 'rankings_list': rankings_list, 'season':season, 'latest_week':latest_week, 'other_weeks':other_weeks})
    
def drive_outcomes(request, season):
    outcomes = GameDriveSeason.objects.select_related().filter(season=season, outcome__name='Touchdown').order_by('-total')[:50]
    return render_to_response('rankings/drive_outcomes.html', {'outcomes':outcomes, 'season': season})
