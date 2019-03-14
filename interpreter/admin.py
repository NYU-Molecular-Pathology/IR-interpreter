from django.contrib import admin

# Register your models here.
from .models import PMKBVariant
from .models import PMKBInterpretation
from .models import UserAccessMetric
from .models import UserUploadMetric
from .models import NYUInterpretation
from .models import NYUTier

admin.site.register(PMKBVariant)
admin.site.register(PMKBInterpretation)
admin.site.register(UserAccessMetric)
admin.site.register(UserUploadMetric)
admin.site.register(NYUInterpretation)
admin.site.register(NYUTier)
