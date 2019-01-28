import sys
import os
import spacy

if len(sys.argv) != 2:
    print('Wrong arguments.')
    exit()

input_file = sys.argv[1]


##### read file #####

with open(input_file, 'r') as f:
    input_file_stream = f.readlines()
    input_file_stream = [x.strip() for x in input_file_stream]
    input_file_stream = list(filter(None, input_file_stream))

dataset_dir = input_file_stream.pop(0)
stories_file = input_file_stream

nlp = spacy.load('en')
data = {}
for story_file in stories_file:
    with open(os.path.join(dataset_dir, story_file + ".story"), 'r') as f:
        story_stream = f.read().split('\n\n')
        story_stream = story_stream[story_stream.index('TEXT:') + 1:]
        sentences = []
        for para in story_stream:
            para = para.replace(
                '\n', ' ')
            doc = nlp(para)
            for sentence in doc.sents:
                sentences.append(sentence)
        data[story_file] = {
            "setences": sentences
        }
    with open(os.path.join(dataset_dir, story_file + ".questions"), 'r') as f:
        question_stream = f.read().split('\n\n')
        question_stream = list(filter(None, question_stream))
        ids = [question[question.find('QuestionID: ') +
                        12:question.find('Question: ') -
                        1] for question in question_stream]
        questions = [question[question.find(
            'Question: ') + 10:question.find('Difficulty') - 1] for question in question_stream]
        data[story_file]["questions"] = []
        for index, _id in enumerate(ids):
            data[story_file]["questions"].append({
                "id": _id,
                "question": nlp(questions[index])
            })


##### for text analyses #####

def get_all_noun_chunks():
    with open('noun_chunks.txt', 'w') as noun_chunks_file:
        for _file in os.listdir(dataset_dir):
            if _file.endswith('.questions'):
                with open(os.path.join(dataset_dir, _file), 'r') as f:
                    question_stream = f.read().split('\n\n')
                    question_stream = list(filter(None, question_stream))
                    questions = [question[question.find(
                        'Question: ') + 10:question.find('Difficulty') - 1] for question in question_stream]
                    for question in questions:
                        doc = nlp(question)

                        noun_chunks_file.write(question + '\n')
                        for chunk in doc.noun_chunks:
                            noun_chunks_file.write(chunk.text + ' | ')
                        noun_chunks_file.write('\n')


def get_all_whats_asked():
    with open('whats_asked.txt', 'w') as whats_asked_file:
        for _file in os.listdir(dataset_dir):
            if _file.endswith('.questions'):
                with open(os.path.join(dataset_dir, _file), 'r') as f:
                    question_stream = f.read().split('\n\n')
                    question_stream = list(filter(None, question_stream))
                    questions = [question[question.find(
                        'Question: ') + 10:question.find('Difficulty') - 1] for question in question_stream]
                    for question in questions:
                        whats_asked_file.write(
                            question + '  ' + get_whats_asked(question)[0] + '\n')


##### config #####

wh_list = ["WDT", "WP", "WP$", "WRB"]
aux_list = ["aux", "ROOT", "auxpass"]

# priority order
# what, which, how and why need to be considered separately
whats_asked_ne = {
    "who": ["PERSON", "ORG", "GPE"],
    "whose": ["PERSON", "ORG", "GPE"],
    "where": ["LOC", "FAC", "GPE", "ORG"],
    "when": ["DATE", "TIME"  # , "EVENT"
             ],
    "how often": ["DATE", "TIME"],
    "how long": ["DATE", "TIME"],
    "how old": ["CARDINAL"],
    "how much money": ["MONEY"],
    "how much": ["MONEY", "QUANTITY", "PERCENT"],
    "how many years": ["DATE", "TIME"],
    "how many": ["QUANTITY", "CARDINAL"],
    "how ": ["QUANTITY", "CARDINAL"]  # not how!
}


##### pipelines #####

def get_whats_asked(question):
    asked = ''
    rest = ''
    doc = question
    wh_index = -1
    aux_index = -1

    for index, token in enumerate(doc):
        if token.tag_ in wh_list and wh_index == -1:
            wh_index = index
        if token.dep_ in aux_list and aux_index == -1 and index > wh_index:
            aux_index = index
    if wh_index == -1:
        wh_index = 0
    if aux_index == -1:
        asked = doc[wh_index:wh_index + 1]
        rest = doc[wh_index + 1:]
    else:
        asked = doc[wh_index: aux_index]
        rest = doc[aux_index:]

    return asked, rest


def NE_match(whats_asked, sentences):
    results = []

    for key in whats_asked_ne:
        if key in whats_asked.text.lower():
            for ne_tag in whats_asked_ne[key]:
                for sentence in sentences:
                    doc = sentence
                    for ent in doc.ents:
                        if ne_tag == ent.label_:
                            results.append({
                                "answer": ent,
                                "sentence": sentence,
                                "similarity": 0,
                                "sentence_duplicate_count": 0,
                                "overlap_count": 0,
                                "head_noun_occurrences": 0,
                                "after_wh_occurrences": 0
                            })

    return results


def others_match(whats_asked, head_noun, sentences):
    results = []
    # what, which, how and why
    whats_asked_text = whats_asked.text.lower()

    if head_noun is not None and (whats_asked_text == "which"):
        for sentence in sentences:
            for chunk in sentence.noun_chunks:
                if chunk.root.dep_ == head_noun.dep_:
                    results.append({
                        "answer": chunk,
                        "sentence": sentence,
                        "similarity": 0,
                        "sentence_duplicate_count": 0,
                        "overlap_count": 0,
                        "head_noun_occurrences": 0,
                        "after_wh_occurrences": 0
                    })

    if len(results) == 0:
        for sentence in sentences:
            tokens = [
                token.text for token in sentence if token.pos_ != "PUNCT"]

            results.append({
                "answer": nlp(' '.join(tokens)),
                "sentence": sentence,
                "similarity": 0,
                "sentence_duplicate_count": 0,
                "overlap_count": 0,
                "head_noun_occurrences": 0,
                "after_wh_occurrences": 0
            })

    return results


def get_after_wh(whats_asked):
    # what city, which city -> city
    return whats_asked[1:]


def get_head_noun(rest_sentence):
    doc = rest_sentence
    for chunk in doc.noun_chunks:
        return chunk.root


def POS_match(POS, lastest_results):
    pass


def head_noun_check(answer_candidates, head_noun):
    results = []

    for candidate in answer_candidates:
        list_candidate = [token.lemma_
                          for token in candidate["sentence"]]
        candidate["head_noun_occurrences"] = list_candidate.count(
            head_noun.lemma_)
        results.append(candidate)

    return results


def after_wh_check(answer_candidates, after_wh):
    results = []

    for candidate in answer_candidates:
        list_candidate = [token.lemma_
                          for token in candidate["sentence"]]
        candidate["after_wh_occurrences"] = list_candidate.count(
            after_wh.lemma_)
        results.append(candidate)

    return results


def duplicate_check(answer_candidates):
    answers_per_sentence = {}
    results = []

    for candidate in answer_candidates:
        sentence = candidate["sentence"].text
        if sentence in answers_per_sentence:
            answers_per_sentence[sentence].append(candidate["answer"])
        else:
            answers_per_sentence[sentence] = [candidate["answer"]]

    for candidate in answer_candidates:
        sentence = candidate["sentence"].text
        candidate["sentence_duplicate_count"] = len(
            answers_per_sentence[sentence])
        results.append(candidate)

    return results


def overlap_check(answer_candidates, question):
    results = []

    for candidate in answer_candidates:
        list_candidate = [
            token.lemma_ for token in candidate["sentence"] if not token.is_stop]
        list_question = [token.lemma_
                         for token in question if not token.is_stop]
        candidate["overlap_count"] = len(
            list(set(list_candidate).intersection(list_question)))
        results.append(candidate)

    return results


def similarity_check(answer_candidates, question):
    results = []

    for candidate in answer_candidates:
        candidate["similarity"] = candidate["sentence"].similarity(question)
        results.append(candidate)

    return results


def should_merge(answer_candidates):
    if len(answer_candidates) < 2:
        return answer_candidates[0]

    if answer_candidates[0]["sentence"] == answer_candidates[1]["sentence"]:
        sentence = answer_candidates[0]["sentence"].text
        index_1 = sentence.find(answer_candidates[0]["answer"].text)
        index_2 = sentence.find(answer_candidates[1]["answer"].text)
        if index_2 - index_1 == len(answer_candidates[0]["answer"].text) + 2:
            result = {
                "answer": nlp(sentence[index_1:index_2 + len(answer_candidates[1]["answer"].text)]),
                "sentence": nlp(sentence)
            }
            return result
        elif index_1 - index_2 == len(answer_candidates[1]["answer"].text) + 2:
            result = {
                "answer": nlp(sentence[index_2:index_1 + len(answer_candidates[0]["answer"].text)]),
                "sentence": nlp(sentence)
            }
            return result

    return answer_candidates[0]


def polish_answer(answer):
    if hasattr(
            answer["answer"],
            'label_') and answer["answer"].label_ == "MONEY":
        for word in answer["sentence"].text.split(' '):
            if answer["answer"].text in word:
                answer["answer"] = word
                return answer

    answer["answer"] = answer["answer"].text.replace('-', ' ').strip()
    return answer


def write_answers(answers):
    with open('results.response', 'w') as f:
        for story_id in answers:
            for answer in answers[story_id]:
                f.write('QuestionID: ' + answer["id"] + '\n')
                f.write('Answer: ' + answer["answer"] + '\n\n')


def print_answers(answers):
    for story_id in answers:
        for answer in answers[story_id]:
            print('QuestionID: ' + answer["id"])
            print('Answer: ' + answer["answer"])
            print('')


def main():
    answers = {}
    for item in data:
        answers[item] = []
        sentences = data[item]['setences']
        questions = data[item]["questions"]

        for question in questions:
            question_doc = question['question']

            whats_asked_doc, rest_sentence = get_whats_asked(question_doc)
            head_noun = get_head_noun(rest_sentence)
            results = NE_match(whats_asked_doc, sentences)
            if len(results) == 0:
                results = others_match(whats_asked_doc, head_noun, sentences)
                after_wh = get_after_wh(whats_asked_doc)
                results = after_wh_check(results, after_wh)

            # if head_noun != None:
            #     results = head_noun_check(results, head_noun)  # ???
            results = duplicate_check(results)
            results = overlap_check(results, question_doc)
            results = similarity_check(results, question_doc)

            results.sort(
                key=lambda x: x["similarity"], reverse=True)
            # results.sort(
            #     key=lambda x: x["sentence_duplicate_count"], reverse=True)
            results.sort(
                key=lambda x: x["overlap_count"], reverse=True)
            # results.sort(
            #     key=lambda x: x["head_noun_occurrences"], reverse=True)
            # results.sort(
            #     key=lambda x: x["after_wh_occurrences"], reverse=True)

            answer = {"answer": ""}
            if len(results) != 0:
                answer = polish_answer(should_merge(results))

            answers[item].append({
                "id": question['id'],
                "answer": answer["answer"]
            })

    print_answers(answers)


if __name__ == "__main__":
    main()
