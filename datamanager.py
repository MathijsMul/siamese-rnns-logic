from __future__ import print_function, division
import os
import torch
import numpy as np
from torch.utils.data import Dataset
import re
import pickle
import nltk
import textwrap
import io
import random

class SentencePairsDataset(Dataset):
    """
    sentence pairs dataset
    """

    def __init__(self, data_file):

        self.data_file = data_file
        self.tree_data = []
        self.word_list = []
        self.relation_list = []
        self.separator_char = '\t'

    def __len__(self):
        return len(self.tree_data)

    def __str__(self):
        return(str(self.tree_data))

    def load_data(self, sequential, print_result=False):
        """
        read data from file and convert to required tree format, to be stored in self.tree_data
        """

        print('Loading data from ', self.data_file)

        if sequential:
            # sequential data loading
            with open(self.data_file, 'r') as f:
                sentences = []
                relset = set()
                wordset = set()
                for line in f:
                    relation, s1, s2 = line.split(self.separator_char)
                    relation = relation.strip()  # remove initial/ending whitespace
                    relset = relset.union({relation})

                    t1 = s1.split()
                    t2 = s2.split()

                    sentences += [t1, t2]
                    self.tree_data += [(relation, t1, t2)]

                    wordset = wordset.union(set(t1))
                    wordset = wordset.union(set(t2))

                self.relation_list = sorted(relset)
                self.word_list = sorted(wordset)

        else:
            # recursive data loading (preserving tree structures), from Michael Repplinger
            with open(self.data_file, 'r') as f:
                trees = []
                relset = set()
                wordset = set()
                for line in f:
                    relation, s1, s2  = line.split(self.separator_char)
                    relation = relation.strip() # remove initial/ending whitespace
                    relset = relset.union({relation})

                    s1 = re.sub(r"([^()\s]+)", r"(. \1)", s1)
                    s2 = re.sub(r"([^()\s]+)", r"(. \1)", s2)
                    t1 = nltk.tree.Tree.fromstring(re.sub(r"\( ", r"(cps ", s1))
                    t2 = nltk.tree.Tree.fromstring(re.sub(r"\( ", r"(cps ", s2))

                    trees += [t1, t2]
                    self.tree_data += [(relation, t1, t2)]

                    wordset = wordset.union(set(t1.leaves()))
                    wordset = wordset.union(set(t2.leaves()))

                self.relation_list = sorted(relset)
                self.word_list = sorted(wordset)

        if print_result:
            print("Vocabulary: \n", self.word_list)
            print("Relations:  \n", self.relation_list)

# this class is necessary because the built-in pytorch DataLoader class doesn't work for the tree-shaped data
class BatchData():
    def __init__(self, unbatched_data, batch_size, shuffle):
        self.unbatched_data = unbatched_data.tree_data
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_samples = len(unbatched_data)
        self.batched_data = []
        self.batched_labels = []
        self.num_batches = 0

    def create_batches(self):
        if self.shuffle:
            random.shuffle(self.unbatched_data)

        # start index of last batch
        last_idx = self.num_samples - (self.num_samples % self.batch_size)

        # case where all batches are full
        if last_idx == self.num_samples:
            last_idx -= self.batch_size

        for start_idx in range(0, last_idx + 1, self.batch_size):
            if start_idx == last_idx:
                # last, possibly incomplete batch
                batch_data = [[sample[1], sample[2]] for sample in self.unbatched_data[start_idx : self.num_samples]]
                batch_labels = [sample[0] for sample in self.unbatched_data[start_idx : self.num_samples]]
            else:
                batch_data = [[sample[1], sample[2]] for sample in self.unbatched_data[start_idx : start_idx + self.batch_size]]
                batch_labels = [sample[0] for sample in self.unbatched_data[start_idx : start_idx + self.batch_size]]

            self.batched_data.append(batch_data)
            self.batched_labels.append(batch_labels)

            self.num_batches += 1

