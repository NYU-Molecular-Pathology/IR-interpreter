from django.contrib import admin

# Register your models here.
from .models import PMKBVariant
from .models import PMKBInterpretation
from .models import UserAccessMetric
from .models import UserUploadMetric

admin.site.register(PMKBVariant)
admin.site.register(PMKBInterpretation)
admin.site.register(UserAccessMetric)
admin.site.register(UserUploadMetric)
