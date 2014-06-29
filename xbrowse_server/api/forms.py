from django import forms
from django.conf import settings
import json
from xbrowse import variant_filters as xbrowse_variant_filters
from xbrowse import quality_filters as xbrowse_quality_filters
from xbrowse.core.variant_filters import VariantFilter
from xbrowse_server.base.models import Family
from xbrowse.analysis_modules.mendelian_variant_search import MendelianVariantSearchSpec
from xbrowse.analysis_modules.combine_mendelian_families import CombineMendelianFamiliesSpec
from xbrowse.analysis_modules.cohort_gene_search import CohortGeneSearchSpec
from xbrowse.analysis_modules.diagnostic_search import DiagnosticSearchSpec

import utils

# TODO: these forms should return a SearchSpec class - possibly subclasses for each search type
from xbrowse_server.gene_lists.models import GeneList


def parse_variant_filter(cleaned_data):
    """
    Sets cleaned_data['variant_filter'] for a form, throwing ValidationError if necessary
    """
    if cleaned_data.get('variant_filter_name'):
        if cleaned_data['variant_filter_name'] not in xbrowse_variant_filters.DEFAULT_VARIANT_FILTERS_DICT:
            raise forms.ValidationError('Unknown variant filter: {}'.format(cleaned_data['variant_filter_name']))
        cleaned_data['variant_filter'] = xbrowse_variant_filters.DEFAULT_VARIANT_FILTERS_DICT[cleaned_data['variant_filter_name']]['variant_filter']
    elif cleaned_data.get('variant_filter'):
        variant_filter_d = json.loads(cleaned_data.get('variant_filter'))
        if variant_filter_d.get('genes_raw'):
            success, result = utils.get_gene_id_list_from_raw(variant_filter_d.get('genes_raw'), settings.REFERENCE)
            if not success:
                raise forms.ValidationError("{} is not a recognized gene or gene set".format(variant_filter_d['genes_raw']))
            variant_filter_d['genes'] = result
            del variant_filter_d['genes_raw']

        if variant_filter_d.get('regions'):
            success, result = utils.get_locations_from_raw(variant_filter_d.get('regions'), settings.REFERENCE)
            if not success:
                raise forms.ValidationError("%s is not a recognized region" % result)
            variant_filter_d['locations'] = result
            del variant_filter_d['regions']
        cleaned_data['variant_filter'] = VariantFilter(**variant_filter_d)


def parse_quality_filter(cleaned_data):

    if cleaned_data.get('quality_filter_name'):
        if cleaned_data.get('quality_filter_name') not in xbrowse_quality_filters.DEFAULT_QUALITY_FILTERS_DICT:
            raise forms.ValidationError("%s is not a valid quality filter name" % cleaned_data.get('quality_filter_name'))
        cleaned_data['quality_filter'] = xbrowse_quality_filters.DEFAULT_QUALITY_FILTERS_DICT[cleaned_data.get('quality_filter_name')]['quality_filter']
    elif cleaned_data.get('quality_filter'):
        qf_dict = json.loads(cleaned_data.get('quality_filter'))
        # TODO
        # if 'hom_alt_ratio' in qf_dict:
        #     qf_dict['hom_alt_ratio'] = float(qf_dict['hom_alt_ratio']) / 100
        # if 'het_ratio' in qf_dict:
        #     qf_dict['het_ratio'] = float(qf_dict['het_ratio']) / 100
        cleaned_data['quality_filter'] = qf_dict


def parse_genotype_filter(cleaned_data):
    if cleaned_data.get('genotype_filter'):
        cleaned_data['genotype_filter'] = json.loads(cleaned_data.get('genotype_filter'))


def parse_burden_filter(cleaned_data):
    if cleaned_data.get('burden_filter'):
        cleaned_data['burden_filter'] = json.loads(cleaned_data.get('burden_filter'))


def parse_family_tuple_list(cleaned_data):
    families = []
    family_tuples = json.loads(cleaned_data.get('family_tuple_list'))
    for project_id, family_id in family_tuples:
        families.append(Family.objects.get(project__project_id=project_id, family_id=family_id))
    cleaned_data['families'] = families


def parse_allele_count_filter(cleaned_data):
    if cleaned_data.get('allele_count_filter'):
        json_dict = json.loads(cleaned_data['allele_count_filter'])
        cleaned_data['allele_count_filter'] = xbrowse_variant_filters.AlleleCountFilter(**json_dict)


class MendelianVariantSearchForm(forms.Form):

    search_mode = forms.CharField()
    variant_filter_name = forms.CharField(required=False)
    variant_filter = forms.CharField(required=False)
    quality_filter_name = forms.CharField(required=False)
    quality_filter = forms.CharField(required=False)

    inheritance_mode = forms.CharField(required=False)
    genotype_filter = forms.CharField(required=False)
    burden_filter = forms.CharField(required=False)
    allele_count_filter = forms.CharField(required=False)

    def clean(self):

        cleaned_data = super(MendelianVariantSearchForm, self).clean()

        if cleaned_data['search_mode'] not in ['standard_inheritance', 'custom_inheritance', 'gene_burden', 'allele_count', 'all_variants']:
            raise forms.ValidationError("Invalid search mode: {}".format(cleaned_data['search_mode']))

        if cleaned_data['search_mode'] == 'standard_inheritance' and not cleaned_data.get('inheritance_mode'):
            raise forms.ValidationError("Inheritance mode is required for standard search. ")

        parse_variant_filter(cleaned_data)
        parse_quality_filter(cleaned_data)
        parse_genotype_filter(cleaned_data)
        parse_burden_filter(cleaned_data)
        parse_allele_count_filter(cleaned_data)

        search_spec = MendelianVariantSearchSpec()
        search_spec.search_mode = cleaned_data['search_mode']
        search_spec.inheritance_mode = cleaned_data.get('inheritance_mode')
        search_spec.genotype_inheritance_filter = cleaned_data.get('genotype_filter')
        search_spec.gene_burden_filter = cleaned_data.get('gene_burden_filter')
        search_spec.allele_count_filter = cleaned_data.get('allele_count_filter')
        search_spec.variant_filter = cleaned_data.get('variant_filter')
        search_spec.genotype_quality_filter = cleaned_data.get('quality_filter')
        cleaned_data['search_spec'] = search_spec

        return cleaned_data


class CohortVariantSearchForm(forms.Form):

    search_mode = forms.CharField()
    variant_filter_name = forms.CharField(required=False)
    variant_filter = forms.CharField(required=False)
    quality_filter_name = forms.CharField(required=False)
    quality_filter = forms.CharField(required=False)
    genotype_filter = forms.CharField(required=False)
    burden_filter = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(CohortVariantSearchForm, self).clean()
        if cleaned_data['search_mode'] not in ['custom_inheritance', 'gene_burden']:
            raise forms.ValidationError("Invalid search mode: {}".format(cleaned_data['search_mode']))

        parse_variant_filter(cleaned_data)
        parse_quality_filter(cleaned_data)
        parse_genotype_filter(cleaned_data)
        parse_burden_filter(cleaned_data)

        search_spec = MendelianVariantSearchSpec()
        search_spec.search_mode = cleaned_data['search_mode']
        search_spec.inheritance_mode = cleaned_data.get('inheritance_mode')
        search_spec.genotype_inheritance_filter = cleaned_data.get('genotype_filter')
        search_spec.gene_burden_filter = cleaned_data.get('gene_burden_filter')
        search_spec.allele_count_filter = cleaned_data.get('allele_count_filter')
        search_spec.variant_filter = cleaned_data.get('variant_filter')
        search_spec.genotype_quality_filter = cleaned_data.get('quality_filter')
        cleaned_data['search_spec'] = search_spec

        return cleaned_data


class CohortGeneSearchForm(forms.Form):

    inheritance_mode = forms.CharField()
    variant_filter_name = forms.CharField(required=False)
    variant_filter = forms.CharField(required=False)
    quality_filter_name = forms.CharField(required=False)
    quality_filter = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(CohortGeneSearchForm, self).clean()

        parse_variant_filter(cleaned_data)
        parse_quality_filter(cleaned_data)

        search_spec = CohortGeneSearchSpec()
        search_spec.inheritance_mode = cleaned_data.get('inheritance_mode')
        search_spec.variant_filter = cleaned_data.get('variant_filter')
        search_spec.genotype_quality_filter = cleaned_data.get('quality_filter')
        cleaned_data['search_spec'] = search_spec

        return cleaned_data


class CohortGeneSearchVariantsForm(CohortGeneSearchForm):

    gene_id = forms.CharField()

    def clean(self):
        cleaned_data = super(CohortGeneSearchVariantsForm, self).clean()
        if not settings.REFERENCE.is_valid_gene_id(cleaned_data['gene_id']):
            raise forms.ValidationError("{} is not a valid gene ID".format(cleaned_data['gene_id']))
        return cleaned_data


class CombineMendelianFamiliesForm(forms.Form):

    inheritance_mode = forms.CharField()
    variant_filter_name = forms.CharField(required=False)
    variant_filter = forms.CharField(required=False)
    quality_filter_name = forms.CharField(required=False)
    quality_filter = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(CombineMendelianFamiliesForm, self).clean()
        parse_variant_filter(cleaned_data)
        parse_quality_filter(cleaned_data)

        search_spec = CombineMendelianFamiliesSpec()
        search_spec.inheritance_mode = cleaned_data.get('inheritance_mode')
        search_spec.variant_filter = cleaned_data.get('variant_filter')
        search_spec.genotype_quality_filter = cleaned_data.get('quality_filter')
        cleaned_data['search_spec'] = search_spec

        return cleaned_data


class CombineMendelianFamiliesVariantsForm(forms.Form):

    inheritance_mode = forms.CharField()
    gene_id = forms.CharField()
    family_tuple_list = forms.CharField()
    variant_filter_name = forms.CharField(required=False)
    variant_filter = forms.CharField(required=False)
    quality_filter_name = forms.CharField(required=False)
    quality_filter = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(CombineMendelianFamiliesVariantsForm, self).clean()
        parse_variant_filter(cleaned_data)
        parse_quality_filter(cleaned_data)
        parse_family_tuple_list(cleaned_data)

        if not settings.REFERENCE.is_valid_gene_id(cleaned_data['gene_id']):
            raise forms.ValidationError("{} is not a valid gene ID".format(cleaned_data['gene_id']))

        return cleaned_data

# class VariantInfoForm(forms.Form):
#
#     xpos = forms.CharField()
#     ref = forms.CharField()
#     alt = forms.CharField()
#
#     def clean(self):
#         cleaned_data = super(VariantInfoForm, self).clean()
#         cleaned_data['xpos'] = int()



class DiagnosticSearchForm(forms.Form):

    gene_list_slug = forms.CharField()
    variant_filter_name = forms.CharField(required=False)
    variant_filter = forms.CharField(required=False)

    def __init__(self, family, *args, **kwargs):
        super(DiagnosticSearchForm, self).__init__(*args, **kwargs)
        self.family = family

    def clean(self):
        cleaned_data = super(DiagnosticSearchForm, self).clean()
        parse_variant_filter(cleaned_data)
        cleaned_data['gene_list'] = GeneList.objects.get(slug=cleaned_data.get('gene_list_slug'))

        search_spec = DiagnosticSearchSpec()
        search_spec.inheritance_mode = cleaned_data.get('inheritance_mode')
        search_spec.variant_filter = cleaned_data.get('variant_filter')
        search_spec.gene_ids = cleaned_data['gene_list'].gene_id_list()
        cleaned_data['search_spec'] = search_spec

        return cleaned_data