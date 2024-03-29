from keras.models import Model
from keras.layers import LSTM, Dense, Input, Embedding
from keras.preprocessing.sequence import pad_sequences
from keras.optimizers import Adam, RMSprop
from keras.callbacks import ModelCheckpoint
from sklearn.model_selection import train_test_split
from collections import Counter
import nltk
nltk.download('punkt')
import numpy as np
import pandas as pd
import re
import json

# Define default value
BATCH_SIZE = 32
NUM_EPOCHS = 35
HIDDEN_UNITS = 256
MAX_INPUT_SEQ_LENGTH = 17
MAX_TARGET_SEQ_LENGTH = 24
MAX_VOCAB_SIZE = 2000

# load data
with open('Q1.csv', 'r', encoding='utf8') as f:
    questions = f.read().split('\n')

with open('Q2.csv', 'r', encoding='utf8') as f:
    answers = f.read().split('\n')

""" 1. count frequency of the word
        input_counter, target_counter
    2. create list of tokenized sentence
        input_texts, target_texts
"""
# Counter = dictionry for counting
input_counter = Counter()
target_counter = Counter()

# list of tokenized sentence
input_texts = []
target_texts = []

# count frequency of the word in QUESTION
prev_words = []
for line in questions:
  next_words = [w.lower() for w in nltk.word_tokenize(line)]
  if len(next_words) > MAX_INPUT_SEQ_LENGTH:
    next_words = next_words[0:MAX_INPUT_SEQ_LENGTH]

  if len(prev_words) > 0:
    input_texts.append(prev_words)
    for w in prev_words:
      input_counter[w] += 1

  prev_words = next_words

prev_words = []
for line in answers:
    next_words = [w.lower() for w in nltk.word_tokenize(line)]
    if len(next_words) > MAX_TARGET_SEQ_LENGTH:
        next_words = next_words[0:MAX_TARGET_SEQ_LENGTH]

    if len(prev_words) > 0:
        target_words = next_words[:]
        target_words.insert(0, '<SOS>')
        target_words.append('<EOS>')
        for w in target_words:
            target_counter[w] += 1
        target_texts.append(target_words)

    prev_words = next_words

"""
  convert word to index only the most 'MAX_VOCAB_SIZE' frequency word
"""

input_word2idx = {}
target_word2idx = {}
for idx, word in enumerate(input_counter.most_common(MAX_VOCAB_SIZE)):
    input_word2idx[word[0]] = idx + 2 # 0 for padding, 1 for unknown

input_word2idx['<PAD>'] = 0
input_word2idx['<UNK>'] = 1


for idx, word in enumerate(target_counter.most_common(MAX_VOCAB_SIZE)):
    target_word2idx[word[0]] = idx + 1 # 0 for unknown

target_word2idx['<UNK>'] = 0

"""
  convert index back to word
"""

input_idx2word = dict([(idx, word) for word, idx in input_word2idx.items()])
target_idx2word = dict([(idx, word) for word, idx in target_word2idx.items()])

num_encoder_tokens = len(input_idx2word)
num_decoder_tokens = len(target_idx2word)

"""
  Save word-index converter for later use
"""
np.save('word-input-word2idx.npy', input_word2idx)
np.save('word-input-idx2word.npy', input_idx2word)
np.save('word-target-word2idx.npy', target_word2idx)
np.save('word-target-idx2word.npy', target_idx2word)

encoder_input_data = []

encoder_max_seq_length = 0
decoder_max_seq_length = 0

for input_words, target_words in zip(input_texts, target_texts):
    encoder_input_wids = []
    for w in input_words:
        w2idx = 1  # default [UNK]
        if w in input_word2idx:
            w2idx = input_word2idx[w]
        encoder_input_wids.append(w2idx)

    encoder_input_data.append(encoder_input_wids)
    encoder_max_seq_length = max(len(encoder_input_wids), encoder_max_seq_length)
    decoder_max_seq_length = max(len(target_words), decoder_max_seq_length)

context = dict()
context['num_encoder_tokens'] = num_encoder_tokens
context['num_decoder_tokens'] = num_decoder_tokens
context['encoder_max_seq_length'] = encoder_max_seq_length
context['decoder_max_seq_length'] = decoder_max_seq_length

np.save('word-context.npy', context)

def generate_batch(input_data, output_text_data):
    """
      Generate more data by pad_sequence (some input data is to short, which is less than encoder_max_seq_lenght)
      Data set is too small, generate bactch is needed

      return input, output (for model training .fit_generator)
    """
    num_batches = len(input_data) // BATCH_SIZE
    while True:
        for batchIdx in range(0, num_batches):
            start = batchIdx * BATCH_SIZE
            end = (batchIdx + 1) * BATCH_SIZE
            encoder_input_data_batch = pad_sequences(input_data[start:end], encoder_max_seq_length)
            decoder_target_data_batch = np.zeros(shape=(BATCH_SIZE, decoder_max_seq_length, num_decoder_tokens))
            decoder_input_data_batch = np.zeros(shape=(BATCH_SIZE, decoder_max_seq_length, num_decoder_tokens))

            # input data is already in index
            # ouput data is not an index yet, convert word to index for label (output)
            #    - decoder input
            #    - decoder output
            for lineIdx, target_words in enumerate(output_text_data[start:end]):
                for idx, w in enumerate(target_words):
                    w2idx = 0  # default [UNK]
                    if w in target_word2idx:
                        w2idx = target_word2idx[w]
                    decoder_input_data_batch[lineIdx, idx, w2idx] = 1
                    if idx > 0:
                        decoder_target_data_batch[lineIdx, idx - 1, w2idx] = 1
            yield [encoder_input_data_batch, decoder_input_data_batch], decoder_target_data_batch

# input
encoder_inputs = Input(shape=(None,), name='encoder_inputs')
# embedding ~ one hot for word
encoder_embedding = Embedding(input_dim=num_encoder_tokens, output_dim=HIDDEN_UNITS,
                              input_length=encoder_max_seq_length, name='encoder_embedding')
encoder_lstm = LSTM(units=HIDDEN_UNITS, return_state=True, name='encoder_lstm')
encoder_outputs, encoder_state_h, encoder_state_c = encoder_lstm(encoder_embedding(encoder_inputs))
encoder_states = [encoder_state_h, encoder_state_c]

decoder_inputs = Input(shape=(None, num_decoder_tokens), name='decoder_inputs')
decoder_lstm = LSTM(units=HIDDEN_UNITS, return_state=True, return_sequences=True, name='decoder_lstm')
# use encoder_states as a initial_state
decoder_outputs, decoder_state_h, decoder_state_c = decoder_lstm(decoder_inputs,
                                                                 initial_state=encoder_states)

# output
decoder_dense = Dense(units=num_decoder_tokens, activation='softmax', name='decoder_dense')
decoder_outputs = decoder_dense(decoder_outputs)

model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

# early stopping for overfitting problem
# because the dataset is very small 
from keras.callbacks import EarlyStopping
callback = EarlyStopping(monitor='val_loss', patience=2)

# perplexity
from keras.losses import categorical_crossentropy
from keras import backend as K
import math

def ppx(y_true, y_pred):
    loss = categorical_crossentropy(y_true, y_pred)
    perplexity = K.cast(K.pow(math.e, K.mean(loss, axis=-1)), K.floatx())
    return perplexity

optimizer = Adam(lr=0.005)
model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=[ppx])

X_train, X_test, y_train, y_test = train_test_split(encoder_input_data, target_texts, test_size=0.05, random_state=42)

print("X train: " , len(X_train))
print("X test: ", len(X_test))

train_gen = generate_batch(X_train, y_train)
test_gen = generate_batch(X_test, y_test)

train_num_batches = len(X_train) // BATCH_SIZE
test_num_batches = len(X_test) // BATCH_SIZE

# checkpoint = ModelCheckpoint(filepath=WEIGHT_FILE_PATH, save_best_only=True)
model.fit_generator(generator=train_gen, steps_per_epoch=train_num_batches,
                    epochs=NUM_EPOCHS,
                    verbose=1, validation_data=test_gen, validation_steps=test_num_batches, callbacks=[callback])

encoder_model = Model(encoder_inputs, encoder_states)
encoder_model.save('encoder-weights.h5')

new_decoder_inputs = Input(batch_shape=(1, None, num_decoder_tokens), name='new_decoder_inputs')
new_decoder_lstm = LSTM(units=HIDDEN_UNITS, return_state=True, return_sequences=True, name='new_decoder_lstm', stateful=True)
new_decoder_outputs, _, _ = new_decoder_lstm(new_decoder_inputs)
new_decoder_dense = Dense(units=num_decoder_tokens, activation='softmax', name='new_decoder_dense')
new_decoder_outputs = new_decoder_dense(new_decoder_outputs)
new_decoder_lstm.set_weights(decoder_lstm.get_weights())
new_decoder_dense.set_weights(decoder_dense.get_weights())

new_decoder_model = Model(new_decoder_inputs, new_decoder_outputs)

new_decoder_model.save('decoder-weights.h5')
