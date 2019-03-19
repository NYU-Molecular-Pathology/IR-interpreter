from django.db import models
from .util import sanitize_genes
import json

variant_types = (
('snp', 'snp'),
('fusion', 'fusion'),
('indel', 'indel'),
('cnv', 'cnv'),
)

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

class TissueType(models.Model):
    """
    All the tissue types available for selection
    """
    type = models.CharField(blank=False, null=False, unique = True, max_length=255)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return(str(self.type))

class TumorType(models.Model):
    """
    All the tumor types available for selection
    """
    type = models.CharField(blank=False, null=False, unique = True, max_length=255)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return(str(self.type))

class PMKBVariant(models.Model):
    """
    Details about an individual variant registered in the PMKB
    """
    gene = models.CharField(blank=False, max_length=255)
    tumor_type = models.ForeignKey(TumorType, on_delete=models.SET_DEFAULT, default = '')
    tissue_type = models.ForeignKey(TissueType, on_delete=models.SET_DEFAULT, default = '')
    variant = models.CharField(blank=False, max_length=255)
    tier = models.IntegerField()
    interpretation = models.ForeignKey('PMKBInterpretation', blank=True, null=True, on_delete = models.SET_NULL)
    source_row = models.IntegerField() # original row in .xlsx file
    uid = models.CharField(null=False, unique = True, max_length=255) # need a unique key for database setup... put md5sum here
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
    variant_type = models.CharField(choices = variant_types, max_length=255)
    # space delimeted list of gene IDs, user-entered, could be many
    genes = models.CharField(blank=False, max_length=255)
    # auto-populated JSON list of genes from 'genes'
    genes_json = models.CharField(blank=True, max_length=255)
    tumor_type = models.ForeignKey(TumorType, on_delete=models.SET_DEFAULT, default = '')
    tissue_type = models.ForeignKey(TissueType, on_delete=models.SET_DEFAULT, default = '')
    interpretation = models.TextField(blank=True)
    citations = models.TextField(blank=True)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Parse the genes into a list to save as genes_json
        """
        gene_list = sanitize_genes(self.genes.split())
        self.genes_json = json.dumps(gene_list)

        # call the parent save method
        super().save(*args, **kwargs)
    def __str__(self):
        return('[{0}] {1}...'.format(self.genes, self.interpretation[:15]))

class NYUTier(models.Model):
    """
    NYU custom tiers for specific variants
    """
    gene = models.CharField(blank=False, max_length=255)
    variant_type = models.CharField(choices = variant_types, blank=False, max_length=255)
    tumor_type = models.ForeignKey(TumorType, on_delete=models.SET_DEFAULT, default = '')
    tissue_type = models.ForeignKey(TissueType, on_delete=models.SET_DEFAULT, default = '')
    coding = models.CharField(blank=False, max_length=255)
    protein = models.CharField(blank=False, max_length=255)
    tier = models.IntegerField()
    comment = models.TextField(blank=True)
    imported = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
