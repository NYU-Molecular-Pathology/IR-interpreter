from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView
from .models import PMKBVariant
from .report import make_report_html
import subprocess

# get all the available tumor and tissue types to populate the uploads form
all_tumor_types = sorted(PMKBVariant.objects.values_list('tumor_type', flat=True).distinct())
all_tissue_types = sorted(PMKBVariant.objects.values_list('tissue_type', flat=True).distinct())

# try to get the app version from the git repo
version = None
try:
    version = subprocess.check_output(['git', 'describe', '--always']).decode('ascii').strip()
except:
    pass


def index(request):
    template = "interpreter/index.html"
    context = {'version': version, 'tumor_types': all_tumor_types, 'tissue_types': all_tissue_types}
    return render(request, template, context)

def upload(request):
    if request.method == 'POST' and 'irtable' in request.FILES:
        tissue_type = request.POST.get('tissue_type', None)
        if tissue_type == 'None':
            tissue_type = None
        tumor_type = request.POST.get('tumor_type', None)
        if tumor_type == 'None':
            tumor_type = None
        try:
            report = make_report_html(input = request.FILES['irtable'],
                tissue_type = tissue_type,
                tumor_type = tumor_type)
            return HttpResponse(report)
        except:
            return HttpResponse('Error: File could not be parsed')
    else:
        return HttpResponse('Invalid file selected')
