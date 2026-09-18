from django.contrib import admin

from .models import Announcement, Assignment, ClassRoom, Submission

admin.site.register(ClassRoom)
admin.site.register(Announcement)
admin.site.register(Assignment)
admin.site.register(Submission)
