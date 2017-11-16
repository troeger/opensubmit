# -*- coding: utf-8 -*-


from django.db import migrations, models

def move_max_authors(apps, schema_editor):
    Course = apps.get_model("opensubmit", "Course")
    for course in Course.objects.all():
        max_authors=course.max_authors
        for assignment in course.assignments.all():
            assignment.max_authors=max_authors
            print("Setting max authors for assignment '{0}' in course '{1}'...".format(assignment.title, course.title))
            assignment.save()

def reverse(apps, schema_editor):
    Assignment = apps.get_model("opensubmit", "Assignment")
    for ass in Assignment.objects.all():
        ass.max_authors=1 # default
        ass.save()

class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0021_auto_20171011_2218'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='max_authors',
            field=models.PositiveSmallIntegerField(default=1, help_text=b'Maximum number of authors (= group size) for this assignment.'),
        ),
        migrations.RunPython(move_max_authors, reverse),
    ]
