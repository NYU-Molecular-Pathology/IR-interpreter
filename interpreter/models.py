from django.db import models
import json

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
    variant = models.CharField(blank=True, max_length=255)

    variant_types = (
    ('snp', 'snp'),
    ('fusion', 'fusion')
    )
    variant_type = models.CharField(choices=variant_types, max_length=255)
    # space delimeted list of gene IDs
    genes = models.CharField(blank=False, max_length=255)
    # auto-populated JSON list of genes from 'genes'
    genes_json = models.CharField(blank=True, max_length=255)
    tumor_type = models.CharField(blank=True, max_length=255)
    tissue_type = models.CharField(blank=True, max_length=255)
    interpretation = models.TextField(blank=True)
    citations = models.TextField(blank=True)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Parse the genes into a list to save as genes_json
        """
        gene_list = self.genes.split()
        self.genes_json = json.dumps(gene_list)

        # call the parent save method
        super().save(*args, **kwargs)
    def __str__(self):
        return('[{0}] {1}...'.format(self.genes, self.interpretation[:15]))

class NYUTier(models.Model):
    """
    NYU custom tiers for specific variants
    """
    variant_types = (
    ('snp', 'snp'),
    ('fusion', 'fusion')
    )
    variant_type = models.CharField(choices=variant_types, blank=False, max_length=255)
    tumor_type = models.CharField(blank=False, max_length=255)
    tissue_type = models.CharField(blank=False, max_length=255)
    coding = models.CharField(blank=False, max_length=255)
    protein = models.CharField(blank=False, max_length=255)
    tier = models.IntegerField()
    interpretation = models.TextField(blank=True)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
