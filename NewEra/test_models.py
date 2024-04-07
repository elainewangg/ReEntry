from django.test import TestCase
from NewEra.models import User, CaseLoadUser, Referral, Resource, Tag, Organization

import datetime

# Test cases for User model
class UserTests(TestCase):

	def test_printing(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_superuser=True)
		brenth = User.objects.create_user(username="brenth", password="testsyay", first_name="Brent", last_name="Hong")
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		self.assertEqual(str(admin), "admin (Admin Guy)")
		self.assertEqual(str(brenth), "brenth (Brent Hong)")
		self.assertEqual(str(maxk), "maxk (Max Kornyev)")
		self.assertEqual(str(joeyp), "joeyp (Joey Perrino)")

        # Delete users
		admin.delete()
		brenth.delete()
		maxk.delete()
		joeyp.delete()

	def test_active_users(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_superuser=True)
		brenth = User.objects.create_user(username="brenth", password="testsyay", first_name="Brent", last_name="Hong", is_reentry_coordinator=True)
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net", is_supervisor=True)
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		self.assertEqual(admin.is_active, True)
		self.assertEqual(brenth.is_active, True)
		self.assertEqual(maxk.is_active, True)
		# joeyp should be inactive
		self.assertEqual(joeyp.is_active, False)

		# Delete users
		admin.delete()
		brenth.delete()
		maxk.delete()
		joeyp.delete()

	def test_superuser(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_superuser=True)
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		
		self.assertEqual(admin.is_superuser, True)
		self.assertEqual(maxk.is_superuser, False)

		# Delete users
		admin.delete()
		maxk.delete()
	
	def test_supvervisor(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_supervisor=True)
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net", is_supervisor=False)
		
		self.assertEqual(admin.is_supervisor, True)
		self.assertEqual(maxk.is_supervisor, False)

		# Delete users
		admin.delete()
		maxk.delete()

	def test_case_load(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_superuser=True)
		brenth = User.objects.create_user(username="brenth", password="testsyay", first_name="Brent", last_name="Hong")
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="George", last_name="Test", email="test@test.net", phone="5555555555", user=brenth)
		c2 = CaseLoadUser.objects.create(first_name="Martha", last_name="Test", email="testing@site.org", phone="6666666666",  user=brenth)
		c3 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)

		self.assertEqual(c1.user, brenth)
		self.assertEqual(c2.user, brenth)
		self.assertTrue(len(list(CaseLoadUser.objects.all())) > 0)
		self.assertEqual(len(list(brenth.get_case_load())), 2)
		self.assertEqual(len(list(maxk.get_case_load())), 1)
		self.assertEqual(len(list(joeyp.get_case_load())), 0)

		# Delete caseload
		c1.delete()
		c2.delete()
		c3.delete()
		# Delete users
		admin.delete()
		brenth.delete()
		maxk.delete()
		joeyp.delete()

	def test_get_referrals(self):
		# Set up users
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		brenth = User.objects.create_user(username="brenth", password="testtest", first_name="Brent", last_name="Hong", is_active=True)
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)
		c2 = CaseLoadUser.objects.create(first_name="Martin", last_name="Tester", email="xyz@test.com", phone="2222222222",  user=maxk)

		# Set up referrals
		r1 = Referral.objects.create(phone="7777777777", notes="check back next week", user=maxk, caseUser=c1)
		r2 = Referral.objects.create(email="test@abcd.com", phone="5656565656", notes="make sure they are still open", user=joeyp)
		r3 = Referral.objects.create(phone="7777777777", notes="keep it up!", user=maxk, caseUser=c1)
		r4 = Referral.objects.create(phone="2222222222", notes="hope this helps", user=maxk, caseUser=c2)

		self.assertEqual(maxk.get_referrals().count(), 3)
		self.assertEqual(brenth.get_referrals().count(), 0)
		self.assertEqual(joeyp.get_referrals().count(), 1)

		# Delete referrals
		r1.delete()
		r2.delete()
		r3.delete()
		r4.delete()
		# Delete caseload
		c1.delete()
		c2.delete()
		# Delete users
		brenth.delete()
		maxk.delete()
		joeyp.delete()


# Test cases for individuals on a case load
class CaseLoadUserTests(TestCase):

	def test_printing(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_superuser=True)
		brenth = User.objects.create_user(username="brenth", password="testsyay", first_name="Brent", last_name="Hong")
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="George", last_name="Test", email="test@test.net", phone="5555555555",  user=brenth)
		c2 = CaseLoadUser.objects.create(first_name="Martha", last_name="Test", email="testing@site.org", phone="6666666666", user=brenth)
		c3 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)

		self.assertEqual(str(c1), "George Test, phone number 5555555555")
		self.assertEqual(str(c2), "Martha Test, phone number 6666666666")
		self.assertEqual(str(c3), "Steve Test, phone number 7777777777")

		# Delete caseload
		c1.delete()
		c2.delete()
		c3.delete()
		# Delete users
		admin.delete()
		brenth.delete()
		maxk.delete()
		joeyp.delete()

	def test_full_name(self):
		# Set up users
		admin = User.objects.create_user(username="admin", password="administrator45", first_name="Admin", last_name="Guy", email="testemail@check.com", phone="5555555556", is_superuser=True)
		brenth = User.objects.create_user(username="brenth", password="testsyay", first_name="Brent", last_name="Hong")
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="George", last_name="Test", email="test@test.net", phone="5555555555",  user=brenth)
		c2 = CaseLoadUser.objects.create(first_name="Martha", last_name="Test", email="testing@site.org", phone="6666666666", user=brenth)
		c3 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)

		self.assertEqual(c1.get_full_name(), "George Test")
		self.assertEqual(c2.get_full_name(), "Martha Test")
		self.assertEqual(c3.get_full_name(), "Steve Test")

		# Delete caseload
		c1.delete()
		c2.delete()
		c3.delete()
		# Delete users
		admin.delete()
		brenth.delete()
		maxk.delete()
		joeyp.delete()

	def test_get_referrals(self):
		# Set up users
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)
		c2 = CaseLoadUser.objects.create(first_name="Martin", last_name="Tester", email="xyz@test.com", phone="2222222222",  user=maxk)
		c3 = CaseLoadUser.objects.create(first_name="Mary", last_name="Testing", email="abc@defg.com", phone="5555555555", user=joeyp)

		# Set up referrals
		r1 = Referral.objects.create(phone="7777777777", notes="check back next week", user=maxk, caseUser=c1)
		r2 = Referral.objects.create(email="test@abcd.com", phone="5656565656", notes="make sure they are still open", user=joeyp)
		r3 = Referral.objects.create(phone="7777777777", notes="keep it up!", user=maxk, caseUser=c1)
		r4 = Referral.objects.create(phone="2222222222", notes="hope this helps", user=maxk, caseUser=c2)

		self.assertEqual(c1.get_referrals().count(), 2)
		self.assertEqual(c2.get_referrals().count(), 1)
		self.assertEqual(c3.get_referrals().count(), 0)

		# Delete referrals
		r1.delete()
		r2.delete()
		r3.delete()
		r4.delete()
		# Delete caseload
		c1.delete()
		c2.delete()
		c3.delete()
		# Delete users
		maxk.delete()
		joeyp.delete()


# Test cases for referrals
class ReferralTests(TestCase):

	def test_printing(self):
		# Set up users
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)
		c2 = CaseLoadUser.objects.create(first_name="Martin", last_name="Tester", email="xyz@test.com", phone="2222222222", user=maxk)

		# Set up referrals
		r1 = Referral.objects.create(phone="7777777777", notes="check back next week", user=maxk, caseUser=c1)
		r2 = Referral.objects.create(email="test@abcd.com", phone="5656565656", notes="make sure they are still open", user=joeyp)
		r3 = Referral.objects.create(phone="7777777777", notes="keep it up!", user=maxk, caseUser=c1)
		r4 = Referral.objects.create(phone="2222222222", notes="hope this helps", user=maxk, caseUser=c2)

		self.assertEqual(str(r1), "Referral sent to 7777777777 by Max Kornyev on %s" % datetime.datetime.now().strftime("%m-%d-%Y"))
		self.assertEqual(str(r2), "Referral sent to 5656565656 by Joey Perrino on %s" % datetime.datetime.now().strftime("%m-%d-%Y"))
		self.assertEqual(str(r3), "Referral sent to 7777777777 by Max Kornyev on %s" % datetime.datetime.now().strftime("%m-%d-%Y"))
		self.assertEqual(str(r4), "Referral sent to 2222222222 by Max Kornyev on %s" % datetime.datetime.now().strftime("%m-%d-%Y"))

		# Delete referrals
		r1.delete()
		r2.delete()
		r3.delete()
		r4.delete()
		# Delete caseload
		c1.delete()
		c2.delete()
		# Delete users
		maxk.delete()
		joeyp.delete()


class TagTests(TestCase):

	def test_printing(self):
		# Set up tags
		tag1 = Tag.objects.create(name="Housing", tag_type="Housing and Needs")
		tag2 = Tag.objects.create(name="Employment", tag_type="Employment")

		self.assertEqual(str(tag1), "Housing")
		self.assertEqual(str(tag2), "Employment")

		# Delete tags
		tag1.delete()
		tag2.delete()


class ResourceTests(TestCase):

	def test_printing(self):
		# Set up users
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)

		# Set up referrals
		r1 = Referral.objects.create(phone="7777777777", notes="check back next week", user=maxk, caseUser=c1)
		r2 = Referral.objects.create(email="test@abcd.com", phone="5656565656", notes="make sure they are still open", user=joeyp)

		# Set up resources
		res1 = Resource.objects.create(name="First Test Resource", email="testresource@res.test")
		res2 = Resource.objects.create(name="Second Test Resource", email="testresource2@res.test")

		# Set up tags
		tag1 = Tag.objects.create(name="Housing", tag_type="Housing and Needs")
		tag2 = Tag.objects.create(name="Employment", tag_type="Employment")

		# Set up many-to-many fields
		res1.tags.add(tag1)
		res1.tags.add(tag2)
		res2.tags.add(tag1)

		res1.referrals.add(r1)
		res2.referrals.add(r1)
		res2.referrals.add(r2)

		self.assertEqual(str(res1), "First Test Resource")
		self.assertEqual(str(res2), "Second Test Resource")

		# Delete resources
		res1.delete()
		res2.delete()
		# Delete referrals
		r1.delete()
		r2.delete()
		# Delete caseload
		c1.delete()
		# Delete users
		maxk.delete()
		joeyp.delete()
		# Delete tags
		tag1.delete()
		tag2.delete()

	def test_many_to_many(self):
		# Delete relevant models
		User.objects.all().delete()
		CaseLoadUser.objects.all().delete()
		Resource.objects.all().delete()
		Tag.objects.all().delete()
		Referral.objects.all().delete()

		# Set up users
		maxk = User.objects.create_user(username="maxk", password="testtime", first_name="Max", last_name="Kornyev", email="maxk@testingsuite.net")
		joeyp = User.objects.create_user(username="joeyp", password="testtest", first_name="Joey", last_name="Perrino", is_active=False)

		# Set up case load
		c1 = CaseLoadUser.objects.create(first_name="Steve", last_name="Test", email="test@abcd.com", phone="7777777777",  user=maxk)

		# Set up referrals
		r1 = Referral.objects.create(phone="7777777777", notes="check back next week", user=maxk, caseUser=c1)
		r2 = Referral.objects.create(email="test@abcd.com", phone="5656565656", notes="make sure they are still open", user=joeyp)

		# Set up resources
		res1 = Resource.objects.create(name="First Test Resource", email="testresource@res.test")
		res2 = Resource.objects.create(name="Second Test Resource", email="testresource2@res.test")

		# Set up tags
		tag1 = Tag.objects.create(name="Housing", tag_type="Housing and Needs")
		tag2 = Tag.objects.create(name="Employment", tag_type="Employment")

		self.assertEqual(res1.tags.count(), 0)
		self.assertEqual(res2.tags.count(), 0)

		self.assertEqual(res1.referrals.count(), 0)
		self.assertEqual(res2.referrals.count(), 0)

		# Set up many-to-many fields
		res1.tags.add(tag1)
		res1.tags.add(tag2)
		res2.tags.add(tag1)

		res1.referrals.add(r1)
		res2.referrals.add(r1)
		res2.referrals.add(r2)

		self.assertEqual(res1.tags.count(), 2)
		self.assertEqual(res2.tags.count(), 1)

		self.assertEqual(res1.referrals.count(), 1)
		self.assertEqual(res2.referrals.count(), 2)

		# Delete resources
		res1.delete()
		res2.delete()
		# Delete referrals
		r1.delete()
		r2.delete()
		# Delete caseload
		c1.delete()
		# Delete users
		maxk.delete()
		joeyp.delete()
		# Delete tags
		tag1.delete()
		tag2.delete()

class OrganizationTests(TestCase):
	def test_printing(self):
		# Set up organizations
		organization1 = Organization.objects.create(name="CMU")
		organization2 = Organization.objects.create(name="REACH")

		self.assertEqual(str(organization1), "CMU")
		self.assertEqual(str(organization2), "REACH")

		# Delete tags
		organization1.delete()
		organization2.delete()
		
	def test_active_organizations(self):
		organization1 = Organization.objects.create(name="CMU")
		organization2 = Organization.objects.create(name="REACH",is_active=False)

		self.assertEqual(organization1.is_active, True)
		self.assertEqual(organization2.is_active, False)

		# Delete tags
		organization1.delete()
		organization2.delete()

	def test_one_to_many(self):
		organization1 = Organization.objects.create(name="CMU")
		member1 = User.objects.create_user(username="test1", password="test", first_name="John", last_name="Doe", organization=organization1)
		member2 = User.objects.create_user(username="test2", password="test", first_name="Adam", last_name="Carter", organization=organization1)

		self.assertEqual(member1.organization.name,"CMU")
		self.assertEqual(member2.organization.name,"CMU")

		member1.delete()
		member2.delete()
		organization1.delete()
		

	
	
