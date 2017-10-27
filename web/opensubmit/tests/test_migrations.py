'''
	Test cases for data migrations.
'''

from .cases import TestMigrations

class TagsTestCase(TestMigrations):

    migrate_from = '0021_auto_20171011_2218'
    migrate_to =   '0022_assignment_max_authors'

    def setUpBeforeMigration(self, apps):
    	pass

    def test_max_authos_migrated(self):
        Assignment = self.apps.get_model('opensubmit', 'Assignment')
        for ass in Assignment.objects.all():
        	self.AssertEqual(ass.max_authors, ass.course.max_authors)
