import hashlib
import re

def is_dupe(simhash1, simhash2, threshold=10):
    return hamming_distance(simhash1, simhash2) < threshold

def create_hash(token):
    return int(hashlib.md5(token.encode()).hexdigest(), 16) & ((1 << 64) - 1)

def compute_simhash(soup):
    text = soup.get_text(separator=' ', strip=True)
    english_text = re.sub(r"[^a-z\s]", "", text)
    words = english_text.lower().split()
    tokens=[]
    for i in range(len(words)-1):
        token = words[i] + ' ' + words[i+1]  
        tokens.append(token)

    vector = [0] * 64
    
    for token in tokens:
        token_hash = create_hash(token)  # Get 64-bit hash
        for i in range(64):
            bit = (token_hash >> i) & 1
            if bit:
                vector[i] += 1  # Weighted by frequency
            else:
                vector[i] -= 1
    
    simhash = 0
    for i, v in enumerate(vector):
        if v > 0:
            simhash |= (1 << i)
    return simhash

def hamming_distance(hash1, hash2):
    x = hash1 ^ hash2
    return bin(x).count('1')  # Count differing bits