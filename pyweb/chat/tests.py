import uuid
import datetime
import posixpath
from django.utils import timezone
from django.db import models, IntegrityError
from django.test import TestCase
from django.contrib.auth.models import User, UserManager
from django.test.client import Client
from chat.models import ChatUserProfile, Message, Conversation


class UserViewTests(TestCase):
	
	def testGet(self):
		user = User.objects.create_user(username="guru")
		user.save()
		c = Client()
		url_components = ['/chat/usr', str(user.pk)]
		response = posixpath.join(*url_components)
		print dir(response)


# # Test cases for Message model
# class MessageTests(TestCase):
# 	def testUniqueness(self):
# 		''' Test to ensure an IntegrityError is raised when message_id is NOT unique
# 		'''
# 		user = User.objects.create_user(username="Cam")
# 		user.save()
# 		convo = Conversation()
# 		convo.save()
# 		msg = Message(sender=user, text="some text msg1", message_id='abc123')
# 		msg1 = Message(sender=user, text="some text msg2", message_id='abc123')
# 		msg.save()
# 		print ' '.join([str(msg.message_id), str(msg1.message_id)])
# 		with self.assertRaises(IntegrityError):
# 			msg1.save()
# 		# msg1.save()

# ##########all tests below here are just for Cam's learning for now.  They don't test any
# #	real functionality of anything other than django itself.

# # Test cases for Conversation model
# class ConversationTests(TestCase):
# 	''' basic testing of conversation modal
# 	'''
# 	# Test Conversation creation
# 	def testCreateConversation(self):
# 		convo = Conversation()
# 		convo.save()
# 		self.assertEquals(len(Conversation.objects.all()), 1)

# 	# Test adding/removing of participants
# 	def testAddRemoveParticipants(self):
# 		user = User.objects.create_user(username="Cam")
# 		user.save()
# 		convo = Conversation()
# 		convo.save()
# 		convo.participants.add(user)
# 		users = []
# 		convo.save()
# 		for x in range(0, 29):
# 			users.append(User.objects.create_user(username="test" + str(x)))
# 			users[x].save()
# 		convo.participants.add(*users)
# 		convo.save()
# 		self.assertEqual(len(convo.participants.all()), len(Conversation.objects.get(
# 			pk=convo.pk).participants.all()))

# 		before = len(convo.participants.all())
# 		convo.participants.remove(users[0])
# 		convo.save()
# 		self.assertEqual(before-1, len(convo.participants.all()))
# 		convo.participants.remove(*users[1:])
# 		self.assertEqual(1, len(convo.participants.all()))
# 		self.assertEqual("Cam", convo.participants.all()[0].username)

# 	def testAddRemoveMessages(self):
# 		users = []
# 		msgs = []
# 		for x in range(0, 99):
# 			users.append(User.objects.create_user(username="test" + str(x)))
# 			users[x].save()
# 			msgs.append(Message(sender=users[x], text="some text " + str(x)))
# 			msgs[x].save()
		
# 		self.assertEqual(len(msgs), 99)

# 		convo = Conversation()
# 		convo.save()
# 		convo.participants.add(*users)
# 		convo.messages.add(*msgs)
# 		convo.save()

# 		print 'HERE: '
# 		print convo.messages.all()

# 		self.assertEqual(len(convo.messages.all()), 99)
# 		self.assertEqual(len(convo.participants.all()), 99)
# 		self.assertEqual(convo.messages.get(message_id=msgs[0].message_id).text,
# 			"some text 0")
# 		self.assertEqual(convo.messages.get(message_id=msgs[98].message_id).text,
# 			"some text 98")
# 		self.assertEqual(convo.messages.get(message_id=msgs[33].message_id).text,
# 			"some text 33")
# 		self.assertEqual(convo.participants.get(pk=users[0].pk).username, "test0")
# 		self.assertEqual(convo.messages.get(message_id=msgs[0].message_id).
# 			sender.username, "test0")

