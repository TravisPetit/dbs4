import numpy as np

# LOAD DATA

corruptedN  = open("corruptedNames.txt","r")
femaleFn    = open("femaleFirstnames.txt","r")
maleFn      = open("maleFirstnames.txt","r")
lastN       = open("lastnames.txt", "r")
generatedN  = open("generatedNames.txt", "r")

correctLastNames  = set()
correctFirstNames = set()
corrupedFL = [] #first and last names
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
        corrupedFL.append( [corruptedFirstName, corruptedLastName] )
    except:
        print("Ignoring invalid name: " + line.strip())
corruptedN.close()

for line in generatedN:
    LastName, FirstName = line.strip().split(" ")
    groundTruth.add( (FirstName, LastName) )
generatedN.close()


# FUNCTIONS

soundex_dict = {
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


def fix(fl, method):
    """
    fl = [FirstName, Lastname]
    method = hamming | soundex | leven | jaccard
    """
    bc = best_candidate(fl, method)
    return bc

def best_candidate(fl, method):
    """
    Returns
    ( argmin_{x in FN} dist(x, fl[0]), argmin_{x in LN} dist(x, fl[1]) )
    """
    distFn = [(x, dist(x, fl[0], method)) for x in correctFirstNames]
    distFn.sort(key=lambda s: s[1], reverse=True)

    distLn = [(x, dist(x, fl[1], method)) for x in correctLastNames]
    distLn.sort(key=lambda s: s[1], reverse=True)

    return distFn[0][0], distLn[0][0]

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
        xcode = x[0]
        ycode = y[0]

        x_ = x.replace(x[0],"", 1)
        y_ = y.replace(y[0],"", 1)

        replaceme = ["A","E","I","O","U","Y","H","W"]

        for char in replaceme:
            x_ = x_.replace(char, "")
            y_ = y_.replace(char, "")

        x_ = x_[0:3]
        y_ = y_[0:3]

        for char in x_:
            xcode += soundex_dict[char]

        for char in y_:
            ycode += soundex_dict[char]

        for i in range(len(x_), 3):
            xcode += "0"
            #x_ += "#"

        for i in range(len(y_), 3):
            ycode += "0"
            #y_ += "#"

        #print(xcode, ycode)

        return int(xcode == ycode)

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
        def trigrams(w):
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

        tri_x = trigrams(x)
        tri_y = trigrams(y)

        Jxy = len(tri_x & tri_y) / len(tri_x | tri_y)

        return 1 - Jxy

# CLEAN UP

fixed = []
methods = ["hamming", "soundex", "leven", "jaccard"]
for method in methods:
    print("Using the " + method + " method ...")

    fixed_with_method = set() #removes duplicates
    for fl in corrupedFL:
        fixedF, fixedL = fix(fl, method)
        fixed_with_method.add( (fixedL, fixedF) )

    fixed.append(fixed_with_method)

for i in [0,1,2,3]:
    f = open(methods[i] + ".txt", "w+")
    list_ = list(fixed[i])
    for lf in list_:
        f.write(lf[0] + " " + lf[1] + "\n")
    f.close()

    print("True Positive Rate using method " + method[i])
    tpr = len(fixed[i] & groundTruth) / len(groundTruth)
    print(trp)
