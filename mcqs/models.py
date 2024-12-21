from django.db import models
from base.models import BaseModel
# Create your models here.
from uuid import UUID
import uuid

from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
class Subject(BaseModel):
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']







class Unit(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='units')
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.subject.name} - Unit {self.name}"
    class Meta:
        ordering = ['subject','order']

        
class Chapter(BaseModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='chapters')
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.unit.subject.name} - Unit {self.unit.name} - Chapter {self.name}"
    class Meta:
        ordering = ['order']


class Topic(BaseModel):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='topics')
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.chapter.unit.subject.name} - Unit {self.chapter.unit.name} - Chapter {self.chapter.name} - Topic {self.name}"
    class Meta:
        ordering = ['order']


class difficulties(BaseModel):
    
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name
    
class mcq_types(BaseModel):
    
    types = models.CharField(max_length=255)
    def __str__(self):
        return self.types

class MCQ(BaseModel):
    bulk_input = models.TextField(blank=True,null=True)

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topics',null=True)
    text = models.TextField(default='Default question text')
    option_1 = models.CharField(max_length=255,blank=True, null=True)
    option_2 = models.CharField(max_length=255,blank=True, null=True)
    option_3 = models.CharField(max_length=255,blank=True, null=True)
    option_4 = models.CharField(max_length=255,blank=True, null=True)
    correct_option = models.CharField(max_length=255,blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='mcq_images/', blank=True, null=True)
   
    difficulty = models.ForeignKey(difficulties, on_delete=models.CASCADE,related_name='difficulty',blank=True, null=True)
    types = models.ForeignKey(mcq_types, on_delete=models.CASCADE, related_name='type',blank=True, null=True)
    
    def __str__(self):
        return self.text
    
    def save(self,*args, **kwargs):
        if self.bulk_input:
            parts = self.bulk_input.split('|')
            if len(parts)==7:
                    self.text=parts[0]
                    self.option_1=parts[1]
                    self.option_2=parts[2]
                    self.option_3=parts[3]
                    self.option_4=parts[4]
                    self.correct_option=parts[5]

                    self.explanation=parts[6]
            self.bulk_input = ''

        
        super(MCQ,self).save(*args,**kwargs)


from datetime import datetime

class TestSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_id = models.CharField(max_length=100, unique=True)  # Unique ID for the test session
     # Remaining time in seconds
    timestamp = models.DateTimeField(auto_now=True)  #t Track when the session was last updaed
    submitted = models.BooleanField(default=False)
    score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=datetime.now)
    total_questions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    timetaken = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Track when the session was created
    totaltime = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selections = models.JSONField(default=list)
    def __str__(self):
        return f"TestSession for {self.user.username} with Test ID {self.test_id}"

class TestAnswer(models.Model):
    test_session = models.ForeignKey(TestSession, on_delete=models.CASCADE)
    mcq_uid = models.UUIDField()  # UID of the MCQ
    selected_option = models.CharField(max_length=10, blank=True, null=True)  # Selected answer option
    timespent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_attempted = models.BooleanField(default=False)  # Track if the question has been attempted
    selected_optiontext = models.CharField(max_length=255, blank=True, null=True)
    correct = models.BooleanField(default=False)
    def __str__(self):
        return f"Answer for {self.mcq_uid} in Test ID {self.test_session.test_id}"

class Bookmark(models.Model):
    TYPE_CHOICES = [
        ('Star', 'Star'),
        ('Unstudied', 'Unstudied'),
        ('Other', 'Other')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bkmk_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # Allowing null and blank
    mcq = models.ForeignKey(MCQ, on_delete=models.CASCADE)
    test_session = models.ForeignKey(TestSession, on_delete=models.CASCADE)
    bookmark_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(default=datetime.now)

    class Meta:
        unique_together = ('user', 'mcq', 'test_session')
