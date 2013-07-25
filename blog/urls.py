from django.conf.urls.defaults import *
from blog.models import Post
from blog.views import *
from blog.feeds import LatestPostFeed
 
feeds = {
    "latest": LatestPostFeed,
}
 
date_based_dict = {
    "date_field": "pub_date",
}
 
urlpatterns = patterns("",
    url(r"^$", homepage ),

    url(r"^feeds/(?P<url>.*)/$", "django.contrib.syndication.views.Feed", {
        "feed_dict": feeds,
    }, name="blog_feeds"),
    
    url(r"^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$",
        object_detail, dict(date_based_dict, **{
            "template_object_name": "post",
        }), name="blog_post_detail"),
    url(r"^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$",
        archive_day, date_based_dict, name="blog_archive_daily"),
    url(r"^(?P<year>\d{4})/(?P<month>[a-z]{3})/$",
        archive_month, date_based_dict, name="blog_archive_month"),
    url(r"^(?P<year>\d{4})/$",
        archive_year, date_based_dict, name="blog_archive_year"),
)