from django.db import models

# Create your models here.


class Bots(models.Model):
    id = models.CharField(max_length=30,primary_key=True)
    name = models.CharField(max_length=511, blank=False)
    score = models.IntegerField()

    class Meta:
        managed = False
        db_table = u'bots'

    def __unicode__(self):
        return self.name