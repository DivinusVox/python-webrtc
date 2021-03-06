import uuid, datetime, posixpath, logging, json

from django.utils import timezone
from django.db import models, transaction, IntegrityError

from django.core import serializers
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory, Client

from django.contrib.auth.models import User, UserManager
from django.forms.models import model_to_dict

from .helpers import DateTimeAwareEncoder, DateTimeAwareDecoder

from .models import Profile, Message, Conversation
from .forms import ProfileForm, UserForm, MessageForm
from .views import (UserCreateView, UserAuthenticateView, UserRestView, ProfileRestView,
	MessageRestView, MessageCreateView, ConversationRestView,
	ConversationCreateView, API_RESULT, API_SUCCESS, API_FAIL, API_ERROR)

logger = logging.getLogger(__name__)

CORE_ASSETLIST_JS = ('jquery', 'underscore', 'backbone', 'modernizr', 'foundation')
CORE_ASSETLIST_CSS = ('normalize', 'foundation')

username = 'testuser'
invalidPk = 9999

def login(client, username='guru', password='work', user=None):
	''' helper method to log user in.  If you specify user you must
		also specify password.
		@input client - required Test Unit Client
		@input username - optional (you must have this or user, if you use this it will
			create the user for you)
		@input password - required
		@input user - optional (you must have this or username)
	'''
	if user is None:
		u = User.objects.create_user(username=username)
		u.set_password(password)
	else:
		u = user
	u.save()

	userDict = model_to_dict(u)
	userDict['password'] = password

	client.user = u
	client.login(username='guru', password='work')

	jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

	response = client.post(reverse('chat:api:user-authenticate'), data=jsonData,
		content_type='application/json')
	rdata = json.loads(response.content)

	if response.status_code != 200:
		raise Exception("Error logging in %s" % response.content)
	return rdata


class DatabaseTests(TestCase):

	def __init__(self, *args, **kwargs):
		super(DatabaseTests, self).__init__(*args, **kwargs)

	def testCreateUserProfile(self):
		''' Tests the creation of a chat user and user profile
		'''
		# Create test user
		user = User.objects.create(username=username)
		user.save()
		# Create user profile
		userp = Profile(user=user)
		userp.save()

		# Do some basic tests to make sure it's saved into the database properly
		self.assertEqual(username, user.username)
		self.assertEqual(user.username, Profile.objects.get(pk=user.pk).user.username)
		self.assertEqual(len(Profile.objects.all()), 1)

	def testConversationIds(self):
		''' tests the creation and saving of conversation ids
		'''
		convo = Conversation()
		convo.save()
		self.assertFalse((convo.id == '') or (convo.id is None), "Something isn't working"
			+ " with conversation id generation")

	def testMessageIds(self):
		''' tests the creation and saving of message ids
		'''
		user = User.objects.create(username=username)
		msg = Message(sender=user, text='heres some text')
		msg.save()
		self.assertFalse((msg.id == '') or (msg.id is None), "Something isn't working"
			+ " with message id generation")


class GenericViewTests(TestCase):

	def testIndexPage(self):
		'''	Verify that the application is able to retrieve the index page and that
			all base assets are available.
		'''
		r = self.client.get(reverse('chat:appindex'))
		self.assertEqual(200, r.status_code)
		# Check page title
		self.assertIn('Guru Labs Chat Demo Application', r.content)
		# Verify that all core assets are available for use
		for assetlist in (CORE_ASSETLIST_JS, CORE_ASSETLIST_CSS):
			for assetname in assetlist: self.assertIn(assetname, r.content)


class UserViewTests(TestCase):

	def __init__(self, *args, **kwargs):
		self.factory = RequestFactory()
		self.user = None
		super(UserViewTests, self).__init__(*args, **kwargs)

	def setUp(self):
		# Create test user
		self.user = User.objects.create_user(username=username, password='work')
		self.user.save()
		self.view = UserRestView()
		self.createView = UserCreateView()
		self.authView = UserAuthenticateView()

	def testGetSuccess(self):
		''' tests a successfull User Get request
		'''
		login(self.client)
	
		response = self.client.get(reverse('chat:api:user-rest',
			args=(str(self.user.pk),)), pk=str(self.user.pk))

		userObj = json.loads(response.content, cls=DateTimeAwareDecoder)
		userForm = UserForm(userObj, instance=User.objects.get(
			pk=self.user.pk))

		self.assertEqual(userForm.is_valid(), True)

	def testGetError(self):
		''' tests an attempt to get an invalid user with an invalid primary key value
		'''
		login(self.client)

		response = self.client.get(reverse('chat:api:user-rest', args=(str(invalidPk), )),
			pk=str(invalidPk))

		rdata = json.loads(response.content, cls=DateTimeAwareDecoder)

		self.assertEquals(response.status_code, 404)

	def testPutSuccess(self):
		''' Successfully updates a user through a Put request
		'''
		login(self.client, user=self.user, password='work')

		userDict = model_to_dict(self.user)
		# lets change the email address
		userDict['email'] = 'guru@guru.com'

		jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

		response = self.client.put(
			reverse('chat:api:user-rest',
			args=(self.user.pk, ) ),
			data=jsonData,
			content_type='application/json')

		rdata = json.loads(response.content)


		# make sure the response was a 200 (OK)
		self.assertEquals(response.status_code, 200)

		# make sure the email got updated
		self.assertEquals(User.objects.get(pk=self.user.pk).email, userDict['email'])

	def testPutError(self):
		''' unsuccessfully updates the user - invalid user id
		'''
		login(self.client, username='new username', password='work')

		userDict = {}
		userDict['username'] = 'new username'
		userDict['first_name'] = 'Mr'
		userDict['last_name'] = 'Guru'
		userDict['email'] = 'guru@guru.com'
		userDict['password1'] = 'work'
		userDict['password2'] = 'work'
		userDict['email'] = 'guru@gurulabs.com'
		jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:user-rest', args=(invalidPk,)),
		 data=jsonData, content_type='application/json')

		self.assertEquals(response.status_code, 400)

	def testUserAuthenticate(self):
		''' tests the login method to ensure it's working.  Errors are thrown within 
				login.
		'''
		rdata = login(self.client)


	def testUserRegisterSuccess(self):
		''' tests user register successfully
		'''
		userDict = {}
		userDict['username'] = 'gurulab'
		userDict['first_name'] = 'Mr'
		userDict['last_name'] = 'Guru'
		userDict['email'] = 'guru@guru.com'
		userDict['password1'] = 'work'
		userDict['password2'] = 'work'

		count = len(User.objects.all())
		countProfiles = len(Profile.objects.all())
		jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:user-create'), data=jsonData,
			content_type='application/json')

		rdata = json.loads(response.content)

		# make sure everything got updated that should have
		self.assertEquals(response.status_code, 200)
		self.assertEquals(count + 1, len(User.objects.all()))
		self.assertEquals(countProfiles + 1, len(Profile.objects.all()))
		try:
			newUserObj = User.objects.get(pk=rdata['id'])
			profile = Profile.objects.get(user=newUserObj)
		except User.DoesNotExist:
			self.assertTrue(False, "User doesn't exist when it should...")
		except Profile.DoesNotExist:
			self.assertFalse(True, "Profile creation didn't occur")


	def testUserRegisterFail(self):
		''' tests user register failure due to differing password/verify_password values
		'''
		userDict = {}
		userDict['username'] = 'gurulab'
		userDict['first_name'] = 'Mr'
		userDict['last_name'] = 'Guru'
		userDict['email'] = 'guru@guru.com'
		userDict['password1'] = 'work'
		userDict['password2'] = 'not_work'

		count = len(User.objects.all())
		jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:user-create'), data=jsonData,
			content_type='application/json')
		rdata = json.loads(response.content)

		self.assertEquals(response.status_code, 400)
		self.assertEquals(count, len(User.objects.all()))

	def testUserRegisterFailUnuniqueUsername(self):
		''' tests user register failure due to username already in use
		'''
		user = User.objects.create_user(username='gurulab')
		user.save()
		userDict = {}
		userDict['username'] = 'gurulab'
		userDict['first_name'] = 'Mr'
		userDict['last_name'] = 'Guru'
		userDict['email'] = 'guru@guru.com'
		userDict['password1'] = 'work'
		userDict['password2'] = 'work'

		count = len(User.objects.all())
		countProfiles = len(Profile.objects.all())
		jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:user-create'), data=jsonData,
			content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(response.status_code, 400)
		self.assertEquals(count, len(User.objects.all()))
		self.assertEquals(countProfiles, len(Profile.objects.all()))


	def testDeleteSuccess(self):
		''' tests deletion of user through delete request
		'''

		user = User.objects.create_user(username='gurus lab coat', password='work')
		user.save()

		login(self.client, user=user)

		count = len(User.objects.all())

		response = self.client.delete(reverse('chat:api:user-rest',
			args=(user.pk, )), content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(len(User.objects.all()), count - 1)

		with self.assertRaises(User.DoesNotExist):
			User.objects.get(pk=rdata['id'])

	def testDeleteFailure(self):
		''' failed delete due to invalid user id
		'''
		login(self.client)

		count = len(User.objects.all())
		response = self.client.delete(reverse('chat:api:user-rest',
			args=(invalidPk, )), content_type='application/json')

		self.assertEquals(response.status_code, 400)
		self.assertEquals(len(User.objects.all()), count)


	def testPostFailure(self):
		''' failed user create due to user id being the same as another id
		'''
		login(self.client)

		userDict = model_to_dict(self.user)
		# invalidPk isn't used in db yet (not enforced by anything but for the tests to
		#	work thats how it has to be)
		userDict['id'] = self.user.pk
		userDict['username'] = username
		count = len(User.objects.all())

		jsonData = json.dumps(userDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:user-create'), data=jsonData,
			content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(response.status_code, 400)
		self.assertEquals(count, len(User.objects.all()))


class ProfileViewTests(TestCase):
	def __init__(self, *args, **kwargs):
		self.factory = RequestFactory()
		self.user = None
		self.profile = None
		super(ProfileViewTests, self).__init__(*args, **kwargs)

	def setUp(self):
		# Create test user
		self.user = User.objects.create_user(username=username, password='work')
		self.profile = Profile(user=self.user)
		self.user.save()
		self.profile.save()
		self.view = ProfileRestView()

	def testGetSuccess(self):
		'''
			Tests for a successful profile GET request
		'''
		login(self.client)

		response = self.client.get(reverse('chat:api:profile-rest',
			args=(self.user.pk, )), content_type='application/json')
	
		response_user = json.loads(response.content, cls=DateTimeAwareDecoder)

		userForm = ProfileForm(response_user,
			instance=Profile.objects.get(pk=response_user['id']))
		#ensure the data we got is valid
		self.assertEqual(userForm.is_valid(), True)

	def testGetInvalidInput(self):
		'''
			test a profile GET request with invalid primary key
		'''
		login(self.client)

		response = self.client.get(reverse('chat:api:profile-rest',
			args=(invalidPk, )), content_type='application/json')
	
		rdata = json.loads(response.content, cls=DateTimeAwareDecoder)

		self.assertEquals(response.status_code, 404)

	def testGetNotLoggedIn(self):
		'''
			Test to make sure authentication only data is not accessible unless you're
				 authorized
		'''

		# login(self.client)
		response = self.client.get(reverse('chat:api:profile-rest',
			args=(invalidPk, )), content_type='application/json')
		self.assertTrue(response.status_code, 302)

	def testLoggedInGetProfile(self):
		'''
			Logged in, get profile test.
		'''
		login(self.client)

		response = self.client.get(reverse('chat:api:login-test', args=(self.user.pk, )),
			content_type='application/json')
		
		response_user = json.loads(response.content, cls=DateTimeAwareDecoder)
		userForm = ProfileForm(response_user,
			instance=Profile.objects.get(pk=response_user['id']))

		self.assertEqual(userForm.is_valid(), True)

	def testPutSuccess(self):
		'''
			Profile PUT success (although there's not much you can update)
		'''

		#this test doesnt do anything for now but make sure a valid response is sent back
		#	right now the profile class can't really be updated with anything...
		login(self.client, user=self.user, password='work')

		profileDict = model_to_dict(self.profile)
		jsonData = json.dumps(profileDict, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:profile-rest',
			args=(self.user.pk, )), data=jsonData, content_type='application/json')

		self.assertEquals(response.status_code, 200)

		rdata = json.loads(response.content)



	def testPutFailInvalid(self):
		''' Tests if the id of the profile sent matches the id of the actual user tied to
				that profile in the database.  In this case it is not, so it should fail.
		'''
		login(self.client)

		user = User.objects.create_user(username='another_user')
		user.save()
		self.profile.user = user
		profileDict = model_to_dict(self.profile)
		profileDict['user'] = invalidPk
		jsonData = json.dumps(profileDict, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:profile-rest',
			args=(self.user.pk, )), data=jsonData, content_type='application/json')

		self.assertEquals(response.status_code, 404)

	def testPutFailure(self):
		''' Invalid profile id sent, should fail and not touch the profiles.
		'''
		login(self.client)
		user = User.objects.create_user(username='another_user')
		user.save()
		self.profile.user = user
		profileDict = model_to_dict(self.profile)
		profileDict['id'] = profileDict['id'] + 1
		jsonData = json.dumps(profileDict, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:profile-rest', 
		 	args=(self.user.username, ) ), data=jsonData, content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(response.status_code, 404)
		self.assertEquals(Profile.objects.get(pk=self.profile.pk).user.pk, self.user.pk)
		self.assertNotEquals(Profile.objects.get(pk=self.profile.pk).user.pk, user.pk)


class MessageViewTest(TestCase):
	def __init__(self, *args, **kwargs):
		self.factory = RequestFactory()
		self.user = None
		self.conversation = None
		self.msg1 = None
		self.msg2 = None
		super(MessageViewTest, self).__init__(*args, **kwargs)

	def setUp(self):
		# Create test user
		self.user = User.objects.create_user(username=username, password='work')
		self.user.save()
		self.msg1 = Message(sender=self.user, text="heres the first message")
		self.msg1.save()

		self.msg2 = Message(sender=self.user, text="heres the second message")
		self.msg2.save()
		
		self.conversation = Conversation()
		self.conversation.save()
		self.conversation.participants.add(self.user)
		self.conversation.messages.add(self.msg1)
		self.conversation.messages.add(self.msg2)
		self.conversation.save()
		self.view = MessageRestView()
		self.createView = MessageCreateView()

	def testGetSuccess(self):
		'''
			Test successful message get request
		'''

		login(self.client, user=self.user)

		response = self.client.get(reverse('chat:api:message-rest',
			args=(self.conversation.pk, self.msg1.id, )), content_type='application/json')

		response_message = json.loads(response.content, cls=DateTimeAwareDecoder)

		messageForm = MessageForm(response_message,
			instance=Message.objects.get(pk=response_message['id']))

		#ensure the data we got is valid
		self.assertEqual(messageForm.is_valid(), True)

	def testGetFailMsg(self):
		''' Message doesn't belong in convo and User doesnt
		'''
		# message isn't in conversation (but user is)
		login(self.client, user=self.user)
		m = Message(sender=self.user, text='bogusmessage')
		m.save()

		response = self.client.get(reverse('chat:api:message-rest',
			args=(self.conversation.pk, m.pk, )), content_type='application/json')

		self.assertEquals(response.status_code, 404)

		# user isn't in conversation, but message is
		login(self.client, username='newUser', password='work')
		response = self.client.get(reverse('chat:api:message-rest',
			args=(self.conversation.pk, self.msg1.pk, )), content_type='application/json')

		self.assertEquals(response.status_code, 404)		


	def testGetFail(self):
		'''
			trying getting a Message with an invalid id
		'''
		login(self.client)
		response = self.client.get(reverse('chat:api:message-rest',
			args=(self.conversation.pk, 'bogusmessageid', )),
			content_type='application/json')
		self.assertEquals(response.status_code, 404)

		with self.assertRaises(Message.DoesNotExist):
			msg = Message.objects.get(pk='bogusmessageid')

	def testDeleteSuccess(self):
		'''
			test successful deletion of Message
		'''
		login(self.client, user=self.user, password='work')

		self.assertEquals(len(Message.objects.all()), 2)

		response = self.client.delete(reverse('chat:api:message-rest',
			args=(self.conversation.pk, self.msg1.pk, )), content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(len(Message.objects.all()), 1)
		with self.assertRaises(Message.DoesNotExist):
			Message.objects.get(pk=rdata['id'])

	def testDeleteFailure(self):
		'''
			test succesful deletion of a Message			
		'''

		login(self.client, user=self.user, password='work')
		self.assertEquals(len(Message.objects.all()), 2)


		response = self.client.delete(reverse('chat:api:message-rest',
			args=(self.conversation.pk, 'bogusmessageid',)),
			content_type='application/json', cpk=self.conversation.pk, pk='bogusmessageid'
			)

		rdata = json.loads(response.content)
		self.assertEquals(response.status_code, 404)
		self.assertEquals(len(Message.objects.all()), 2)

	def testPut(self):
		'''
			Test that PUT Message requests always return 400	
		'''
		#this should always fail
		user = User.objects.create_user(username='bogusGuru', password='work')
		user.save()
		self.msg1.sender = user

		login(self.client, user=user, password='work')

		messageDict = model_to_dict(self.msg1)
		jsonData = json.dumps(messageDict, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:message-rest', args=(
		 	self.conversation.pk, self.msg1.pk, ) ), data=jsonData,
			content_type='application/json')

		self.assertEquals(response.status_code, 400)

	def testPostSuccess(self):
		'''
			Test a successful Message creation
		'''

		login(self.client, user=self.user, password='work')

		msg = Message(sender=self.user, text='new message')
		msg.id = 'uniqueuniqueunique'
		messageDict = model_to_dict(msg)
		
		count = len(Message.objects.all())
		jsonData = json.dumps(messageDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:message-create',
			args=(self.conversation.pk, )), data=jsonData,
		 	content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(count + 1, len(Message.objects.all()))
		try:
			newMessageObj = Message.objects.get(pk=rdata['id'])
			self.assertTrue(newMessageObj in Conversation.objects.get(
				pk=self.conversation.pk).messages.all())
		except Message.DoesNotExist:
			self.assertTrue(false, "error with message post")
		self.assertTrue(Message.objects.get(pk=rdata['id']).text == msg.text)

	def testPostFailure(self):
		'''
			test unsuccessful Message creation - id already taken
		'''

		login(self.client, user=self.user, password='work')

		msg = Message(sender=self.user, text='new message')
		msg.id = self.msg1.id
		messageDict = model_to_dict(msg)
		
		count = len(Message.objects.all())
		jsonData = json.dumps(messageDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:message-create',
			args=(self.conversation.pk, )), data=jsonData,
		 	content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(response.status_code, 400)
		self.assertEquals(count, len(Message.objects.all()))


class ConversationViewTests(TestCase):
	def __init__(self, *args, **kwargs):
		self.factory = RequestFactory()
		self.user = None
		self.conversation = None
		self.msg1 = None
		self.msg2 = None
		super(self.__class__, self).__init__(*args, **kwargs)

	def setUp(self):
		# Create test user
		self.user = User.objects.create_user(username=username, password='work')
		self.user.save()
		self.msg1 = Message(sender=self.user, text="heres the first message")
		self.msg1.save()

		self.msg2 = Message(sender=self.user, text="heres the second message")
		self.msg2.save()
		
		self.conversation = Conversation()
		self.conversation.save()
		self.conversation.participants.add(self.user)
		self.conversation.messages.add(self.msg1)
		self.conversation.messages.add(self.msg2)
		self.conversation.save()
		self.view = ConversationRestView()
		self.createView = ConversationCreateView()

	def testGetSuccess(self):
		'''
			test successful conversation GET request.  The server should return a special
				dictionary formated as follows.

				[{"id" : "alphanumericrandomid", "text" : "message text..."}, {...}, ...]
		'''

		login(self.client, user=self.user, password='work')

		self.conversation.participants.add(self.user)
		self.conversation.save()

		response = self.client.get(reverse('chat:api:conversation-rest',
			args=(self.conversation.id, )), content_type='application/json')

		msgs = json.loads(response.content, cls=DateTimeAwareDecoder)

		dbmsgs = Conversation.objects.get(pk=self.conversation.id).messages.all()

		self.assertEquals(len(msgs), len(dbmsgs))

		for msg in msgs:
			foundIt = False
			for dbmsg in dbmsgs:
				if msg['id'] == dbmsg.id:
					if msg['text'] is dbmsg.text:
						foundIt = True
						break
			self.assertFalse(foundIt, "%s not found in %s" % (msg, str(dbmsgs)))

	def testPostSuccess(self):
		'''
			test successful Conversation creation
		'''
		login(self.client)

		convo = Conversation()
		conversationDict = model_to_dict(convo)
		count = len(Conversation.objects.all())
		jsonData = json.dumps(conversationDict, cls=DateTimeAwareEncoder)

		response = self.client.post(reverse('chat:api:conversation-create'),
			data=jsonData, content_type='application/json')

		rdata = json.loads(response.content)

		self.assertEquals(count + 1, len(Conversation.objects.all()))
		try:
			newConvoObj = Conversation.objects.get(pk=rdata['id'])
		except Conversation.DoesNotExist:
			self.assertTrue(false, "error with message post")

	def testPut(self):
		'''
			Test that conversation PUT (update) requests fail
		'''
		login(self.client)
		#this should always fail
		convo = Conversation()
		convo.save()
		convo.participants.add(self.user)
		
		convoDict = model_to_dict(convo)
		jsonData = json.dumps(convoDict, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:conversation-rest', args=(
			str(convo.pk), ) ), data=jsonData, content_type='application/json')

		self.assertTrue(response.status_code == 400)

	def testDeleteFail(self):
		''' This tests a user trying to delete a conversation they don't belong to.
				Should 404
		'''
		login(self.client)
		response = self.client.delete(reverse('chat:api:conversation-rest',
			args=(self.conversation.id, ) ), content_type='application/json')

		self.assertEquals(response.status_code, 404)

	def testDeleteSuccess(self):
		''' This tests a user trying to delete a conversation they belong to.
				Should 200
		'''
		user = User.objects.create_user(username='user1', password='work')
		user.save()

		self.conversation.participants.add(user)
		self.conversation.save()

		count = len(Conversation.objects.all())

		login(self.client, user=user)
		response = self.client.delete(reverse('chat:api:conversation-rest',
			args=(self.conversation.id, ) ), content_type='application/json')
		rdata = json.loads(response.content)


		self.assertEquals(count - 1, len(Conversation.objects.all()))
		self.assertEquals(response.status_code, 200)

class TestFormValidation(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(username='formtester', password='work')
		self.user.save()
		self.data = {}
		self.jsonData = json.dumps(self.data)

	def testRegisterForm(self):
		'''
			Test that UserCreationForm is working properly
		'''
		response = self.client.post(reverse('chat:api:user-create'), data=self.jsonData,
			content_type='application/json')
		rdata = json.loads(response.content)
		errors = rdata['error']
		for key, value in errors.iteritems():
			self.assertTrue(value[0] == 'This field is required.')

	def testMessageForm(self):
		'''
			Test that MessageForm is working properly
		'''
		login(self.client, user=self.user)
		convo = Conversation()
		convo.save()
		msg = Message(sender=self.user, text='some msg text')
		msg.save()
		convo.participants.add(self.user)
		convo.messages.add(msg)
		convo.save()

		response = self.client.post(reverse('chat:api:message-create',
			args=(convo.pk, )), data=self.jsonData,
		 	content_type='application/json')

		rdata = json.loads(response.content)
		errors = rdata['error']
		for key, value in errors.iteritems():
			self.assertTrue(value[0] == 'This field is required.')

	def testConversationForm(self):
		'''
			Test that ConversationForm is working properly.
		'''

		login(self.client, user=self.user)

		message = Message(sender=self.user, text='asdf')
		message.save()
		conversation = Conversation()
		conversation.save()
		conversation.participants.add(self.user)
		conversation.messages.add(message)
		conversation.save()

		self.data['messages'] = [message.pk]
		self.jsonData = json.dumps(self.data)

		response = self.client.post(reverse('chat:api:conversation-create'),
			data=self.jsonData, content_type='application/json')


		rdata = json.loads(response.content)
		errors = rdata['error']
		for key, value in errors.iteritems():
			self.assertTrue(value[0] == 'This field is required.' or \
				value[0] == 'New conversations cant have old messages.', value[0])


	def testProfileForm(self):
		'''
			Test that ProfileForm is working properly.
		'''

		login(self.client, user=self.user)
		profile = Profile(user=self.user)
		profile.save()

		self.data['user'] = self.user.pk
		self.data['id'] = self.user.pk
		self.jsonData = json.dumps(self.data, cls=DateTimeAwareEncoder)

		response = self.client.put(reverse('chat:api:profile-rest',
			args=(self.user.pk, )), data=self.jsonData, content_type='application/json')


		rdata = json.loads(response.content)
		self.assertTrue(response.status_code == 200)


	def testUserForm(self):
		'''
			Test that User PUT / update requests are working properly.
		'''
		login(self.client, user=self.user)

		response = self.client.put(
			reverse('chat:api:user-rest',
			args=(self.user.pk, ) ),
			data=self.jsonData,
			content_type='application/json')

		rdata = json.loads(response.content)
		errors = rdata['error']
		for key, value in errors.iteritems():
			self.assertTrue(value[0] == 'This field is required.')