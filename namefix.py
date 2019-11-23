import numpy as np
import time

print("Preprocessing ... ")

soundex_dict = {
    "A" : "",
    "E" : "",
    "I" : "",
    "O" : "",
    "U" : "",
    "Y" : "",
    "H" : "",
    "W" : "",
    "B" : "1",
    "F" : "1",
    "P" : "1",
    "V" : "1",
    "C" : "2",
    "G" : "2",
    "J" : "2",
    "K" : "2",
    "Q" : "2",
    "S" : "2",
    "X" : "2",
    "Z" : "2",
    "D" : "3",
    "T" : "3",
    "L" : "4",
    "M" : "5",
    "N" : "5",
    "R" : "6"
}

def soundexify(name):
    """
    Returns the soundex code of a word
    e.g. soundexify("Rupert") = "R163"
    """
    code = name[0]
    name = name.replace(name[0],"",1)
    name = name[0:3]

    for char in name:
        code += soundex_dict[char]

    for i in range(len(code), 3):
        code += "0"

    return code


def jaccardify(w):
    """
    Returns the trigrams of a word as a set
    e.g. jaccardify("abc") = {##a, #ab, abc, bc#, ##c}
    """
    trigrams = set()
    for i in range(len(w)):
        tmp = ""
        for j in [i-2, i-1, i]:
            if j < 0:
                tmp += "#"
            else:
                tmp += w[j]
        trigrams.add(tmp)
        trigrams.add(tmp)

    try:
        trigrams.add(w[-2] + w[-1] + "#")
        trigrams.add(w[-1] + "##")
    except:
        pass

    return trigrams


class word:
    def __init__(self, w):
        self.w = w
        self.soundex = soundexify(w)
        self.trigrams = jaccardify(w)

    def __repr__(self):
        return self.w

    def __str__(self):
        return self.w

# LOAD DATA

corruptedN  = open("corruptedNames.txt","r")
femaleFn    = open("femaleFirstnames.txt","r")
maleFn      = open("maleFirstnames.txt","r")
lastN       = open("lastnames.txt", "r")
generatedN  = open("generatedNames.txt", "r")

correctLastNames  = set()
correctFirstNames = set()
corruptedFL = [] #first and last names
groundTruth = set()

for lname in lastN:
    correctLastNames.add(word(lname.strip()))
lastN.close()

for fname in maleFn:
    correctFirstNames.add(word(fname.strip()))
maleFn.close()

for fname in femaleFn:
    correctFirstNames.add(word(fname.strip()))
femaleFn.close()

for line in corruptedN:
    try:
        corruptedLastName, corruptedFirstName = line.strip().split(" ")
        corruptedFL.append( [word(corruptedFirstName), word(corruptedLastName)] )
    except:
        print("\tIgnoring invalid name: " + line.strip())

corruptedN.close()

for line in generatedN:
    LastName, FirstName = line.strip().split(" ")
    groundTruth.add( (FirstName, LastName) )
generatedN.close()

print("Done!\n")

def best_candidate(fl, method):
    """
    Returns
    argmin_{x in FN} dist(x, fl[0]) and
    argmin_{x in LN} dist(x, fl[1])

    where
    fl = [firstname, lastname]
    """
    if fl[0] in correctFirstNames:
        FirstN = fl[0].w
    else:
        distFn = ((x.w, dist(x, fl[0], method)) for x in correctFirstNames)
        FirstN = min(distFn, key=lambda x : x[1])[0]

    if fl[1] in correctLastNames:
        LastN = fl[1].w
    else:
        distLn = ((x.w, dist(x, fl[1], method)) for x in correctLastNames)
        LastN = min(distLn, key=lambda x : x[1])[0]

    return FirstN, LastN

def dist(x, y, method):
    if method == "hamming":
        x, y = x.w, y.w

        short = x if len(x) <= len(y) else y
        long_ = x if len(x) >  len(y) else y

        for i in range(len(short), len(long_)):
            short += "#"

        score = 0

        for ch1, ch2 in zip(x, y):
            if ch1 != ch2:
                score += 1
        return score

    if method == "soundex":
        return int(x.soundex == y.soundex)

    if method == "leven":
        x, y = x.w, y.w
        # from https://stackabuse.com/levenshtein-distance-and-text-similarity-in-python/
        size_x = len(x) + 1
        size_y = len(y) + 1
        matrix = np.zeros ((size_x, size_y))
        for i in range(size_x):
            matrix [i, 0] = i
        for i in range(size_y):
            matrix [0, i] = i

        for i in range(1, size_x):
            for j in range(1, size_y):
                if x[i-1] == y[j-1]:
                    matrix [i,j] = min(
                        matrix[i-1, j] + 1,
                        matrix[i-1, j-1],
                        matrix[i, j-1] + 1
                    )
                else:
                    matrix [i,j] = min(
                        matrix[i-1,j] + 1,
                        matrix[i-1,j-1] + 1,
                        matrix[i,j-1] + 1
                    )
        return (matrix[size_x - 1, size_y - 1])

    if method == "jaccard":
        Jxy = len(x.trigrams & y.trigrams) / len(x.trigrams | y.trigrams)
        return 1 - Jxy

    if method == "w_sum":
        w_hamming = 0.2
        w_soundex = 0.2
        w_jaccard = 0.2
        w_leven   = 0.4
        return w_hamming * dist(x,y,"hamming") +\
               w_jaccard * dist(x,y,"jaccard") +\
               w_soundex * dist(x,y,"soundex") +\
               w_leven   * dist(x,y,"leven")

# CLEAN UP

fixed = []
#methods = ["hamming", "soundex", "leven", "jaccard", "w_sum"]
methods = ["hamming", "soundex", "leven", "jaccard"]

start = time.time()
for method in methods:
    print("Using the " + method + " method ...")

    fixed_with_method = set() #removes duplicates

    i = 0
    for fl in corruptedFL:
        i+=1
        fixedF, fixedL = best_candidate(fl, method)
        fixed_with_method.add( (fixedL, fixedF) )

        if i % (5 * 2720) == 0:
            print(str(round(i / len(corruptedFL) * 100,2)) + " %")

    fixed.append(fixed_with_method)

for i in range(len(methods)):
    f = open(methods[i] + ".txt", "w+")
    list_ = list(fixed[i])
    for lf in list_:
        f.write(lf[0] + " " + lf[1] + "\n")
    f.close()

    print("True Positive Rate using method " + methods[i])
    tpr = len(fixed[i] & groundTruth) / len(groundTruth)
    print(tpr)

end = time.time()
time_elapsed = end - start
time_elapsed /= 60 # minutes

print("Time time elapsed: {} minutes ".format(time_elapsed))
