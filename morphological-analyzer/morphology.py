import sys
import copy

if len(sys.argv) != 4:
    print('Wrong arguments.')
    exit()

dictionary_file = sys.argv[1]
rules_file = sys.argv[2]
test_file = sys.argv[3]

with open(dictionary_file, 'r') as f:
    dictionary_stream = f.readlines()
    dictionary_stream = [x.strip() for x in dictionary_stream]
    dictionary_stream = [item.split() for item in dictionary_stream]
    # remove trailing lines
    dictionary_stream = list(filter(None, dictionary_stream))
with open(rules_file, 'r') as f:
    rules_stream = f.readlines()
    rules_stream = [x.strip() for x in rules_stream]
    rules_stream = [item.split() for item in rules_stream]
    rules_stream = list(filter(None, rules_stream))
with open(test_file, 'r') as f:
    test_stream = f.readlines()
    test_stream = [x.strip() for x in test_stream]
    test_stream = list(filter(None, test_stream))

dicts = []
for item in dictionary_stream:
    dict_item = {
        "word": item[0],
        "POS": item[1],
        "ROOT": None if len(item) == 2 else item[3]
    }
    dicts.append(dict_item)
newer_dicts = copy.copy(dicts)

rules = []
for item in rules_stream:
    rule_item = {
        "pos": item[0],
        "char": item[1],
        "replacement": item[2] if item[2] != '-' else None,
        "original": item[3],
        "derived": item[5]
    }
    rules.append(rule_item)

test = test_stream


def main():
    results = []
    for index, word in enumerate(test):
        POS_list = POS_lookup(word, dicts)
        if len(POS_list) != 0:
            for POS in POS_list:
                root = word if dicts[POS[0]
                                     ]['ROOT'] is None else dicts[POS[0]]['ROOT']
                results.append(word + ' ' + POS[1] + ' ' +
                               'ROOT=' + root + ' ' + 'SOURCE=dictionary')
        else:
            morphology_match(word, rules)
            for rule in rules:
                if rule['pos'] == 'SUFFIX' and word.lower().endswith(
                        rule['char']):
                    derived_word = word[:-len(rule['char'])] + (
                        '' if rule["replacement"] is None else rule["replacement"])
                    POS_list = POS_lookup(derived_word, newer_dicts)
                    if len(POS_list) != 0:
                        for POS in POS_list:
                            if rule['original'] == POS[1]:
                                root = derived_word if newer_dicts[POS[0]
                                                                   ]['ROOT'] is None else newer_dicts[POS[0]]['ROOT']
                                results.append(
                                    word +
                                    ' ' +
                                    rule["derived"] +
                                    ' ' +
                                    'ROOT=' +
                                    root +
                                    ' ' +
                                    'SOURCE=morphology')
                if rule['pos'] == 'PREFIX' and word.lower(
                ).startswith(rule['char']):
                    derived_word = (
                        '' if rule["replacement"] is None else rule["replacement"]) + word[len(rule['char']):]
                    POS_list = POS_lookup(derived_word, newer_dicts)
                    if len(POS_list) != 0:
                        for POS in POS_list:
                            if rule['original'] == POS[1]:
                                root = derived_word if newer_dicts[POS[0]
                                                                   ]['ROOT'] is None else newer_dicts[POS[0]]['ROOT']
                                results.append(
                                    word +
                                    ' ' +
                                    rule["derived"] +
                                    ' ' +
                                    'ROOT=' +
                                    root +
                                    ' ' +
                                    'SOURCE=morphology')

        matched_words = [x.split()[0] for x in results]
        if word not in matched_words:
            results.append(word + ' noun ROOT=' + word + ' SOURCE=default')
        if index != len(test) - 1:
            # print a blank line between each word's definitions
            results.append(str(index))

    results = list(dict.fromkeys(results))  # remove duplicates
    for result in results:
        print() if result.isnumeric() else print(result)


def POS_lookup(word, dicts):
    results = []
    dicts_words = [d['word'] for d in dicts]
    for index, dicts_word in enumerate(dicts_words):
        if word.lower() == dicts_word.lower():
            results.append((index, dicts[index]['POS']))
    return results


def morphology_match(word, rules):
    for rule in rules:
        if rule['pos'] == 'SUFFIX' and word.lower().endswith(rule['char']):
            derived_word = word[:-len(rule['char'])] + (
                '' if rule["replacement"] is None else rule["replacement"])
            POS_list = POS_lookup(derived_word, newer_dicts)
            if len(POS_list) != 0:
                for POS in POS_list:
                    if rule['original'] == POS[1]:
                        root = derived_word if newer_dicts[POS[0]
                                                           ]['ROOT'] is None else newer_dicts[POS[0]]['ROOT']
                        newer_dicts.append(
                            {'word': word,
                             'POS': rule["derived"],
                             "ROOT": root})
            else:
                morphology_match(derived_word, rules)
        if rule['pos'] == 'PREFIX' and word.lower().startswith(rule['char']):
            derived_word = (
                '' if rule["replacement"] is None else rule["replacement"]) + word[len(rule['char']):]
            POS_list = POS_lookup(derived_word, newer_dicts)
            if len(POS_list) != 0:
                for POS in POS_list:
                    if rule['original'] == POS[1]:
                        root = derived_word if newer_dicts[POS[0]
                                                           ]['ROOT'] is None else newer_dicts[POS[0]]['ROOT']
                        newer_dicts.append(
                            {'word': word,
                             'POS': rule["derived"],
                             "ROOT": root})
            else:
                morphology_match(derived_word, rules)


if __name__ == '__main__':
    main()
