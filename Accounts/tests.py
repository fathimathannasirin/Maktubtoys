from django.test import TestCase

from .forms import RegistrationForm, UserForm


class PhoneValidationTests(TestCase):
    def test_registration_accepts_local_eight_digit_phone(self):
        form = RegistrationForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '12345678',
            'email': 'test@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone_number'], '+97412345678')

    def test_profile_edit_rejects_non_eight_digit_phone(self):
        form = UserForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '12345',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)
