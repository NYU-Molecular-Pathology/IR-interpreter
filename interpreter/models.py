from django.db import models

class PMKBVariant(models.Model):
    """
    Details about an individual variant registered in the PMKB
    """
    gene = models.CharField(blank=False, max_length=255)
    tumor_type = models.CharField(blank=False, max_length=255)
    tissue_type = models.CharField(blank=False, max_length=255)
    variant = models.CharField(blank=False, max_length=255)
    tier = models.IntegerField()
    interpretation = models.ForeignKey('PMKBInterpretation', blank=True, null=True, on_delete = models.SET_NULL)
    source_row = models.IntegerField() # original row in .xlsx file
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return('[{0}] {1}...'.format(self.gene, self.variant[:15]))

class PMKBInterpretation(models.Model):
    """
    An interpretation for variant(s) in the PMKB database
    """
    interpretation = models.TextField(blank=True)
    citations = models.TextField(blank=True)
    source_row = models.IntegerField(blank=True, unique = True) # original row in .xlsx file
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return('[{0}] {1}...'.format(self.id, self.interpretation[:15]))
