from django.http import HttpResponse
from django.shortcuts import render
from .models import PMKBVariant
from .report import make_report_html
import subprocess
import logging

# logger = logging.getLogger(__name__)
logger = logging.getLogger()

# try to get the app version from the git repo
version = None
try:
    version = subprocess.check_output(['git', 'describe', '--always']).decode('ascii').strip()
except:
    pass

MAX_UPLOAD_SIZE = 2 * 1024 * 1024 # 2MB

def index(request):
    """
    Returns the home page index
    """
    logger.info("index requested")
    # get all the available tumor and tissue types to populate the uploads form
    all_tumor_types = sorted(PMKBVariant.objects.values_list('tumor_type', flat=True).distinct())
    all_tissue_types = sorted(PMKBVariant.objects.values_list('tissue_type', flat=True).distinct())
    template = "interpreter/index.html"
    context = {'version': version, 'tumor_types': all_tumor_types, 'tissue_types': all_tissue_types}
    return render(request, template, context)

def upload(request):
    """
    Responds to a POST request from an uploaded Ion Reporter .tsv file
    """
    if request.method == 'POST' and 'irtable' in request.FILES:
        logger.info("POST requested")
        # check for a tumor or tissue type passed
        tissue_type = request.POST.get('tissue_type', None)
        if tissue_type == 'None':
            tissue_type = None
        tumor_type = request.POST.get('tumor_type', None)
        if tumor_type == 'None':
            tumor_type = None

        # check for file too large
        logger.info("checking file size")
        if request.FILES['irtable'].size > MAX_UPLOAD_SIZE:
            logger.error("file size too large; {0:.2f}MB".format(request.FILES['irtable'].size / (1024 * 1024)))
            return HttpResponse('Error: File is too large, size limit is: {0}MB'.format(MAX_UPLOAD_SIZE / (1024 * 1024)) )
        # check file type
        logger.info("checking file type")
        if not str(request.FILES['irtable']).endswith('.tsv'):
            logger.error("Invalid file type")
            return HttpResponse('Error: Invalid file type, filename must end with ".tsv"')

        # try to generate the HTML report
        try:
            logger.info("generating report HTML")
            report = make_report_html(input = request.FILES['irtable'],
                tissue_type = tissue_type,
                tumor_type = tumor_type)
            return HttpResponse(report)
        except:
            logger.error("an error occured while generating report HTML")
            return HttpResponse('Error: File could not be parsed')
    else:
        return HttpResponse('Error: Invalid file selected')
