from bs4 import BeautifulSoup
import shelve
import os, re

file_exists = os.path.exists("words.shelve")

word_store = shelve.open("words.shelve")

if not file_exists:
    word_store['*']=0


stop_words = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could",
    "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes",
    "her", "here", "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im",
    "ive", "if", "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shant", "she", "shed", "shell", "shes", "should", "shouldnt",
    "so", "some", "such", "than", "that", "thats", "the", "their", "theirs", "them", "themselves", "then", "there",
    "theres", "these", "they", "theyd", "theyll", "theyre", "theyve", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasnt", "we", "wed", "well", "were", "weve", "were", "werent",
    "what", "whats", "when", "whens", "where", "wheres", "which", "while", "who", "whos", "whom", "why", "whys",
    "with", "wont", "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your", "yours", "yourself",
    "yourselves"
}

def getWords(soup, limit = 50):
    text = soup.get_text(separator=" ", strip=True).lower()
    english_text = re.sub(r"[^a-z\s]", "", text)
    words = text.split()

    words = [word for word in words if len(word) > 2]


    num_words = len(words)
    if num_words < limit:
        return 0

    for word in words:
        if word in stop_words:
            continue
        if word in word_store:
            word_store[word] += 1
        else:
            word_store[word] = 1

    if num_words > word_store['*']:
        word_store['*'] = num_words

    return num_words
