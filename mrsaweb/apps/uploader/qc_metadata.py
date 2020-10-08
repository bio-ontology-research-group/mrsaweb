import schema_salad.schema
import schema_salad.ref_resolver
import schema_salad.jsonld_context
import logging
import pkg_resources
import logging
import traceback
import uuid
from rdflib import Graph, Namespace
from pyshex.evaluate import evaluate

def qc_metadata(metadatafile):
    schema_resource = pkg_resources.resource_stream(__name__, "schema.yml")
    cache = {"https://raw.githubusercontent.com/bio-ontology-research-group/mrsaweb/master/mrsaweb/apps/uploader/schema.yml": schema_resource.read().decode("utf-8")}
    (document_loader,
     avsc_names,
     schema_metadata,
     metaschema_loader) = schema_salad.schema.load_schema("https://raw.githubusercontent.com/bio-ontology-research-group/mrsaweb/master/mrsaweb/apps/uploader/schema.yml", cache=cache)

    shex = pkg_resources.resource_stream(__name__, "shex.rdf").read().decode("utf-8")

    if not isinstance(avsc_names, schema_salad.avro.schema.Names):
        print(avsc_names)
        return False

    try:
        doc, metadata = schema_salad.schema.load_and_validate(document_loader, avsc_names, metadatafile, True)
        doc["id"] = uuid.uuid4().urn
        g = schema_salad.jsonld_context.makerdf("workflow", doc, document_loader.ctx)
        rslt, reason = evaluate(g, shex, doc["id"], "https://raw.githubusercontent.com/bio-ontology-research-group/mrsaweb/master/mrsaweb/apps/uploader/shex.rdf#submissionShape")

        if not rslt:
            print(reason)

        return rslt
    except Exception as e:
        traceback.print_exc()
        logging.warn(e)
    return False


def to_rdf(uri, metadatafile):
    schema_resource = pkg_resources.resource_stream(__name__, "schema.yml")
    cache = {"https://raw.githubusercontent.com/bio-ontology-research-group/mrsaweb/master/mrsaweb/apps/uploader/schema.yml": schema_resource.read().decode("utf-8")}
    (document_loader,
     avsc_names,
     schema_metadata,
     metaschema_loader) = schema_salad.schema.load_schema("https://raw.githubusercontent.com/bio-ontology-research-group/mrsaweb/master/mrsaweb/apps/uploader/schema.yml", cache=cache)

    shex = pkg_resources.resource_stream(__name__, "shex.rdf").read().decode("utf-8")

    if not isinstance(avsc_names, schema_salad.avro.schema.Names):
        print(avsc_names)
        return False

    doc, metadata = schema_salad.schema.load_and_validate(document_loader, avsc_names, metadatafile, True)
    doc["id"] = uri
    return schema_salad.jsonld_context.makerdf("workflow", doc, document_loader.ctx)
