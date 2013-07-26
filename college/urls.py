from django.conf.urls.defaults import *
from django.contrib.sitemaps.views import sitemap
from sitemaps import all_sitemaps
from views import player_detail, team_players, player
from college.api import CollegeResource, CollegeYearResource, CoachResource, CollegeCoachResource, GameResource
from tastypie.api import Api

v1_api = Api(api_name='v1')
v1_api.register(CollegeResource())
v1_api.register(CollegeYearResource())
v1_api.register(CoachResource())
v1_api.register(CollegeCoachResource())
v1_api.register(GameResource())

urlpatterns = patterns('college.views',
     url(r'^seasons/(?P<season>\d+)/week/(?P<week>\d+)/$', 'season_week'),
     url(r'^custom-rankings/fewest-rushing-yards-lost/(?P<season>\d+)/$', 'rushing_losses'),
     url(r'^conferences/$', 'conference_index'),
     url(r'^conferences/(?P<conf>[-a-z0-9]+)/$', 'conference_detail'),
     url(r'^conferences/(?P<conf>[-a-z0-9]+)/(?P<season>\d+)/$', 'conference_detail'),
     url(r'^games/$', 'game_index'),
     url(r'^bowl-games/$', 'bowl_games'),
     url(r'^bowl-games/(?P<bowl>[-a-z]+)/$', 'bowl_game_detail'),
     url(r'^bowl-games/(?P<season>\d{4})/$', 'bowl_game_season'),
     url(r'^teams(\.(?P<format>(html|rdf\+xml|rdf\+nt)))?/$', 'team_index'),
     url(r'^teams/undefeated/(?P<season>\d+)/$', 'undefeated_teams'),
     url(r'^teams/(?P<team>[-a-z]+)/$', 'team_detail', name="team_detail"),
     url(r'^teams/(?P<team>[-a-z]+)/coaching-history/$', 'team_coaching_history', name="tch"),
     url(r'^teams/(?P<team>[-a-z]+)/alums-in-coaching/$', 'alums_in_coaching', name="alum_coach"),
     url(r'^teams/(?P<team>[-a-z]+)/bowl-games/$', 'team_bowl_games'),
     url(r'^teams/(?P<team>[-a-z]+)/offense/$', 'team_offense'),
     url(r'^teams/(?P<team>[-a-z]+)/offense/rushing/$', 'team_offense_rushing'),
     url(r'^teams/(?P<team>[-a-z]+)/defense/$', 'team_defense'),
     url(r'^teams/(?P<team>[-a-z]+)/penalties/$', 'team_penalties'),
     url(r'^teams/(?P<team>[-a-z]+)/first-downs/$', 'team_first_downs'),
     url(r'^teams/(?P<team>[-a-z]+)/first-downs/(?P<category>rushing|passing|penalty)/$', 'team_first_downs_category'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/$', 'team_detail_season', name="team_detail_season"),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/drives/$', 'team_drives_season', name="team_drives_season"),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/coaches/$', 'team_coaches_season'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/rankings/$', 'team_rankings_season'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/rankings/week/(?P<week>\d+)/$', 'team_rankings_season'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/rankings/(?P<rankingtype>[-a-z]+)/$', 'team_ranking_detail'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/classes/(?P<cl>[fr|so|jr|sr])/$', 'team_by_cls'),
     url(r'^teams/(?P<team>[-a-z]+)/opponents/$', 'team_opponents'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/players/$', team_players, name="college_team_players"),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/players/positions/(?P<pos>[a-z][a-z][a-z]?)/$', 'team_position_detail', name="team_pos_det"),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/players/class/(?P<cls>[a-z][a-z][a-z]?)/$', 'team_class_detail'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/players/(?P<player>[-a-z]+)/(?P<number>[0-9a-zA-Z]{1,3})/(?P<position>[A-Za-z]{1,3})/$', player_detail, name='college_player_number_position'),
     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/players/(?P<player>[-a-z]+)/$', player, name='college_player'),
#     url(r'^teams/(?P<team>[-a-z]+)/(?P<season>\d+)/players/(?P<player>[-a-z]+)/vs/(?P<team2>[-a-z]+)/$', player_vs_team, name='college_player_vs_team'),
     url(r'^teams/(?P<team>[-a-z]+)/vs_conference/(?P<conference>[-a-z]+)/$', 'team_vs_conference'),
     url(r'^teams/(?P<team1>[-a-z]+)/vs/(?P<team2>[-a-z]+)/$', 'team_vs', name='team_vs'),
     url(r'^teams/(?P<team1>[-a-z]+)/vs/(?P<team2>[-a-z]+)/(?P<outcome>wins|losses|ties)/$', 'team_vs'),
     url(r'^teams/(?P<team1>[-a-z]+)/vs/(?P<team2>[-a-z]+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$', 'game', name="game_detail"),
     url(r'^teams/(?P<team1>[-a-z]+)/vs/(?P<team2>[-a-z]+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/drives/$', 'game_drive'),
     url(r'^teams/(?P<team1>[-a-z]+)/vs/(?P<team2>[-a-z]+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/plays/$', 'game_plays'),
     url(r'^states/$', 'state_index'),
     url(r'^states/(?P<state>[a-z][a-z])/$', 'state_detail'),
     url(r'^sitemap\.xml$', sitemap, {'sitemaps': all_sitemaps}),
     
     # API urls
     url(r'^api/', include(v1_api.urls)),
     
)
