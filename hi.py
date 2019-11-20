import numpy as np

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
    correctLastNames.add(lname.strip())
lastN.close()

for fname in maleFn:
    correctFirstNames.add(fname.strip())
maleFn.close()

for fname in femaleFn:
    correctFirstNames.add(fname.strip())
femaleFn.close()

for line in corruptedN:
    try:
        corruptedLastName, corruptedFirstName = line.strip().split(" ")
        corruptedFL.append( [corruptedFirstName, corruptedLastName] )
    except:
        print("Ignoring invalid name: " + line.strip())
        print()

corruptedN.close()

for line in generatedN:
    LastName, FirstName = line.strip().split(" ")
    groundTruth.add( (FirstName, LastName) )
generatedN.close()


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
    code = name[0]
    name = name.replace(name[0],"",1)
    name = name[0:3]

    for char in name:
        code += soundex_dict[char]

    for i in range(len(code), 3):
        code += "0"

    return code


def jaccardify(w):
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


# SETUP
print("preprocessing ... ")
correctFirstNamesSoundex = [soundexify(name) for name in correctFirstNames]
correctLastNamesSoundex = [soundexify(name) for name in correctLastNames]

corruptedFLSoundex = [[soundexify(n[0]), soundexify(n[1])] for n in corruptedFL]

correctFirstNamesJaccard = [jaccardify(name) for name in correctFirstNames]
correctLastNamesJaccard = [jaccardify(name) for name in correctLastNames]

corruptedFLJaccard = [[jaccardify(n[0]), jaccardify(n[1])] for n in corruptedFL]
print("Done!\n")


def firstNames(method):
    if method == "hamming" : return correctFirstNames
    if method == "leven"   : return correctFirstNames
    if method == "soundex" : return correctFirstNamesSoundex
    if method == "jaccard" : return correctFirstNamesJaccard
    raise Exception("Bad input: {}".format(method))


def lastNames(method):
    if method == "hamming" : return correctLastNames
    if method == "leven"   : return correctLastNames
    if method == "soundex" : return correctLastNamesSoundex
    if method == "jaccard" : return correctLastNamesJaccard
    raise Exception("Bad input: {}".format(method))


def fl_list(method):
    if method == "hamming" : return corruptedFL
    if method == "leven"   : return corruptedFL
    if method == "soundex" : return corruptedFLSoundex
    if method == "jaccard" : return corruptedFLJaccard
    raise Exception("Bad input: {}".format(method))


def best_candidate(fl, method):
    """
    Returns
    ( argmin_{x in FN} dist(x, fl[0]), argmin_{x in LN} dist(x, fl[1]) )
    """
    if fl[0] in correctFirstNames:
        FirstN = fl[0]
    else:
        distFn = ((x, dist(x, fl[0], method)) for x in firstNames(method))
        FirstN = min(distFn, key=lambda x : x[1])[0]

    if fl[1] in correctLastNames:
        LastN = fl[1]
    else:
        distLn = ((x, dist(x, fl[1], method)) for x in lastNames(method))
        LastN = min(distLn, key=lambda x : x[1])[0]

    return FirstN, LastN

def dist(x, y, method):
    if method == "hamming":
        dist = abs( len(x) - len(y) ) # e.g. dist(Rik, Travis) = 3, dist(bob, dan) = 0
        short = x if len(x) <= len(y) else y

        long_ = {x,y} - {short}
        if long_:
            long_ = list(long_)[0]
        else:
            return 0 # both names are equal

        for i in range(dist):
            short += "#" # Travis, Rik -> Travis, Rik###

        score = 0
        for i in range(len(long_)):
            if short[i] != long_[i]:
                score += 1

        return score

    if method == "soundex":
        return int(x == y)

    if method == "leven":
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
        Jxy = len(x & y) / len(x | y)
        return 1 - Jxy

# CLEAN UP

fixed = []
methods = ["hamming", "soundex", "leven", "jaccard"]
#methods = ["soundex", "hamming", "leven", "jaccard"]

for method in methods:
    print("Using the " + method + " method ...")

    fixed_with_method = set() #removes duplicates

    list_ = fl_list(method)

    i = 0
    for fl in list_:
        i+=1
        fixedF, fixedL = best_candidate(fl, method)
        fixed_with_method.add( (fixedL, fixedF) )
        if i % 200 == 0:
            print(str(round(i / len(corruptedFL) * 100,2)) + " %")

    fixed.append(fixed_with_method)

for i in [0,1,2,3]:
    f = open(methods[i] + ".txt", "w+")
    list_ = list(fixed[i])
    for lf in list_:
        f.write(lf[0] + " " + lf[1] + "\n")
    f.close()

    print("True Positive Rate using method " + method[i])
    tpr = len(fixed[i] & groundTruth) / len(groundTruth)
    print(tpr)
