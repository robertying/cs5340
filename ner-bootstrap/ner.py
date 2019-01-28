import sys
from operator import itemgetter

if len(sys.argv) != 4:
    print('Wrong arguments.')
    exit()

seed_rules_file = sys.argv[1]
training_data_file = sys.argv[2]
test_data_file = sys.argv[3]

with open(seed_rules_file, 'r') as f:
    seed_rules_stream = f.readlines()
    seed_rules_stream = [x.strip() for x in seed_rules_stream]
    seed_rules_stream = [item.split() for item in seed_rules_stream]
    # remove trailing lines
    seed_rules_stream = list(filter(None, seed_rules_stream))
with open(training_data_file, 'r') as f:
    training_data_stream = f.readlines()
    training_data_stream = [x.strip() for x in training_data_stream]
    training_data_stream = list(filter(None, training_data_stream))
with open(test_data_file, 'r') as f:
    test_data_stream = f.readlines()
    test_data_stream = [x.strip() for x in test_data_stream]
    test_data_stream = list(filter(None, test_data_stream))

seed_rules = []
for rule in seed_rules_stream:
    seed_rules.append({
        "type": rule[0],
        "contains": rule[1][rule[1].find("(")+1:rule[1].find(")")],
        "class": rule[3]
    })

train_data = []
for i in range(0, len(training_data_stream), 2):
    train_data.append({
        "context": training_data_stream[i][9:],
        "NP": training_data_stream[i+1][4:]
    })

test_data = []
for i in range(0, len(test_data_stream), 2):
    test_data.append({
        "context": test_data_stream[i][9:],
        "NP": test_data_stream[i+1][4:]
    })


def main():
    print("SEED DECISION LIST")
    print('')
    print_list(seed_rules)
    print('')

    spelling_list = seed_rules.copy()
    context_list = []
    N = 2
    iteration = 3

    for i in range(iteration):
        labeled_instances = apply(spelling_list, train_data)
        tmp_context_list = induce_list(
            "CONTEXT", labeled_instances, context_list)
        best_context_list = get_best_rules(tmp_context_list, N)
        print("ITERATION #"+str(i+1)+": NEW CONTEXT RULES")
        print('')
        print_list(best_context_list)
        print('')
        context_list = context_list + best_context_list

        labeled_instances = apply(context_list, train_data)
        tmp_spelling_list = induce_list(
            "SPELLING", labeled_instances, spelling_list)
        best_spelling_list = get_best_rules(tmp_spelling_list, N)
        print("ITERATION #"+str(i+1)+": NEW SPELLING RULES")
        print('')
        print_list(best_spelling_list)
        print('')
        spelling_list = spelling_list + best_spelling_list

    final_list = create_final_list(spelling_list, context_list)
    print("FINAL DECISION LIST")
    print('')
    print_list(final_list)
    print('')

    test_labeled_list = apply_all(final_list, test_data)
    print("APPLYING FINAL DECISION LIST TO TEST INSTANCES")
    for item in test_labeled_list:
        print('')
        print("CONTEXT: "+item["context"])
        print("NP: "+item["NP"])
        print("CLASS: "+item["class"] if 'class' in item else "NONE")


def apply(rules, instances):
    labeled_instances = []

    for instance in instances:
        for rule in rules:
            if rule["type"] == "SPELLING" and rule["contains"] in instance["NP"].split(' '):
                labeled_instances.append({
                    "context": instance["context"],
                    "NP": instance["NP"],
                    "class": rule["class"]
                })
                break
            if rule["type"] == "CONTEXT" and rule["contains"] in instance["context"].split(' '):
                labeled_instances.append({
                    "context": instance["context"],
                    "NP": instance["NP"],
                    "class": rule["class"]
                })
                break

    return labeled_instances


def apply_all(rules, instances):
    labeled_instances = []

    for instance in instances:
        flag = False
        for rule in rules:
            if rule["type"] == "SPELLING" and rule["contains"] in instance["NP"].split(' '):
                labeled_instances.append({
                    "context": instance["context"],
                    "NP": instance["NP"],
                    "class": rule["class"]
                })
                flag = True
                break
            if rule["type"] == "CONTEXT" and rule["contains"] in instance["context"].split(' '):
                labeled_instances.append({
                    "context": instance["context"],
                    "NP": instance["NP"],
                    "class": rule["class"]
                })
                flag = True
                break
        if not flag:
            labeled_instances.append({
                "context": instance["context"],
                "NP": instance["NP"],
                "class": "NONE"
            })

    return labeled_instances


def induce_list(type, labeled_instances, _seed_rules):
    rules = []
    tmp_list = []
    freqs = []
    plain_seed_rules = [{
        "type": rule["type"],
        "contains":rule["contains"],
        "class":rule["class"]
    } for rule in _seed_rules]

    for instance in labeled_instances:
        strings = instance["context" if type == "CONTEXT" else "NP"]
        for string in strings.split(' '):
            rule = {
                "type": type,
                "contains": string
            }
            if rule in rules:
                index = rules.index(rule)
                freqs[index][instance["class"]
                             ] = freqs[index][instance["class"]] + 1
            else:
                freqs.append({
                    "LOCATION": 1 if instance["class"] == "LOCATION" else 0,
                    "ORGANIZATION": 1 if instance["class"] == "ORGANIZATION" else 0,
                    "PERSON": 1 if instance["class"] == "PERSON" else 0
                })
                rules.append(rule)

    for index, rule in enumerate(rules):
        freq = freqs[index]
        _sum = freq["LOCATION"]+freq["ORGANIZATION"]+freq["PERSON"]
        for _class in freq:
            prob = freq[_class]/_sum
            if _sum >= 5 and prob >= 0.8:
                rule["freq"] = _sum
                rule["prob"] = prob
                rule["class"] = _class

                _rule = dict(rule)
                del _rule["freq"], _rule["prob"]
                if _rule not in plain_seed_rules:
                    tmp_list.append(rule)

    return tmp_list


def sort_list(rules):
    s = sorted(rules, key=itemgetter('contains'))
    s = sorted(s, key=itemgetter('freq'), reverse=True)
    return sorted(s, key=itemgetter('prob'), reverse=True)


def get_best_rules(rules, num):
    location_list = [rule for rule in rules if rule["class"] == "LOCATION"]
    organization_list = [
        rule for rule in rules if rule["class"] == "ORGANIZATION"]
    person_list = [rule for rule in rules if rule["class"] == "PERSON"]

    s = sort_list(location_list)[
        :2] + sort_list(organization_list)[:2] + sort_list(person_list)[:2]
    return sort_list(s)


def create_final_list(spelling_list, context_list):
    return spelling_list + context_list


def print_list(rules):
    for rule in rules:
        prob = -1 if "prob" not in rule else rule["prob"]
        freq = -1 if "freq" not in rule else rule["freq"]
        print(rule["type"]+' '+"Contains("+rule["contains"]+") -> " +
              rule["class"]+" (prob="+"{0:.3f}".format(round(prob, 3))+" ; freq="+str(freq)+')')


if __name__ == "__main__":
    main()
