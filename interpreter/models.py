from django.db import models

class UserAccessMetric(models.Model):
    """
    Details about usage of the app
    """
    ip = models.CharField(max_length=100)
    view = models.CharField(max_length=255)
    visited = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return(self.ip)

class UserUploadMetric(models.Model):
    """
    Details about usage of the app
    """
    ip = models.CharField(max_length=100)
    size = models.IntegerField()
    visited = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return(self.ip)

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

class NYUInterpretation(models.Model):
    """
    Custom NYU interpretation
    """
    tumor_type = models.CharField(blank=False, max_length=255)
    tissue_type = models.CharField(blank=False, max_length=255)
    variant = models.CharField(blank=False, max_length=255)
    variant_type = models.CharField(blank=False, max_length=255)
    interpretation = models.TextField(blank=True)
    citations = models.TextField(blank=True)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class NYUInterpretationGene(models.Model):
    """
    A gene entry associated with an NYUInterpretation; there may be multiple genes per NYUInterpretation
    """
    interpretation = models.ForeignKey('NYUInterpretation', blank=True, null=True, on_delete = models.SET_NULL)
    gene = models.CharField(blank=False, max_length=255)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class NYUTier(models.Model):
    """
    NYU custom tiers for specific variants
    """
    variant_type = models.CharField(blank=False, max_length=255)
    tumor_type = models.CharField(blank=False, max_length=255)
    tissue_type = models.CharField(blank=False, max_length=255)
    coding = models.CharField(blank=False, max_length=255)
    protein = models.CharField(blank=False, max_length=255)
    tier = models.IntegerField()
    interpretation = models.TextField(blank=True)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
