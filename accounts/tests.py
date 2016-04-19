from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from lib.test_utils import ClientTest


class AddUserTest(ClientTest):
    fixtures = ['test_users.yaml']

    def test_load_page_anonymous(self):
        """Load page while logged out -> login page."""
        response = self.client.get(reverse('signup'))
        self.assertRedirects(
            response,
            reverse('signin')+'?next='+reverse('signup'),
        )

    def test_load_page_normal_user(self):
        """Load page as normal user -> sorry, don't have permission."""
        self.client.login(username='user2', password='secret')
        response = self.client.get(reverse('signup'))
        self.assertStatusOK(response)
        self.assertTemplateUsed(response, self.PERMISSION_DENIED_TEMPLATE)

    def test_load_page_superuser(self):
        """Load page as superuser -> page loads normally."""
        self.client.login(username='superuser_user', password='secret')
        response = self.client.get(reverse('signup'))
        self.assertStatusOK(response)

    # TODO: Add tests that submit the Add User form with errors.
    # TODO: Add a test to check that a new, unactivated user can't login yet.

    def test_add_user_success(self):
        """
        Submit the Add User form correctly, follow the activation email's
        link, and check that the new user was added correctly.
        """
        self.client.login(username='superuser_user', password='secret')

        # Submit the add user form.
        new_user_username = 'alice'
        new_user_email = 'alice123@example.com'
        response = self.client.post(reverse('signup'), dict(
            username=new_user_username,
            email=new_user_email,
        ))

        # Check that an activation email was sent.
        self.assertEqual(len(mail.outbox), 1)
        # Check that the user was redirected to the add-user-complete page.
        # (Yes, the reverse() name is still userena_signup_complete...)
        self.assertRedirects(response, reverse(
            'userena_signup_complete',
            kwargs={'username': new_user_username},
        ))

        # Check the activation email.
        activation_email = mail.outbox[0]
        # Check that the intended recipient is the only recipient.
        self.assertEqual(len(activation_email.to), 1)
        self.assertEqual(activation_email.to[0], new_user_email)
        # The requested username should be somewhere in the email body.
        self.assertTrue(new_user_username in activation_email.body)

        # From the email, get the new user's password and activation link.
        # Password: should be preceded with the words "password is:".
        # (Feels hackish to search this way though...)
        # Activation link: should be the only link in the email, i.e.
        # the only "word" with '://' in it.
        activation_link = None
        new_user_password = None
        prev_word = None
        prev_prev_word = None
        for word in activation_email.body.split():
            if prev_prev_word == 'password' and prev_word == 'is:':
                new_user_password = word
            if '://' in word:
                activation_link = word
            prev_prev_word = prev_word
            prev_word = word
        self.assertIsNotNone(new_user_password)
        self.assertIsNotNone(activation_link)

        # Activation link should redirect to the profile detail page...
        response = self.client.get(activation_link)
        self.assertRedirects(response, reverse('userena_profile_detail', kwargs={'username': new_user_username}))
        # ...and should log us in as the new user.
        response = self.client.get(activation_link, follow=True)
        self.assertEqual(response.context['user'].username, new_user_username)

        # Check various permissions.
        self.assertFalse(response.context['user'].is_superuser)
        # Should be able to access own account or profile functions, but not
        # others' account or profile functions.
        for url_name in ['userena_email_change',
                         'userena_password_change',
                         'userena_profile_edit',
                         ]:
            response = self.client.get(reverse(url_name, kwargs={'username': new_user_username}))
            self.assertStatusOK(response)
            self.assertTemplateNotUsed(response, self.PERMISSION_DENIED_TEMPLATE)
            response = self.client.get(reverse(url_name, kwargs={'username': 'superuser_user'}))
            self.assertEqual(response.status_code, 403)

        # Can we log out and then log back in as the new user?
        self.client.logout()
        self.assertTrue(self.client.login(
            username=new_user_username,
            password=new_user_password,
        ))

class SigninTest(ClientTest):
    fixtures = ['test_users.yaml']

    def test_signin_page(self):
        """Go to the signin page while logged out."""
        response = self.client.get(reverse('signin'))
        self.assertStatusOK(response)

    # TODO: Add tests that submit the signin form with errors.

    def signin_success(self, identification_method, remember_me):
        """
        Submit the Signin form correctly, then check that we're signed in.
        """
        # Determine the info we'll use to sign in.
        if identification_method == 'username':
            identification = 'user2'
            user = User.objects.get(username=identification)
        elif identification_method == 'email':
            identification = 'user2@example.com'
            user = User.objects.get(email=identification)
        else:
            raise ValueError('Invalid identification method.')

        # Sign in using the signin form.
        # TODO: Test for cookies when remember_me=True?
        response = self.client.post(reverse('signin'), follow=True, data=dict(
            identification=identification,
            password='secret',
            remember_me=remember_me,
        ))
        # Check that it redirects to the source_about page (assumes the user has no sources).
        # TODO: Test when the user has at least one source (should go to source list)
        self.assertRedirects(response, reverse('source_about'))

        # Check that we're signed in as the correct user.
        # From http://stackoverflow.com/a/6013115
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        # Log out to prepare for a possible next test run of this function
        # with different parameters.
        self.client.logout()

    def test_signin_success(self):
        self.signin_success(identification_method='username', remember_me=True)
        self.signin_success(identification_method='username', remember_me=False)
        self.signin_success(identification_method='email', remember_me=True)
        self.signin_success(identification_method='email', remember_me=False)


class EmailAllTest(ClientTest):
    fixtures = ['test_users.yaml']

    def test_load_page_anonymous(self):
        """Load page while logged out -> login page."""
        response = self.client.get(reverse('emailall'))
        self.assertRedirects(
            response,
            reverse('signin')+'?next='+reverse('emailall'),
        )

    def test_load_page_normal_user(self):
        """Load page as normal user -> sorry, don't have permission."""
        self.client.login(username='user2', password='secret')
        response = self.client.get(reverse('emailall'))
        self.assertStatusOK(response)
        self.assertTemplateUsed(response, self.PERMISSION_DENIED_TEMPLATE)

    def test_load_page_superuser(self):
        """Load page as superuser -> page loads normally."""
        self.client.login(username='superuser_user', password='secret')
        response = self.client.get(reverse('emailall'))
        self.assertStatusOK(response)
        self.assertTemplateUsed(response, 'accounts/email_all_form.html')

    def test_submit(self):
        """Test submitting the form."""
        self.client.login(username='superuser_user', password='secret')
        response = self.client.post(reverse('emailall'), data=dict(
            subject="Subject goes here",
            message="Message\ngoes here.",
        ))
        self.assertStatusOK(response)

        # Check that an email was sent.
        self.assertEqual(len(mail.outbox), 1)
        # Check that the email has the expected number of recipients:
        # the number of users with an email address.
        # (Special users like 'robot' don't have emails.)
        num_of_users = User.objects.all().exclude(email='').count()
        self.assertEqual(len(mail.outbox[0].bcc), num_of_users)

        # TODO: Check the emails in more detail: subject, message, and
        # possibly checking at least some of the bcc addresses.
