import sys

if len(sys.argv) != 3 and len(sys.argv) != 4:
    print('Wrong arguments.')
    exit()

pcfg_file = sys.argv[1]
sentences_file = sys.argv[2]

if len(sys.argv) == 4 and sys.argv[3] == '-prob':
    prob = True
elif len(sys.argv) == 3:
    prob = False
else:
    print('Wrong arguments.')
    exit()

with open(pcfg_file, 'r') as f:
    pcfg_stream = f.readlines()
pcfg_stream = [x.strip() for x in pcfg_stream]
pcfg_stream = [item.split() for item in pcfg_stream]
# remove trailing lines
pcfg_stream = list(filter(None, pcfg_stream))

pcfg = []
for item in pcfg_stream:
    if len(item) == 5:
        pcfg_item = {
            "left": item[0],
            "right1": item[2],
            "right2": item[3],
            "prob": float(item[4])
        }
    else:
        pcfg_item = {
            "left": item[0],
            "right": item[2],
            "prob": float(item[3])
        }
    pcfg.append(pcfg_item)

with open(sentences_file, 'r') as f:
    sentences_stream = f.readlines()
sentences_stream = [x.strip() for x in sentences_stream]
sentences_stream = [item.split() for item in sentences_stream]
# remove trailing lines
sentences = list(filter(None, sentences_stream))


def main():
    for sentence in sentences:
        N = len(sentence)
        result = parse_prob(sentence) if prob else parse(sentence)

        print("PARSING SENTENCE: " + ' '.join(sentence))
        if prob:
            print("NUMBER OF PARSES FOUND: " +
                  str(1 if 'S' in result[0][N - 1] else 0))
            print("TABLE:")
            for i in range(N):
                for j in range(i, N):
                    POS_probs = []
                    for pos, pprob in sorted(result[i][j].items()):
                        POS_probs.append(
                            "{0}({1:.4f})".format(pos, round(pprob, 4)))
                    if len(POS_probs) == 0:
                        print("cell[{},{}]: {}".format(
                            i + 1, j + 1, '-'))
                    else:
                        print("cell[{},{}]: {}".format(
                            i + 1, j + 1, ' '.join(POS_probs)))
        else:
            print("NUMBER OF PARSES FOUND: " +
                  str(result[0][N - 1].count('S')))
            print("TABLE:")
            for i in range(N):
                for j in range(i, N):
                    if len(result[i][j]) == 0:
                        print("cell[{},{}]: {}".format(
                            i + 1, j + 1, '-'))
                    else:
                        print("cell[{},{}]: {}".format(
                            i + 1, j + 1, ' '.join(sorted(result[i][j]))))
        print()


def lookup_terminal(word):
    return [(x["left"], x["prob"]) for x in list(
        filter(lambda x: "right" in x and x["right"] == word, pcfg))]


def lookup_nonterminal(POS_1, POS_2):
    return [(x["left"], x["prob"]) for x in list(filter(
        lambda x: "right1" in x and x["right1"] == POS_1 and x["right2"] == POS_2, pcfg))]


def parse(sentence):
    # index starts with 0
    N = len(sentence)
    t = [[[] for x in range(N)] for y in range(N)]
    for c in range(N):
        results_1 = lookup_terminal(sentence[c])
        for result_1 in results_1:
            t[c][c].append(result_1[0])
        for r in reversed(range(c)):
            for s in range(r + 1, c + 1):
                for B in t[r][s - 1]:
                    for C in t[s][c]:
                        results_2 = lookup_nonterminal(B, C)
                        for result_2 in results_2:
                            t[r][c].append(result_2[0])
    return t


def parse_prob(sentence):
    # index starts with 0
    N = len(sentence)
    t = [[{} for x in range(N)] for y in range(N)]
    for c in range(N):
        results_1 = lookup_terminal(sentence[c])
        for result_1 in results_1:
            t[c][c][result_1[0]] = result_1[1]
        for r in reversed(range(c)):
            for s in range(r + 1, c + 1):
                for B in t[r][s - 1]:
                    for C in t[s][c]:
                        results_2 = lookup_nonterminal(B, C)
                        for result_2 in results_2:
                            t[r][c][result_2[0]] = max(
                                t[r][c][result_2[0]] if result_2[0] in t[r][c] else 0, result_2[1] * t[r][s - 1][B] * t[s][c][C])
    return t


if __name__ == "__main__":
    main()
