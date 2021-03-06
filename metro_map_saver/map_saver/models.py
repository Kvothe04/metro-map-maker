import json

from django.db import models
from citysuggester.utils import suggest_city
from taggit.managers import TaggableManager

PUBLICLY_VISIBLE_TAGS = [
    'real',
    'speculative',
    'unknown',
]

# Having any of these tags excludes you from public visibility
EXCLUDED_TAGS = [
    'reviewed',
    'excluded',
]

class SavedMap(models.Model):

    """ Saves map data and its corresponding urlhash together so that maps can be easily shared
    """

    urlhash = models.CharField(max_length=64)
    mapdata = models.TextField()
    # gallery_visible: should this be shown in the default view of the Admin Gallery?
    gallery_visible = models.BooleanField(default=True, db_index=True)
    # publicly_visible: should this be shown in the publicly-visible gallery?
    #   (using this to improve speed and reduce query complexity)
    publicly_visible = models.BooleanField(default=False, db_index=True)
    name = models.CharField(max_length=255, blank=True, default='')
    thumbnail = models.TextField(blank=True, default='')
    stations = models.TextField(blank=True, default='')
    station_count = models.IntegerField(default=-1)
    created_at = models.DateField(auto_now_add=True)

    # Create a token that can be used for creators to be able to name their maps
    # but subsequent visitors to that map will not be able to rename it
    naming_token = models.CharField(max_length=64, blank=True, default='')

    # Store the suggested city (if any) so we can refer to it
    # without needing to calculate it every time
    # Consider: making suggested_city a foreign key to TravelSystem
    #   this would also mean that renaming a TravelSystem wouldn't
    #   require re-saving maps with that suggested_city to prevent 500 errors in the admin
    #   (though I don't re-name TravelSystems often)
    suggested_city = models.CharField(max_length=255, blank=True, default='')
    suggested_city_overlap = models.IntegerField(default=-1)

    tags = TaggableManager(blank=True)

    def _suggest_city(self, overlap=None):

        """ Override overlap to specify the number of stations
            that must overlap to be considered a match;
            uses utils.MINIMUM_STATION_OVERLAP otherwise
        """

        return suggest_city(set(self.stations.lower().split(',')), overlap)

    def _get_stations(self):

        """ Returns a set of station names from a given mapdata
        """

        stations = set()
        try:
            mapdata = json.loads(self.mapdata)
        except Exception:
            return ''

        for x in mapdata:
            for y in mapdata[x]:
                if 'station' in mapdata[x][y]:
                    stations.add(mapdata[x][y]['station'].get('name', '').lower())

        return ','.join(stations)

    def _station_count(self):
        if self.stations:
            return self.stations.count(',')
        else:
            return 0

    @property
    def _publicly_visible(self):
        # New maps won't have an ID; can't access tags until a map has an ID
        if not self.id:
            return
        return all([
            self.gallery_visible,
            self.name,
            self.thumbnail,
        ]) and (
            set([tag.slug for tag in self.tags.all()]).intersection(set(PUBLICLY_VISIBLE_TAGS)) \
            and not set([tag.slug for tag in self.tags.all()]).intersection(set(EXCLUDED_TAGS))
        )

    def __str__(self):
        return self.urlhash

    def save(self, *args, **kwargs):
        self.stations = self._get_stations()
        self.station_count = self._station_count()
        self.name = self.name.strip()
        self.thumbnail = self.thumbnail.strip()
        if self._publicly_visible:
            self.publicly_visible = True
        else:
            self.publicly_visible = False
        suggested_city = self._suggest_city()
        if suggested_city:
            self.suggested_city = suggested_city[0][0].split("(")[0].strip()
            self.suggested_city_overlap = suggested_city[0][1]
        super().save(*args, **kwargs)

    class Meta:
        permissions = (
            ('hide_map', "Can set a map's gallery_visible to hidden"),
            ('name_map', "Can set a map's name"),
            ('tag_map', "Can change the tags associated with a map"),
            ('generate_thumbnail', "Can generate thumbnails for a map"),
            ('edit_publicly_visible', "Can edit a publicly visible map"),
        )
