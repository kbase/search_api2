search api changes
----------

### Local developer notes
Added local developer setup notes in `docs` to describe how I was able to best work on this repo

### Filtering by type

Filtering by type was implemented as a match on the object type field (`obj_type_name`), but this does not work in all usage cases. E.g. in the Narrative public data search tool, the search specifies the "Genome" type and sorting by scientific name. Since scientific name is not implemented across indexes, ES throws an error.

The solution is that the `object_types` search param is used to specify indexes to include in the search. The mapping from KBase workspace type to ES index alias is already present in the index spec repo.

I believe this was the technique used i search1.

### Highlighting

Both the query and processing of highlight results needed changes to work correctly. It is possible that these changes were made necessary in the transition from ES 5.5 to 7.5. In any case, it works now.

In addition, highlighting no longer overwrites field values in the search results. This suffers three problems -

- the search ui requires highlights returned separately because it displays a highlight sections separate from the object info.
- the highlight mechanism can truncate fields - we don't want to truncate the object info.
- not all matched and included in the highlight are included in the object info displauy; we want to ensure that all reasons for matching an object are available in highlights

	
### Rich(er) user info

For narrative info (when requested) the owner is augmented with profile information. In this iteration, it is just the owner's real name. Support was added for the user profile (config, simple client.)

### Fix narrative info

The narrative summary (`access_group_narrative_info`) was incorrect (it returned narratives not referenced in the reslts). This was fixed (it was a simple ES query issue)

### Fix workspace info

The workspace info (`access_groups_info`) returned was incomplete. The entire workspace info tuple is now returned.

### Travis 

Travis tests were not working when I initially pushed up changes. There was simply a missing dependency (yaml).

### Work on v2 of some methods

The `search_objects` and `search_types` methods apis are a bit awkward. Part of the reason for that is now three sets of devs working on them, making inconsistent changes. Streamlined versions of those (`search_objects2` and `search_types2`) were developed for use with the search ui. They work, but have not been integrated into the ui search tool, so further changes may be necessary.