from django.contrib import admin

# Register your models here.
from .models import PMKBVariant
from .models import PMKBInterpretation

admin.site.register(PMKBVariant)
admin.site.register(PMKBInterpretation)
