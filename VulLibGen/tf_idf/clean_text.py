import re

# Try to load NLTK stopwords, fallback to basic list if unavailable
try:
    from nltk.corpus import stopwords
    stopwds = stopwords.words('english')
except (LookupError, OSError):
    # Fallback: basic English stopwords list
    stopwds = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
               "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
               'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
               'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
               'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were',
               'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
               'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
               'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
               'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
               'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
               'once']


def expand_apostrophe(string):
    pat_is = re.compile("(it|he|she|that|this|there|here)(\'s)", re.I)
    pat_s = re.compile("(?<=[a-zA-Z])\'s")
    pat_s2 = re.compile("(?<=s)\'s?")
    pat_not = re.compile("(?<=[a-zA-Z])\'t")
    pat_would = re.compile("(?<=[a-zA-Z])\'d")
    pat_will = re.compile("(?<=[a-zA-Z])\'ll")
    pat_am = re.compile("(?<=[I|i])\'m")
    pat_are = re.compile("(?<=[a-zA-Z])\'re")
    pat_ve = re.compile("(?<=[a-zA-Z])\'ve")

    text = pat_is.sub(r"\1 is", string)
    text = re.sub(r"won't", "will not", text)
    text = pat_s.sub("", text)
    text = pat_s2.sub("", text)
    text = pat_not.sub(" not", text)
    text = pat_would.sub(" would", text)
    text = pat_will.sub(" will", text)
    text = pat_am.sub(" am", text)
    text = pat_are.sub(" are", text)
    text = pat_ve.sub(" have", text)
    text = text.replace('\'', ' ')
    return text


def remove_stopwords(tokens):
    return [w for w in tokens if not (w in stopwds)]


def cleaned_text(text):
    text = expand_apostrophe(text)
    text = re.sub(u'[^a-zA-Z]', ' ', text)
    tokens = text.lower().strip().split()
    rmstw_tokens = remove_stopwords(tokens)
    return rmstw_tokens