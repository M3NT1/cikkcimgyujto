import sqlite3
from gensim import corpora, models
from textblob import TextBlob
from collections import Counter

# Egyszerű magyar stopszavak lista
HUNGARIAN_STOP_WORDS = set(
    ['a', 'az', 'és', 'hogy', 'nem', 'ez', 'van', 'volt', 'egy', 'de', 'is', 'aki', 'ami', 'amely', 'meg', 'fel', 'ki',
     'be', 'le', 'el', 'át', 'rá', 'te', 'mi', 'ti', 'ők', 'én', 'ő', 'olyan', 'ilyen', 'csak', 'így', 'úgy', 'vagy',
     'illetve', 'azaz', 'tehát', 'mint', 'akkor', 'ha', 'mert', 'pedig', 'után', 'szerint', 'között', 'alatt'])


def get_titles_from_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT title FROM articles")
    titles = [row[0] for row in c.fetchall()]
    conn.close()
    return titles


def preprocess_text(text):
    words = text.lower().split()
    return [word for word in words if word.isalnum() and word not in HUNGARIAN_STOP_WORDS]


def topic_modeling(titles, num_topics=5):
    preprocessed_titles = [preprocess_text(title) for title in titles]
    dictionary = corpora.Dictionary(preprocessed_titles)
    corpus = [dictionary.doc2bow(text) for text in preprocessed_titles]

    lda_model = models.LdaMulticore(corpus=corpus, id2word=dictionary, num_topics=num_topics)

    return lda_model, dictionary, corpus


def analyze_sentiment(text):
    return TextBlob(text).sentiment.polarity


def analyze_titles(db_path):
    titles = get_titles_from_db(db_path)

    # Témamodellezés
    lda_model, dictionary, corpus = topic_modeling(titles)

    # Témák és hangulatok elemzése
    topic_sentiments = {i: [] for i in range(lda_model.num_topics)}
    topic_frequencies = Counter()

    for i, title in enumerate(titles):
        # Téma azonosítása
        bow = dictionary.doc2bow(preprocess_text(title))
        topic_distribution = lda_model.get_document_topics(bow)
        main_topic = max(topic_distribution, key=lambda x: x[1])[0]

        # Hangulat elemzése
        sentiment = analyze_sentiment(title)

        # Adatok gyűjtése
        topic_sentiments[main_topic].append(sentiment)
        topic_frequencies[main_topic] += 1

    # Eredmények összesítése
    results = []
    for topic_id in range(lda_model.num_topics):
        topic_words = lda_model.show_topic(topic_id, topn=5)
        avg_sentiment = sum(topic_sentiments[topic_id]) / len(topic_sentiments[topic_id]) if topic_sentiments[
            topic_id] else 0
        frequency = topic_frequencies[topic_id]

        results.append({
            'topic_id': topic_id,
            'top_words': [word for word, _ in topic_words],
            'avg_sentiment': avg_sentiment,
            'frequency': frequency
        })

    return results
