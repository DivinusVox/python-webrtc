import uuid, json, logging, datetime

from django.shortcuts import render, render_to_response

from django.core import serializers

from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

from django.views.generic import View
from django.template import Context, loader, RequestContext

from django.contrib.auth.models import User
from django.forms.models import model_to_dict

from .util import DateTimeAwareEncoder, DateTimeAwareDecoder

from .models import Profile, Message, Conversation
from .forms import (UserForm, ProfileForm, MessageForm, ConversationForm,
	UserCreateForm, ProfileCreateForm, MessageCreateForm, ConversationCreateForm)

logger = logging.getLogger(__name__)

API_SUCCESS = 'success'
API_FAIL = 'fail'
API_ERROR = 'error'
API_RESULT = 'result'

API_INVALID_DATA = "invalid data: (%s) - errors:(%s)"
API_BAD_PK = "id %s does not exist (%s)"

class BaseView(View):
	def invalidRequest(self):
		response = {}
		try:
			raise Exception
		except Exception as e:
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = str(e)
			return HttpResponseBadRequest(response)

class CreateView(BaseView):
	def get(self, request, *args, **kwargs):
		return self.invalidRequest()

	def put(self, request, *args, **kwargs):
		return self.invalidRequest()

	def delete(self, request, *args, **kwargs):
		return self.invalidRequest()

	def post(self, request, *args, **kwargs):
		rdata = json.loads(request.body, cls=DateTimeAwareDecoder)
		response = {}
		try:
			objForm = self.form(rdata)
			if not objForm.is_valid():
				response[API_RESULT] = API_FAIL
				response[API_ERROR] = API_INVALID_DATA % (str(rdata), objForm.errors)
			else:
				obj = objForm.save()
				response['id'] = obj.pk
				response[API_RESULT] = API_SUCCESS
				return HttpResponse(json.dumps(response))

		except self.model.DoesNotExist:
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], self.model.__name__)
		return HttpResponseBadRequest(json.dumps(response))


class RestView(BaseView):
	''' Abstract class for RestView's.  Make sure each of the following are declared
		within child class.  RestView will take care of get, put, and delete.  You 
		must pass the primary key as a kwarg with self.pkString as the key to identify
		it.
		self.model - Points to the Django model class
		self.form - points to the Django FormModel for the self.model class
		self.pkString - The primary key 'key' that will be passed through kwargs
	'''
	def get(self, request, *args, **kwargs):
		try:
			obj = self.model.objects.get(pk=kwargs['pk'])
			return HttpResponse(json.dumps(model_to_dict(obj), cls=DateTimeAwareEncoder),
				content_type='application/json')
		except self.model.DoesNotExist:
			response = {}
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], self.model.__name__)
			return HttpResponseBadRequest(json.dumps(response))

	def put(self, request, *args, **kwargs):
		rdata = json.loads(request.body, cls=DateTimeAwareDecoder)
		response = {}
		try:
			dbObj = self.model.objects.get(pk=kwargs['pk'])

			objForm = self.form(rdata, instance=dbObj)

			if not objForm.is_valid():
				response[API_RESULT] = API_FAIL
				response[API_ERROR] = API_INVALID_DATA % str(rdata)
			else:
				objForm.save()
				response['id'] = objForm.data['id']
				response[API_RESULT] = API_SUCCESS
				return HttpResponse(json.dumps(response))

		except self.model.DoesNotExist:
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], self.model.__name__)
		return HttpResponseBadRequest(json.dumps(response))

	def delete(self, request, *args, **kwargs):
		response = {}
		try:
			dbObj = self.model.objects.get(pk=kwargs['pk'])
			dbObj.delete()
			response['id'] = kwargs['pk']
			response[API_RESULT] = API_SUCCESS
		except self.model.DoesNotExist:
			response = {}
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], self.model.__name__)
			return HttpResponseBadRequest(json.dumps(response))
		return HttpResponse(json.dumps(response))

	def post(self, request, *args, **kwargs):
		return self.invalidRequest()

class UserRestView(RestView):
	def __init__(self, *args, **kwargs):
		self.model = User
		self.form = UserForm
		super(self.__class__, self).__init__(*args, **kwargs)

class UserCreateView(CreateView):
	def __init__(self, *args, **kwargs):
		self.model = User
		self.form = UserCreateForm
		super(self.__class__, self).__init__(*args, **kwargs)

class ProfileRestView(View):

	def get(self, request, *args, **kwargs):
		try:
			obj = Profile.objects.get(user=kwargs['pk'])
			return HttpResponse(json.dumps(model_to_dict(obj), cls=DateTimeAwareEncoder),
				content_type='application/json')
		except Profile.DoesNotExist:
			response = {}
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], Profile.__name__)
			return HttpResponseBadRequest(json.dumps(response))

	def put(self, request, *args, **kwargs):
		rdata = json.loads(request.body, cls=DateTimeAwareDecoder)
		response = {}
		try:
			dbObj = Profile.objects.get(user=kwargs['pk'])

			objForm = ProfileForm(rdata, instance=dbObj)

			if not objForm.is_valid():
				response[API_RESULT] = API_FAIL
				response[API_ERROR] = API_INVALID_DATA % str(rdata)
			else:
				objForm.save()
				response['id'] = objForm.data['id']
				response[API_RESULT] = API_SUCCESS
				return HttpResponse(json.dumps(response))

		except Profile.DoesNotExist:
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], Profile.__name__)
		return HttpResponseBadRequest(json.dumps(response))

	def delete(self, request, *args, **kwargs):
		response = {}
		try:
			dbObj = Profile.objects.get(user=kwargs['pk'])
			dbObj.delete()
			response['id'] = kwargs['pk']
			response[API_RESULT] = API_SUCCESS
		except Profile.DoesNotExist:
			response = {}
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], Profile.__name__)
			return HttpResponseBadRequest(json.dumps(response))
		return HttpResponse(json.dumps(response))

	def post(self, request, *args, **kwargs):
		return self.invalidRequest()

class ProfileCreateView(CreateView):
	def __init__(self, *args, **kwargs):
		self.model = Profile
		self.form = ProfileCreateForm
		super(self.__class__, self).__init__(*args, **kwargs)

class ConversationRestView(RestView):
	def __init__(self, *args, **kwargs):
		self.model = Conversation
		self.form = ConversationForm
		super(self.__class__, self).__init__(*args, **kwargs)

	def get(self, *args, **kwargs):
		try:
			#TODO:  is there a more efficient way to do this db query and build response?			
			obj = self.model.objects.get(pk=kwargs['pk'])
			msgs = list(obj.messages.all())
			response = []
			for msg in msgs:
				response.append({'id' : msg.pk, 'text' : msg.text})
			return HttpResponse(json.dumps(response, cls=DateTimeAwareEncoder),
				content_type='application/json')
		except self.model.DoesNotExist:
			response = {}
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = API_BAD_PK % (kwargs['pk'], self.model.__name__)
			return HttpResponseBadRequest(json.dumps(response))

	def delete(self, request, *args, **kwargs):
		return self.invalidRequest()

class ConversationCreateView(CreateView):
	def __init__(self, *args, **kwargs):
		self.model = Conversation
		self.form = ConversationCreateForm
		super(self.__class__, self).__init__(*args, **kwargs)

class MessageRestView(RestView):
	def __init__(self, *args, **kwargs):
		self.model = Message
		self.form = MessageForm
		super(self.__class__, self).__init__(*args, **kwargs)

	def put(self, request, *args, **kwargs):
		return self.invalidRequest()

class MessageCreateView(CreateView):
	def __init__(self, *args, **kwargs):
		self.model = Message
		self.form = MessageForm
		super(self.__class__, self).__init__(*args, **kwargs)

	def post(self, request, *args, **kwargs):
		rdata = json.loads(request.body, cls=DateTimeAwareDecoder)
		response = {}
		try:
			msgForm = self.form(rdata)
			conversation = Conversation.objects.get(pk=kwargs['cpk'])
			if not msgForm.is_valid():
				response[API_RESULT] = API_FAIL
				response[API_ERROR] = API_INVALID_DATA % (str(rdata), msgForm.errors)
			else:
				obj = msgForm.save()
				conversation.messages.add(obj)
				conversation.save()
				response['id'] = obj.pk
				response[API_RESULT] = API_SUCCESS
				return HttpResponse(json.dumps(response))

		except self.model.DoesNotExist:
			response[API_RESULT] = API_FAIL
			response[API_ERROR] = ' - '.join([API_BAD_PK % (kwargs['pk'],
				self.model.__name__), (API_BAD_PK % (kwargs['cpk']))])
		return HttpResponseBadRequest(json.dumps(response))

def application_index(request):
	return render_to_response('index.html', {
			'title' : 'Guru Labs Chat Demo Application',
		}, context_instance=RequestContext(request))