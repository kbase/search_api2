
# A request to get a total count on refdata for a search query
search_request1 = {
    "id": "xyz",
    "method": "KBaseSearchEngine.search_objects",
    "version": "1.1",
    "params": [{
        "access_filter": {
            "with_private": 0,
            "with_public": 1
        },
        "match_filter": {
            "exclude_subobjects": 1,
            "full_text_in_all": "coli",
            "source_tags": ["refdata"],
            "source_tags_blacklist": 0
        },
        "pagination": {
            "count": 0,
            "start": 0
        },
        "post_processing": {
            "ids_only": 1,
            "include_highlight": 1,
            "skip_data": 1,
            "skip_info": 1,
            "skip_keys": 1
        }
    }]
}

search_response1 = {
    "id": "xyz",
    "jsonrpc": "2.0",
    "result": [{
        "pagination": {
            "start": 0,
            "count": 0
        },
        "sorting_rules": [{
          "property": "timestamp",
          "is_object_property": 0,
          "ascending": 1
        }],
        "objects": [],
        "total": 15039,
        "search_time": 1848
    }]
}

# Method call to get type counts
search_request2 = {
    "version": "1.1",
    "method": "KBaseSearchEngine.search_types",
    "id": "6959719268936883",
    "params": [{
        "access_filter": {
            "with_private": 1,
            "with_public": 1
        },
        "match_filter": {
            "exclude_subobjects": 1,
            "full_text_in_all": "coli",
            "source_tags": ["refdata", "noindex"],
            "source_tags_blacklist": 1
        }
    }]
}

search_response2 = {
    "id": "6959719268936883",
    "jsonrpc": "2.0",
    "result": [{
        "type_to_count": {
            "Narrative": 13,
            "Taxon": 3318,
            "Tree": 3,
            "Genome": 3174,
            "Workspace": 1
        },
        "search_time": 1506
    }]
}

search_request3 = {
  "id": "xyz",
  "method": "KBaseSearchEngine.search_objects",
  "params": [{
    "access_filter": {
      "with_private": 1,
      "with_public": 1
    },
    "match_filter": {
      "exclude_subobjects": 1,
      "full_text_in_all": "coli",
      "source_tags": ["refdata", "noindex"],
      "source_tags_blacklist": 1
    },
    "pagination": {
      "count": 20,
      "start": 0
    },
    "post_processing": {
      "add_narrative_info": 1,
      "ids_only": 0,
      "include_highlight": 1,
      "skip_data": 0,
      "skip_info": 0,
      "skip_keys": 0
    },
    "sorting_rules": [{
      "ascending": 0,
      "is_object_property": 0,
      "property": "access_group_id"
    }, {
      "ascending": 1,
      "is_object_property": 0,
      "property": "type"
    }]
  }],
  "version": "1.1"
}

search_response3 = {
    "id": "xyz",
    "jsonrpc": "2.0",
    "result": [{
        "pagination": {"start": 0, "count": 20},
        "sorting_rules": [{
            "property": "access_group_id",
            "is_object_property": 0,
            "ascending": 0
        }, {
            "property": "type",
            "is_object_property": 0,
            "ascending": 1
        }],
        "objects": [],
        "total": 6509,
        "search_time": 1918,
        "access_group_narrative_info": {},
    }]
}

# Genome features search to get the total count
search_request4 = {
  "id": "17499051636214047",
  "method": "KBaseSearchEngine.search_objects",
  "params": [{
    "access_filter": {
      "with_private": 1,
      "with_public": 1
    },
    "match_filter": {
      "exclude_subobjects": 0,
      "full_text_in_all": "coli",
      "source_tags": [],
      "source_tags_blacklist": 0
    },
    "object_types": ["GenomeFeature"],
    "pagination": {
      "count": 0,
      "start": 0
    },
    "post_processing": {
      "add_access_group_info": 0,
      "ids_only": 1,
      "include_highlight": 0,
      "skip_data": 1,
      "skip_info": 1,
      "skip_keys": 1
    }
  }],
  "version": "1.1"
}

search_response4 = {
  "jsonrpc": "2.0",
  "id": "17499051636214047",
  "result": [{
    "pagination": {
      "start": 0,
      "count": 0
    },
    "sorting_rules": [{
      "property": "timestamp",
      "is_object_property": 0,
      "ascending": 1
    }],
    "objects": [],
    "total": 94222799,
    "search_time": 355
  }]
}

search_request5 = {
  "id": "2328138435664152",
  "method": "KBaseSearchEngine.search_objects",
  "params": [{
    "access_filter": {
      "with_private": 1,
      "with_public": 1
    },
    "match_filter": {
      "exclude_subobjects": 0,
      "full_text_in_all": "coli",
      "source_tags": [],
      "source_tags_blacklist": 0
    },
    "object_types": ["GenomeFeature"],
    "pagination": {
      "count": 20,
      "start": 0
    },
    "post_processing": {
      "add_access_group_info": 1,
      "ids_only": 0,
      "include_highlight": 1,
      "skip_data": 0,
      "skip_info": 0,
      "skip_keys": 0
    },
    "sorting_rules": [{
      "ascending": 1,
      "is_object_property": 1,
      "property": "genome_scientific_name"
    }, {
      "ascending": 1,
      "is_object_property": 0,
      "property": "guid"
    }, {
      "ascending": 1,
      "is_object_property": 1,
      "property": "feature_type"
    }, {
      "ascending": 1,
      "is_object_property": 1,
      "property": "id"
    }]
  }],
  "version": "1.1"
}

search_response5 = {
  "jsonrpc": "2.0",
  "id": "2328138435664152",
  "result": [{
    "pagination": {
      "start": 0,
      "count": 20
    },
    "sorting_rules": [{
      "property": "genome_scientific_name",
      "is_object_property": 1,
      "ascending": 1
    }, {
      "property": "guid",
      "is_object_property": 0,
      "ascending": 1
    }, {
      "property": "feature_type",
      "is_object_property": 1,
      "ascending": 1
    }, {
      "property": "id",
      "is_object_property": 1,
      "ascending": 1
    }],
    "objects": [{
      "guid": "WS:4258/13216/1:feature/kb|g.2231.peg.5834",
      "parent_guid": "WS:4258/13216/1",
      "object_name": "kb|g.2231",
      "timestamp": 1453530416321,
      "type": "GenomeFeature",
      "type_ver": 1,
      "creator": "kbasetest",
      "mod": "KBase Search",
      "parent_data": {
        "domain": "Bacteria",
        "scientific_name": "'Nostoc azollae' 0708",
        "taxonomy": "Bacteria; Cyanobacteria; Nostocales; Nostocaceae; Trichormus; 'Nostoc azollae' 0708"
      },
      "data": {
        "aliases": ["Aazo_0443", "Aazo_0443"],
        "function": "Ribosomal protein S12p Asp88 (E. coli) methylthiotransferase (EC 2.8.4.4)",
        "id": "kb|g.2231.peg.5834",
        "location": [
          ["kb|g.2231.c.0", 456225, "-", 1254]
        ],
        "protein_translation": "MLGLLVEAGYGVDTNDELADYVIVNTCSFIEAAREESVKTLVELAEANKKVVITGCLAQHFQEQLLEELPEALAVIGTGDYHKIVNVIERVEQGERVKQITPQPTYIADETTPRYRTTTEGVAYLRVAEGCDYRCAFCIIPHLRGNQRSRTIESIVAEAKQLASQGVKEIILISQITTNYGLDIYGKPKLAELLCALGKVDVPWIRMHYAYPTGLTPDVIAAIQEIPNVLPYLDLPLQHSHPEILRAMNRPWQGRVNDTIIESIKTALPSAVLRTTFIVGFPGETQEHFEHLLEFTERHEFDHVGVFTFSPEEGTPAYNLLNQLPQELMVERRDQLMALQQPISLLKNQQEVDKIVDVLIEQENPESGELIGRSGRFSPEVDGQVYVKGDAGLGTIVPVKIHSADAYDLYGQIIMSN",  # noqa
        "type": "CDS"
      },
      "key_props": {
        "feature_type": "CDS",
        "strand": "-",
        "aliases": "Aazo_0443, Aazo_0443",
        "genome_domain": "Bacteria",
        "stop": "456225",
        "ontology_terms": "",
        "function": "Ribosomal protein S12p Asp88 (E. coli) methylthiotransferase (EC 2.8.4.4)",
        "start": "454972",
        "genome_scientific_name": "'Nostoc azollae' 0708",
        "contig_id": "kb|g.2231.c.0",
        "id": "kb|g.2231.peg.5834",
        "genome_taxonomy": "Bacteria; Cyanobacteria; Nostocales; Nostocaceae; Trichormus; 'Nostoc azollae' 0708"
      },
      "highlight": {
        "function": ["Ribosomal protein S12p Asp88 (E. <em>coli</em>) methylthiotransferase (EC 2.8.4.4)"]
      }
    }],
    "total": 28138389,
    "search_time": 3183,
    "access_groups_info": {
      "4258": [4258, "KBasePublicGenomesV5", "kbasetest", "2017-02-02T06:31:09+0000", 36987, "n", "r", "unlocked", {}]
    }
  }]
}

# Basic ecoli search example with all metadtaa
search_request6 = {
    "params": [{
        "match_filter": {
            "full_text_in_all": "coli",
            "exclude_subobjects": 1,
            "source_tags": ["refdata", "noindex"],
            "source_tags_blacklist": 1
        },
        "pagination": {
            "start": 0,
            "count": 20
        },
        "post_processing": {
            "ids_only": 0,
            "skip_info": 0,
            "skip_keys": 0,
            "skip_data": 0,
            "include_highlight": 1,
            "add_narrative_info": 1
        },
        "access_filter": {
            "with_private": 1,
            "with_public": 1
        },
        "sorting_rules": [{
            "is_object_property": 0,
            "property": "access_group_id",
            "ascending": 0
        }, {
            "is_object_property": 0,
            "property": "type",
            "ascending": 1
        }]
    }],
    "method": "KBaseSearchEngine.search_objects",
    "version": "1.1",
    "id": "4564119057768642"
}
