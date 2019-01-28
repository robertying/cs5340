import os

dataset_dir = './developset'

with open('all-inputfile.txt', 'w') as all_input:
    all_input.write(dataset_dir+'\n')
    with open('all-stories.answers', 'w') as all_answers:
        for _file in os.listdir(dataset_dir):
            if _file.endswith('.answers'):
                with open(os.path.join(dataset_dir, _file), 'r') as f:
                    answers_stream = f.read()
                    all_answers.write(answers_stream)
                    all_input.write(_file[:-8]+'\n')
