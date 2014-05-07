// FrontPage Manager View
var WebsocketMessenger = WebsocketMessenger || {
	Models: {},
	Collections: {},
	Views: {},
}

WebsocketMessenger.Views.FrontPageView = WebsocketMessenger.Views.BaseView.extend({
	// 	Backbone.js view used to manage the front page of the application

	// 	@signal 'user:form:create:retrieved' args=(request data):
	//		Signal fired after the view has successfully retrieved an HTML 
	// 		form that can be used to create user accounts for the site.
	//	@signal 'user:form:create:init' args=(user model, create user form view):
	//		Signal fired after a create user form has been initialized.
	//		The user model and view are passed as input arguments for the signal.

	url_form_createuser: undefined,
	$modalcontent: undefined,
	
	tmpl_notification: undefined,
	tmpl_formerrors: undefined,

	form_errors_selectorstring: 'small.error',
	
	user_msg_accountcreated: "User account created successfully, you can now log in to the site",

	initialize: function(options) {
		options = options || {};
		
		// Set view default options
		_.defaults(options, { 
			'user_msg_accountcreated' : this.user_msg_accountcreated, 
			'form_errors_selectorstring' : this.form_errors_selectorstring,
		});
		this.form_errors_selectorstring = options.form_errors_selectorstring;
		this.user_msg_accountcreated = options.user_msg_accountcreated;
		this.url_form_createuser = options.url_form_createuser;
		this.$modalcontent = options.modalcontent;
		
		// View HTML microtemplates
		this.tmpl_notification = options.tmpl_notification;
		this.tmpl_formerrors = options.tmpl_formerrors;
		
		// Set internal view signals/handlers
		this.listenTo(this, 'user:form:create:retrieved', this.initCreateUserForm.bind(this));
	},

	events: {
		'click #btn-create-account' : 'getCreateUserForm',
	},

	checkModalContentElement: function() {
		if (_.isUndefined(this.$modalcontent))
			throw new Error(
				'Please provide a reference to the element which should be used '
				+ 'for modal content');
	},

	getCreateUserForm: function() {
		// 	Retrieve the create user form from the web server
		// 	This method provides an example of how a Backbone view can wrap
		// 	a JavaScript asset and make it easier to work with. Simple callbacks
		// 	can be provided which trigger view signals, allowing other internal 
		// 	view methods to respond as well as external listeners that may be 
		// 	interested in responding to events (such as if the view fails to
		// 	retrieve the form).
		var mview = this;
		if (_.isUndefined(this.url_form_createuser))
			throw new Error('No URL for retrieving the create-user form was provided');
		this.checkModalContentElement();
		this.$modalcontent.foundation('reveal', 'open', {
			url: mview.url_form_createuser,
			success: function(data) {
				mview.$modalcontent.one("opened", function(){
					mview.trigger('user:form:create:retrieved', data);
				});
			},
			error: function() {
				var emessage = 'Unable to retrieve create user form';
				if (_.isFunction(mview.tmpl_notification)) {
					emessage = mview.tmpl_notification({ msg : emessage });
				}
				mview.errorMessage(emessage);
			}, 
		});
	}, 

	initCreateUserForm: function(rdata) {
		// Initialize the user form retrieved by the view
		var mview = this;
		
		this.checkModalContentElement();

		// Form UI references
		var $apiref = this.$modalcontent.find('api');

		// Create a user model and view for collecting the user details
		var umodel = new WebsocketMessenger.Models.BaseModel({}, {
			createurl: $apiref.attr('href-create'),
			updateurl: $apiref.attr('href-update'),
		});
		var uview = new WebsocketMessenger.Views.FormView({
			el: this.$modalcontent.find('.formcontent'),
			model: umodel,
			form_fieldnames: WebsocketMessenger.form_fieldnames(this.$modalcontent),
		});
		
		// Add event handlers for form submission events
		uview.listenTo(uview, 'form:submit:cancel', function(){ // Close form
			mview.$modalcontent.foundation('reveal', 'close');
		});
		
		// Destroy the user model after the dialog is closed
		mview.$modalcontent.one('closed', function(){ umodel.trigger('destroy'); });
		
		// Remove form elements and events after model is destroyed
		uview.listenTo(umodel, 'destroy', uview.removeView.bind(uview));
		
		// Remove form errors
		uview.listenTo(uview, 'form:submit', function(){
			WebsocketMessenger.remove_form_errors(uview, mview.form_errors_selectorstring);
		});

		// Display form errors
		uview.listenTo(uview, 'form:submit:errors', function(ferrors) {
			WebsocketMessenger.display_form_errors(uview, ferrors, mview.tmpl_formerrors);
		});
		
		// Close form dialog after user created successfully
		uview.listenTo(uview, 'form:submit:success', function(){
			mview.$modalcontent.foundation('reveal', 'close');
			mview.userMessage(mview.user_msg_accountcreated);
		});

		mview.trigger('user:form:create:init', umodel, uview);
	}

});

$(document).ready(function(){
	
	// Initialize foundation and plugins
	$(document).foundation();

	// Retrieve page api reference
	var $apiref = $('api');
	var $modalref = $('#modal-content');

	// Compile HTML Templates for the Page
	var tmpl_notification = _.template($('#template-notification').html());
	var tmpl_formerror = _.template($('#template-formerror').html());
	
	// Create a page view
	var fpview = new WebsocketMessenger.Views.FrontPageView({
		el: $('body'),
		url_form_createuser: $apiref.attr('user-create'),
		tmpl_notification: tmpl_notification,
		tmpl_formerrors: tmpl_formerror,
		modalcontent: $modalref,
	});
});