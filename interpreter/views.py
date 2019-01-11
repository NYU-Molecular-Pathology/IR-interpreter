from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
import datetime
from  .ir import IRTable, IRRecord
from .interpret import interpret_pmkb

def index(request):
    return render(request, 'interpreter/index.html', {})

def demo(request):
    template = 'report.html'
    report_template = get_template(template)
    ir_tsv = "example-data/SeraSeq.tsv"
    ir_table = IRTable(ir_tsv)
    ir_table = interpret_pmkb(ir_table = ir_table)
    report_html = report_template.render({'IRtable': ir_table})
    return HttpResponse(report_html)
