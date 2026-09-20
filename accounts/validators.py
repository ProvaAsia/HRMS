import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว (A–Z)'),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _('รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว')


class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _('รหัสผ่านต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว (a–z)'),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _('รหัสผ่านต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว')


class SpecialCharValidator:
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/`~]', password):
            raise ValidationError(
                _('รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว เช่น !@#$%^&*'),
                code='password_no_special',
            )

    def get_help_text(self):
        return _('รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว')
