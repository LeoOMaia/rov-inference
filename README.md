# SBRC-2024
Esse repositório contêm código e dados usados na elaboração do artigo: *Identificação de Políticas de Validação de Rotas no RPKI*.

**Datasets usados**
  - AS-relationship: [CAIDA AS Relationships Dataset](https://www.caida.org/catalog/datasets/as-relationships/). <disponibilizado em 16-12-2023>
  - BGP dump: Os dados BGP foram obtidos das plataformas [Route Views](https://www.routeviews.org/routeviews/) e [RIPE RIS](https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris/) pela ferramenta [BGPStream](https://bgpstream.caida.org/docs).
  - Resultados: Os resultados das classificações podem ser obtidos no diretório [data](https://github.com/MarcelHMendes/rov-inference/blob/master/data/) e visualizados pelo [website](https://homepages.dcc.ufmg.br/~marcelmendes/medicao_1/).

**Configuração do experimento**

Os anúncios foram realizados por meio da plataforma [PEERING](https://peering.ee.columbia.edu/) entre 15 e 30 de dezembro de 2023.

| Prefixos | ROAs | 
|--------|--------|
| 204.9.170.0/24 | curta para BadSite, longa para GoodSite, sem ROA | 
| 138.185.228.0/24 | curta para BadSite, sem ROA |
| 138.185.231.0/24 | longa para GoodSite, sem ROA |
| 138.185.229.0/24 | curta para BadSite, INVÁLIDA |
| 138.185.230.0/24 | curta e INVÁLIDA para BadSite, longa e VÁLIDA para GoodSite |
