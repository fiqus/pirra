from ckeditor.fields import RichTextField
from django.db import models

# Create your models here.

class FrequentlyAskedQuestion(models.Model):
    question = models.TextField()
    answer = RichTextField()
    published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)


    class Meta(object):
        ordering = ('order',)

    def __str__(self):
        return self.question


class LatestNews(models.Model):
    date = models.DateField()
    title = models.TextField()
    description = RichTextField()

    def __str__(self):
        return "{} - {}".format(self.date, self.title)