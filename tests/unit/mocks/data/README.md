Data for mocks

Generally all mock described herein uses a query for "Prochlorococcus marinus str. GP2". For search_objects and search_types, a query generated by the data-search ui was used as the basis. For get_objects a hand-crafted query was created with the same post_processing.

Each case includes the initial request, the params, the elasticsearch result, the prepared result, and the api response.

All test data is in JSON, stored in *.json files.

Each test data file is located in a directory named after the service, and for the api, a subdirectory for the method.

Data files use the naming convention <case>-<usage>.json, where <case> is 'case-01', 'case-02', etc., and usage is one of 'request', 'params', 'result', or 'response'. 

case-01: A default public + private search, with all post processing additions enabled, no result parts disabled, via the data-search interface with search query for "Prochlorococcus marinus str. GP2".

case-02: Designed for get_objects, using the ids returned by case-01.