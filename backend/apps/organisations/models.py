from shared.models import BaseModel
from django.db import models
from apps.tenants.models import Client

class Organisation(BaseModel):
    tenant = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='organisation')
    name = models.CharField(max_length=255)
    org_type = models.CharField(
        max_length=20,
        choices=[('company', 'Company'), ('agency', 'Agency')],
        default='company'
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    cin = models.CharField(max_length=50, blank=True)  # Company Identification Number
    gst_number = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    employee_count = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('1-10', '1-10'), ('11-50', '11-50'), ('51-200', '51-200'),
            ('201-500', '201-500'), ('501-1000', '501-1000'), ('1000+', '1000+')
        ]
    )
    description = models.TextField(blank=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'organisations_organisation'


class Department(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    head_user_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'organisations_department'


class Location(BaseModel):
    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    is_headquarters = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}, {self.city}"

    class Meta:
        db_table = 'organisations_location'
