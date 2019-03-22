from django.db import models
from .util import sanitize_genes
import json
import os

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
        return("{0} [{1}]".format(self.view, self.ip))

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

# load relative paths from JSON file
config_json = os.path.join(os.path.realpath(os.path.dirname(__file__)), "importer.json")
with open(config_json) as f:
    config_json_data = json.load(f)

fixtures_dir = os.path.join(os.path.realpath(os.path.dirname(__file__)), config_json_data['fixtures_dir'])
nyu_added_interpretations_json = os.path.join(fixtures_dir, config_json_data['nyu_added_interpretations_json'])
nyu_added_tiers_json = os.path.join(fixtures_dir, config_json_data['nyu_added_tiers_json'])

def NYUInterpretation_to_json(instance, json_file = nyu_added_interpretations_json):
    """
    Save copies of all items to a JSON file
    """
    # load a list of old entries
    with open(nyu_added_interpretations_json) as f:
        data = json.load(f)
    # start a dict to save to the JSON
    d = {}
    d['model'] = 'interpreter.NYUInterpretation'
    d['pk'] = instance.id
    d['fields'] = {}
    d['fields']['variant'] = str(instance.variant)
    d['fields']['variant_type'] = str(instance.variant_type)
    d['fields']['genes'] = str(instance.genes)
    d['fields']['tumor_type'] = str(instance.tumor_type.type)
    d['fields']['tissue_type'] = str(instance.tissue_type.type)
    d['fields']['interpretation'] = str(instance.interpretation)
    d['fields']['citations'] = str(instance.citations)

    # add new dict to list
    data.append(d)

    # write new JSON file
    with open(nyu_added_interpretations_json, "w") as f:
        json.dump(data, f, indent = 4)

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

        # save a copy to the JSON
        NYUInterpretation_to_json(instance = self)

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
