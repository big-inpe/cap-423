# CAP-423 - Ciência de Dados Geoespaciais

## Projeto

Este projeto tem como objetivo criar uma base de dados com informações extraídas das imagens de satélite disponíveis no INPE através de técnicas de IA para possibilitar a recuperação por conteúdo.

Nesta primeira etapa, quatro classes (ou "alvos") foram escolhidas para se extrair das imagens: cicatriz de queimadas, pivôs, área de agricultura e estradas. Este repositório guarda dados referentes especificamente à etapa de reconhecimento de vias. 

## Sub-projeto

A seguir algumas informações básicas a respeito do problema e estratégias utilizadas.

### Características do problema

As imagens serão do sensor [MSI](https://sentiwiki.copernicus.eu/web/s2-mission#S2Mission-MSIInstrumentS2-Mission-MSI-Instrumenttrue) do satélite [Sentinel-2](https://sentiwiki.copernicus.eu/web/s2-mission]), portanto tem-se à disposição bandas tanto no espectro visível (RGB) quanto fora (NIR, SWIR, etc.), com imagens variando entre 10m a 20 de resolução espacial e tempo de revisita de 5 dias (em média).

A classe abordada aqui é "estrada". Esta classe pode ser sub-dividida em duas: estradas asfaltadas e não-asfaltadas. Referente a estradas asfaltadas, a base de dados OpenStreetMap é uma fonte relativamente confiável, portanto para a extração desta categoria basta um cruzamento de dados. A classe estradas não-asfaltadas apresenta um desafio maior, uma vez que podem aparecer em lugares remotos e repentinamente, o que torna a base OpenStreetMap (entre outras) não confiável.

Deve-se notar que qualquer análise deve ser reprodutível, uma vez que se pretende implementar em um dataflow maior.

### Estratégias utilizada

Foram testadas 3 estratégias, utilizando técnicas tanto clássicas quanto de IA.

#### Extração de contornos e análise de linearidade

A estratégia geral aqui é extrair as feições de estradas o melhor possível para posterior utilização do algoritmo de Hough, "limpando" os contornos não lineares. 

- Pré-processamento:
  - conversão de imagens RGB para escala de cinza.
  - cálculo do índice NDVI (Normalized Difference Vegetation Index) para ajudar a distinguir vegetação.
- Detecção de Bordas:
  - utilização do método de detecção de bordas Canny com ajustes nos parâmetros para diferentes níveis de separação (nenhuma, moderada e alta).
  - análise visual para selecionar os melhores parâmetros.
- Transformação de Hough:
  - configuração de parâmetros para identificar feições lineares, como estradas, após a aplicação dos detectores de bordas.
- Análise de Índices Específicos:
  - uso do índice BSI (Bare Soil Index) para realçar áreas não vegetadas, possivelmente relacionadas a estradas ou clareiras.

O primeiro problema encontrado é a qualidade da máscara de contornos. A maior parte das estradas são delineadas, entretanto nem todas e não só estradas, o que por sí só mina o resultado da transformação de Hough. 

### Transformações morfológicas e limiarização adaptativa

Para o segundo experimento, o fluxo combina segmentação, morfologia, detecção de bordas e análise de linearidade para identificar estradas rurais em imagens. O artigo base encontra-se [aqui](https://ieeexplore.ieee.org/document/8274890). Segue racional utilizado:
- Segmentação Binária:
  - segmentação da imagem em regiões potenciais de estrada e não-estrada utilizando o algoritmo de segmentação adaptativa de Otsu.
- Transformações Morfológicas:
  -aplicação de duas erosões seguidas de uma dilatação, usando um elemento estrutural retangular de tamanho 3x3, para refinar as características de estradas não estruturadas.
- Detecção de Bordas (LoG - Laplacian of Gaussian):
  - suavização da imagem dilatada com um filtro Gaussiano para reduzir ruídos.
  - aplicação de um kernel Laplaciano para detectar bordas.
- Transformada de Hough:
  - delimitação de linhas representando os limites das estradas.
  - identificação dos pontos de início e fim de cada linha detectada.

Algumas adaptações foram testadas, como suavização através de filtro Gaussiano, utilização do NDVI e transformações morfológicas antes do processo de limiarização.

### Aprendizado de Máquina
Após os experimentos acima não apresentarem bons resultados, se propôs o desenvolvimento de um modelo de Aprendizado de Máquina (AM) supervisionado. A motivação principal para se testar tal abordagem é encontrar extratores de feições ótimos para esta tarefa em específico, ao contrário de se adotar aqueles feitos à mão como Canny.

É necessário comentar que se considerou um modelo não-supervisionado, como k-means ou GMM (Gaussian Mixture Models), entretanto a resposta espectral de vias não-asfaltadas é muito parecida, senão idêntica, daquela de solo exposto. Considerando que a área de estudo se situa no bioma Cerrado (também conhecida como savana brasileira), encontrar limites ótimos dentro do espaço de atributos considerando apenas informação espectral é inviável.

Infelizmente não se encontrou dataset  de imagens do Sentinel-2 com anotações de vias, portanto nós desenvolvemos um. 

Devido à escassez de tempo, foi necessário encontrar uma base de anotações de vias já pronta, preferencialmente em formato vetorial e georreferenciado. Primeiramente se considerou a base OpenStreetMap, devido à sua abrangência espacial, entretanto logo se observou que, para vias não-asfaltadas especificamente, a base deixa muito a desejar, com o problema se agravando conforme se afasta de regiões metropolitanas. A solução encontrada foi a base desenvolvida pelo projeto [IAmazon](https://imazon.org.br/publicacoes/mapping-roads-in-the-brazilian-amazon-with-artificial-intelligence-and-sentinel-2/), o qual mapeou todas as estradas (asfaltadas e não-asfaltadas) do bioma amazônia dentro do território nacional para o ano de 2012. A área delimitada para se extrair as amostras se encontra na região de transição entre Amazônia e Cerrado, no intuito se de aproximar o máximo possível das características da região de estudo.

O processo de criação dos limites de cada amostra (aqui intitulado “frames”) se deu utilizando QGis. Foram gerados 7992 frames de 1280mx1280m, sem sobreposição. Para a extração das anotações, primeiro se converteu o dado vetorial em matricial, com pixels de via igual a 1 e 0 caso contrário. Em formato matricial, as anotações foram recortadas para cada frame. Já o recorte das imagens do Sentinel-2 se deu através do Google Earth Engine (GEE), para as datas de abril de 2017 a abril de 2018. Se utilizou de tal intervalo de tempo devido à localização adotada apresentar muita nuvem ao longo de todo o ano, portanto foi necessário processo de mosaicagem para pixels com presença de nuvem. 

Devido à discrepância entre data de anotação e captura das imagens, algumas amostras possuem vias não anotadas. 

Em resumo, foram geradas 7992 amostras, onde cada amostra é um par de imagens: as anotações em forma de máscara binária e a imagem propriamente dita com 4 bandas (vermelho, verde, azul e infravermelho próximo) e dimensão de 128x128 pixels. A base gerada pode ser baixada através deste [link](https://drive.google.com/file/d/162Mh5b9PzhjoAUXvD_zd6mCz-HyU-K78/view?usp=sharing).

A arquitetura selecionada para o modelo é aquela da U-Net, devido à sua ampla utilização em tarefas de classificação de imagens no meio do Sensoriamento Remoto. 

Se utilizou do torch para a implementação do modelo e rotinas de treinamento e teste. O código foi executado no ambiente do Colab, com acesso a uma GPU T4. O modelo foi treinado por 60 épocas com um taxa de aprendizado inicial de 0,01, decaindo 0,1 a cada 20 épocas. A função perda foi o dice e o otimizador, Adam. 

## Estrutura do repositório

O notebooks mostram os experimentos para cada estratégia delineada acima. 

O script main.py pode ser rodado direto do shell, apenas passando os argumentos como caminho da imagem de entrada e pesos. Ele recebe uma imagem e retorna a máscara binária via/outros. Note que a imagem pode ter qualquer dimensão, entretanto deve possuir quatro bandas: RGB-NIR (recomendado ser proveninente do Sentinel-2).

Os pesos dos modelo podem ser baixados através [deste link](https://drive.google.com/file/d/1Bb338jzCb6G-Y71pVQ0IdiOPdvmeZKUY/view?usp=sharing). 

Para rodar a maior parte dos script o seu ambiente precisa ter gdal instalado. Recomenda-se criar um ambiente virtual a parte (utilizar miniconda). O comando é !conda install gdal -y.
