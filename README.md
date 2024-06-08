# CoNEXT-2024
This repository contains code and data used in the article: Identification of Route Validation Policies in RPKI.

**Datasets Used**
  - AS-relationship: [CAIDA AS Relationships Dataset](https://www.caida.org/catalog/datasets/as-relationships/). <provided on 12-16-2023>
  - BGP dump: BGP data was obtained from the [Route Views](https://www.routeviews.org/routeviews/) e [RIPE RIS](https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris/) platforms through the [BGPStream](https://bgpstream.caida.org/docs) tool.
  - Results: Classification results can be obtained in the [data](https://github.com/MarcelHMendes/rov-inference/blob/master/data/) directory and visualized through the [website](https://homepages.dcc.ufmg.br/~marcelmendes/medicao_1/).

**Experiment Configuration**

The announcements were made through the [PEERING](https://peering.ee.columbia.edu/) platform between December 15 and 30, 2023.

| Prefixes | ROAs | 
|--------|--------|
| 204.9.170.0/24 | short for BadSite, long for GoodSite, no ROA | 
| 138.185.228.0/24 | short for BadSite, no ROA |
| 138.185.231.0/24 | long for GoodSite, no ROA |
| 138.185.229.0/24 | short for BadSite, INVALID |
| 138.185.230.0/24 | short and INVALID for BadSite, long and VALID for GoodSite |
