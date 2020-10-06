import pkg_resources
import yaml
import re
import string
import arvados

api = arvados.api()

def type_to_heading(type_name):
    """
    Turn a type name like "sampleSchema" from the metadata schema into a human-readable heading.
    """

    # Remove camel case
    decamel = re.sub('([A-Z])', r' \1', type_name)
    # Split
    parts = decamel.split()
    # Capitalize words and remove unwanted components
    filtered = [part.capitalize() for part in parts if (part.lower() != 'schema' and part != '')]
    # Reassemble
    return ' '.join(filtered)

def name_to_label(field_name):
    """
    Turn a filed name like "host_health_status" from the metadata schema into a human-readable label.
    """
    
    # May end in a number, which should be set off by a space
    set_off_number = re.sub('([0-9]+)$', r' \1', field_name)
    
    return string.capwords(set_off_number.replace('_', ' '))

def is_iri(string):
    """
    Return True if the given string looks like an IRI, and False otherwise.
    Used for finding type IRIs in the schema.
    Right now only supports http(s) URLs because that's all we have in our schema.
    """

    return string.startswith('http')

def generate_form(schema, options):
    """
    Linearize the schema into a list of dicts.
    Each dict either has a 'heading' (in which case we put a heading for a
    form section in the template) or an 'id', 'label', 'type', and 'required'
    (in which case we make a form field in the template).
    
    Non-heading dicts with type 'select' will have an 'options' field, with a
    list of (name, value) tuples, and represent a form dropdown element.
    
    Non-heading dicts with type 'number' may have a 'step', which, if <1 or
    'any', allows the number to be a float.
    
    Non-heading dicts may have a human-readable 'docstring' field describing
    them.
    Takes the deserialized metadata schema YAML, and also a deserialized YAML
    of option values. The option values are keyed on (unscoped) field name in
    the schema, and each is a dict of human readable option -> corresponding
    IRI.
    """

    # Get the list of form components, one of which is the root
    components = schema.get('$graph', [])

    # Find the root
    root_name = None
    # And also index components by type name
    by_name = {}
    for component in components:
        # Get the name of each
        component_name = component.get('name', None)
        if isinstance(component_name, str):
            # And remember how to map back form it
            by_name[component_name] = component
        if component.get('documentRoot', False):
            # Find whichever one is the root
            root_name = component_name


    def walk_fields(type_name, parent_keys=['metadata'], subtree_optional=False):
        """
        Do a traversal of the component tree.
        Yield a bunch of form item dicts, in order.
        Form IDs are .-separated keypaths for where they are in the structure.
        parent_keys is the path of field names to where we are in the root record's document tree.
        """

        if len(parent_keys) > 1:
            # First make a heading, if we aren't the very root of the form
            yield {'heading': type_to_heading(type_name)}

        for field_name, field_type in by_name.get(type_name, {}).get('fields', {}).items():
            # For each field

            ref_iri = None
            docstring = None
            if not isinstance(field_type, str):
                # If the type isn't a string
                
                # It may have documentation
                docstring = field_type.get('doc', None)

                # See if it has a more info/what goes here URL
                predicate = field_type.get('jsonldPredicate', {})
                # Predicate may be a URL, a dict with a URL in _id, maybe a
                # dict with a URL in _type, or a dict with _id and _type but no
                # URLs anywhere. Some of these may not technically be allowed
                # by the format, but if they occur, we might as well try to
                # handle them.
                if isinstance(predicate, str):
                    if is_iri(predicate):
                        ref_iri = predicate
                else:
                    # Assume it's a dict. Look at the fields we know about.
                    for field in ['_id', 'type']:
                        field_value = predicate.get(field, None)
                        if isinstance(field_value, str) and is_iri(field_value) and ref_iri is None:
                            # Take the first URL-looking thing we find
                            ref_iri = field_value
                            break


                # Now overwrite the field type with the actual type string
                field_type = field_type.get('type', '')

            # Decide if the field is optional (type ends in ?)
            optional = False
            if field_type.endswith('?'):
                # It's optional
                optional = True
                # Drop the ?
                field_type = field_type[:-1]
                
            # Decide if the field is a list (type ends in [])
            is_list = False
            if field_type.endswith('[]'):
                # It's a list
                is_list = True
                # Reduce to the normal type
                field_type = field_type[:-2]

            if field_type in by_name:
                # This is a subrecord. We need to recurse
                for item in walk_fields(field_type, parent_keys + [field_name], subtree_optional or optional):
                    yield item
            else:
                # This is a leaf field. We need an input for it.
                record = {}
                record['id'] = '.'.join(parent_keys + [field_name])
                record['label'] = name_to_label(field_name)
                record['required'] = not optional and not subtree_optional
                record['list'] = is_list
                if ref_iri:
                    record['ref_iri'] = ref_iri
                if docstring:
                    record['docstring'] = docstring

                if field_name in options:
                    # The field will be a 'select' type no matter what its real
                    # data type is.
                    record['type'] = 'select' # Not a real HTML input type. It's its own tag.
                    # We have a set of values to present
                    record['options'] = []
                    for name, value in options[field_name].items():
                        # Make a tuple for each one
                        record['options'].append((value, name))
                elif field_type == 'string':
                    if field_name.endswith('date'):
                        # Use a date picker to generate a good string.
                        # Comes back YYYY-MM-DD.
                        record['type'] = 'date'
                    else:
                        # Normal text string
                        record['type'] = 'text'
                elif field_type == 'int':
                    record['type'] = 'number'
                elif field_type == 'float' or field_type == 'double':
                    record['type'] = 'number'
                    # Choose a reasonable precision for the control
                    record['step'] = '0.0001'
                else:
                    raise NotImplementedError('Unimplemented field type {} in {} in metadata schema'.format(field_type, type_name))
                yield record

    return list(walk_fields(root_name))


METADATA_SCHEMA = yaml.safe_load(pkg_resources.resource_stream("uploader", "schema.yml"))
METADATA_OPTION_DEFINITIONS = yaml.safe_load(pkg_resources.resource_stream("uploader", "options.yml"))
FORM_ITEMS = generate_form(METADATA_SCHEMA, METADATA_OPTION_DEFINITIONS)
ONT_TO_URI_PATTERN_MAP = {
    'NCBITAXON': 'http://purl.obolibrary.org/obo/NCBITaxon_',
    'HANCESTRO': 'http://purl.obolibrary.org/obo/HANCESTRO_',
    'UO': 'http://purl.obolibrary.org/obo/UO_',
    'PATO': 'http://purl.obolibrary.org/obo/PATO_',
    'NCIT': 'http://purl.obolibrary.org/obo/NCIT_',
    'GENEPIO': 'http://purl.obolibrary.org/obo/GENEPIO_',
    'OBI': 'http://purl.obolibrary.org/obo/OBI_',
    'EFO': 'http://www.ebi.ac.uk/efo/EFO_'
}


PREFIX_MAP = {
    'MainSchema': 'http://cbrc.kaust.edu.sa/mrsa-schema#MainSchema/',
    'hostSchema': 'http://cbrc.kaust.edu.sa/mrsa-schema#hostSchema/',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'obo': 'http://purl.obolibrary.org/obo/',
    'sio': 'http://semanticscience.org/resource/',
    'efo': 'http://www.ebi.ac.uk/efo/>',
    'evs': 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#',
    'edam': 'http://edamontology.org/',
    'wikidata': 'http://www.wikidata.org/entity/'
}

def to_prefixed_uri(val):
    for key in PREFIX_MAP:
        if isinstance(val, str) and PREFIX_MAP[key] in val:
            return val.replace(PREFIX_MAP[key], key + ":")
        
        if isinstance(val, list):
            prefixed_val = []
            for i in range(len(val)):
                if PREFIX_MAP[key] in val[i]:
                    prefixed_val.append(val[i].replace(PREFIX_MAP[key], key + ":"))
                else:
                    prefixed_val.append(val[i])
            return prefixed_val
    return val

def get_ontology(val):
    ont_list =[]
    for key in ONT_TO_URI_PATTERN_MAP:
        if isinstance(val, str) and ONT_TO_URI_PATTERN_MAP[key] in val:
            return [{'iri': val, 'ontology': key}]

        if isinstance(val, list):
            for i in range(len(val)):
                if ONT_TO_URI_PATTERN_MAP[key] in val[i]:
                    ont_list.append({'iri': val[i], 'ontology': key})
    return ont_list

def fix_iri_path_param(iri):
    iri = re.sub(r'(?!http:\/\/)(http:\/){1}', 'http://', iri)
    iri = re.sub(r'(?!https:\/\/)(https:\/){1}', 'https://', iri)
    return iri