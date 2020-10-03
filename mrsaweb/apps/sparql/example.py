LIST_SUBMISSION_EXAMPLE = 'PREFIX MainSchema: <http://biohackathon.org/bh20-seq-schema#MainSchema/> \n \
PREFIX sio: <http://semanticscience.org/resource/> \n \
PREFIX efo: <http://www.ebi.ac.uk/efo/> \n \
PREFIX obo: <http://purl.obolibrary.org/obo/> \n \
PREFIX evs: <http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#> \n \
PREFIX edam: <http://edamontology.org/> \n \
 \n \
select distinct ?sub ?host_species ?sample_id ?collection_date ?submitter ?seq_technology ?virus_species \n \
from <https://workbench.cborg.cbrc.kaust.edu.sa>  \n \
 \n \
where { \n \
 \n \
  ?sub MainSchema:host  ?host ; \n \
       MainSchema:sample ?sample ; \n \
       MainSchema:submitter ?submitter ; \n \
       MainSchema:technology ?technology ; \n \
       MainSchema:virus ?virus . \n \
 \n \
  ?host efo:EFO_0000532 ?host_species . \n \
 \n \
  ?sample sio:SIO_000115 ?sample_id; \n \
	  evs:C25164 ?collection_date . \n \
 \n \
  ?virus edam:data_1875 ?virus_species . \n \
  ?technology obo:OBI_0600047 ?seq_technology . \n \
 \n \
} ORDER BY 1 LIMIT 10'

LIST_SARS_COV_SUBMISSION_EXAMPLE = 'PREFIX MainSchema: <http://biohackathon.org/bh20-seq-schema#MainSchema/> \n \
PREFIX sio: <http://semanticscience.org/resource/> \n \
PREFIX efo: <http://www.ebi.ac.uk/efo/> \n \
PREFIX obo: <http://purl.obolibrary.org/obo/> \n \
PREFIX evs: <http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#> \n \
PREFIX edam: <http://edamontology.org/> \n \
 \n \
select distinct ?sub ?host_species ?sample_id ?collection_date ?submitter ?seq_technology (obo:NCBITaxon_2697049 as ?virus_species) \n \
from <https://workbench.cborg.cbrc.kaust.edu.sa>  \n \
 \n \
where { \n \
 \n \
  ?sub MainSchema:host  ?host ; \n \
       MainSchema:sample ?sample ; \n \
       MainSchema:submitter ?submitter ; \n \
       MainSchema:technology ?technology ; \n \
        MainSchema:virus ?virus .  \n \
  ?virus edam:data_1875 obo:NCBITaxon_2697049 .  \n \
 \n \
  ?host efo:EFO_0000532 ?host_species . \n \
 \n \
  ?sample sio:SIO_000115 ?sample_id; \n \
	  evs:C25164 ?collection_date . \n \
  ?technology obo:OBI_0600047 ?seq_technology . \n \
 \n \
} ORDER BY 1 LIMIT 10'


GET_SUBMISSION_BY_URI_EXAMPLE = 'PREFIX MainSchema: <http://biohackathon.org/bh20-seq-schema#MainSchema/> \n \
PREFIX sio: <http://semanticscience.org/resource/> \n \
PREFIX efo: <http://www.ebi.ac.uk/efo/> \n \
PREFIX obo: <http://purl.obolibrary.org/obo/> \n \
PREFIX evs: <http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#> \n \
PREFIX edam: <http://edamontology.org/> \n \
 \n \
select distinct (<http://arvados.org/keep:00a6af865453564f6a59b3d2c81cc7c1+123/sequence.fasta> as ?submission) \n \
        ?host_id ?host_species ?host_sex ?host_age ?host_age_unit ?host_health_status ?host_treatment (group_concat(distinct ?host_vaccination;separator=",") as ?host_vaccinations) ?ethnicity \n \
        ?sample_id (group_concat(distinct ?specimen_source;separator=",") as ?specimen_sources) ?sample_storage_conditions (group_concat(distinct ?source_database_accession;separator=",") as ?source_database_accessions)  \n \
        ?collector_name ?collection_date ?collecting_institution ?collection_location \n \
       (group_concat(distinct ?seq_technology;separator=",") as ?seq_technologies) ?sequence_assembly_method (group_concat(distinct ?sequencing_coverage;separator=",") as ?sequencing_coverages) \n \
       ?virus_species ?virus_strain \n \
from <https://workbench.cborg.cbrc.kaust.edu.sa>  \n \
 \n \
where { \n \
  <http://arvados.org/keep:00a6af865453564f6a59b3d2c81cc7c1+123/sequence.fasta> MainSchema:host  ?host ; \n \
       MainSchema:sample ?sample ; \n \
       MainSchema:submitter ?submitter ; \n \
       MainSchema:technology ?technology ; \n \
       MainSchema:virus ?virus . \n \
 \n \
  ?host efo:EFO_0000532 ?host_species . \n \
  OPTIONAL { ?host sio:SIO_000115 ?host_id .} \n \
  OPTIONAL { ?host obo:PATO_0000047 ?host_sex .} \n \
  OPTIONAL { ?host obo:PATO_0000011 ?host_age .} \n \
  OPTIONAL { ?host obo:NCIT_C42574 ?host_age_unit .} \n \
  OPTIONAL { ?host obo:NCIT_C25688 ?host_health_status .} \n \
  OPTIONAL { ?host efo:EFO_0000727 ?host_treatment .} \n \
  OPTIONAL { ?host efo:VO_0000002 ?host_vaccination .} \n \
  OPTIONAL { ?host sio:SIO_001014 ?ethnicity .} \n \
 \n \
  ?sample sio:SIO_000115 ?sample_id; \n \
	  evs:C25164 ?collection_date . \n \
  OPTIONAL { ?sample obo:OBI_0001479 ?specimen_source .} \n \
  OPTIONAL { ?sample obo:OBI_0001472 ?sample_storage_conditions .} \n \
  OPTIONAL { ?sample edam:data_2091 ?source_database_accession .} \n \
  OPTIONAL { ?sample obo:OBI_0001895 ?collector_name .} \n \
  OPTIONAL { ?sample obo:NCIT_C41206 ?collecting_institution .} \n \
  OPTIONAL { ?sample obo:GAZ_00000448 ?collection_location .} \n \
 \n \
  ?virus edam:data_1875 ?virus_species . \n \
  OPTIONAL { ?virus sio:SIO_010055 ?virus_strain .} \n \
 \n \
  ?technology obo:OBI_0600047 ?seq_technology . \n \
  OPTIONAL { ?technology efo:EFO_0002699 ?sequence_assembly_method .} \n \
  OPTIONAL { ?technology obo:FLU_0000848 ?sequencing_coverage .} \n \
}'
