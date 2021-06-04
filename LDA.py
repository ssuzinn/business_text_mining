import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import pyLDAvis.gensim_models
from gensim import corpora
import gensim

def plot_2d_graph(vocabs, xs, ys):
    plt.figure(figsize=(20, 20))
    font_name = font_manager.FontProperties(fname='c:\\windows\\fonts\\nanumbarungothic-yethangul.ttf',
                                            ).get_name()
    rc('font', family=font_name)
    rc('font', size=15)
    plt.scatter(xs, ys, marker='o')
    for i, v in enumerate(vocabs):
        plt.annotate(v, xy=(xs[i], ys[i]))

def Token2vec(DF, mincount):
    model = Word2Vec(sentences=DF.NOUNS, min_count=mincount, workers=6, sg=0)
    word_vectors = model.wv
    pca = PCA(n_components=5)
    vocabs = list(model.wv.index_to_key)
    word_vocab_list = [model.wv[v] for v in vocabs]
    xys = pca.fit_transform(word_vocab_list)
    xs = xys[:, 0]
    ys = xys[:, 1]
    plot_2d_graph(vocabs, xs, ys)

def display_topics(model, feature_names, no_top_words):
    topics = []
    for topic_idx, topic in enumerate(model.components_):
        important_words = [feature_names[i] for i in topic.argsort()[:-no_top_words - 1:-1]]
        print( f"Topic {topic_idx}")
        print(",".join(important_words))
        topics.append(important_words)
    return topics

def TFIDF(DF):
    tfidv = TfidfVectorizer(min_df=0.01).fit(DF.corpus)
    #tfidf = TfidfVectorizer(max_features = 100, max_df=0.95, min_df=0).fit_transform(DF.corpus)# 상위 100개
    TFIDF=tfidv.transform(DF.corpus)
    #data_array = TFIDF.toarray()
    #text=tfidv.get_feature_names()
    return tfidv,TFIDF

def LDA(DF,num):
    tfidv, tfidf = TFIDF(DF)
    lda = LatentDirichletAllocation(n_components=num)
    lda.fit(tfidf)
    topic = display_topics(lda, tfidv.get_feature_names(), 20)
    return topic,lda,tfidf

def LDA_DOCS(DF,num):
    topics,model,matrix = LDA(DF,num)
    topics_df = pd.DataFrame(topics)
    topic_dist = model.transform(matrix)
    DF['topic label'] = topic_dist.argmax(1)
    DF['topic prob'] = topic_dist.max(1)
    return DF, topics_df


def GensimLDA(DF,NUM_TOPICS):
    Token = DF.NOUNS
    dictionary = corpora.Dictionary(Token)
    corpus = [dictionary.doc2bow(text) for text in Token]
    NUM_TOPICS = NUM_TOPICS  # 20개의 토픽, k=20
    ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=NUM_TOPICS, id2word=dictionary, passes=30)
    topics = ldamodel.print_topics(num_words=10)
    pyLDAvis.enable_notebook()
    vis = pyLDAvis.gensim_models.prepare(ldamodel, corpus, dictionary)
    return vis


def SNA(DF,num_words):
    from apyori import apriori
    import networkx as nx
    re = list(apriori(DF.NOUNS, min_support=0.01))
    df = pd.DataFrame(re)
    df['length'] = df['items'].apply(lambda x: len(x))
    df = df[(df.length == 2) & (df.support >= 0.01)].sort_values('support', ascending=False)
    G = nx.Graph()
    ar = list(df['items'][:num_words])
    G.add_edges_from(ar)
    pr = nx.pagerank(G)
    nsize = np.array([v for v in pr.values()])
    nsize = 2000 * (nsize - min(nsize)) / (max(nsize) - min(nsize))
    pos = nx.circular_layout('G')
    plt.figure(figsize=(16, 12))
    plt.axis('off')
    nx.draw_networkx(G, font_family='AppleGothic', font_size=15,
                     cmap=plt.cm.rainbow, node_size=nsize)
    plt.savefig('SNA.png')