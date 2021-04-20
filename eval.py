from __future__ import absolute_import, division, print_function

import argparse
import csv
import logging
import os
import sys

import numpy as np
import torch
from torch.utils.data import (DataLoader, SequentialSampler,
                              TensorDataset)
from tqdm import tqdm

from transformers import BertTokenizer, BertForSequenceClassification

from utils import convert_examples_new, convert_dataset_to_features
from dataset import HumorDetectionDataset
from model import HumorDetectionModel

from sklearn.metrics import f1_score, precision_score, recall_score

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class InputExample(object):
    """A single training/test example for simple sequence classification."""

    def __init__(self, guid, text_a, text_b=None, label=None):
        """Constructs a InputExample.

        Args:
            guid: Unique id for the example.
            text_a: string. The untokenized text of the first sequence. For single
            sequence tasks, only this sequence must be specified.
            text_b: (Optional) string. The untokenized text of the second sequence.
            Only must be specified for sequence pair tasks.
            label: (Optional) string. The label of the example. This should be
            specified for train and dev examples, but not for test examples.
        """
        self.guid = guid
        self.text_a = text_a
        self.text_b = text_b
        self.label = label


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, input_ids, input_mask, segment_ids, label_id):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_id = label_id


class DataProcessor(object):
    """Base class for data converters for sequence classification data sets."""

    def get_train_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the train set."""
        raise NotImplementedError()

    def get_dev_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the dev set."""
        raise NotImplementedError()

    def get_labels(self):
        """Gets the list of labels for this data set."""
        raise NotImplementedError()

    @classmethod
    def _read_tsv(cls, input_file, quotechar=None):
        """Reads a tab separated value file."""
        with open(input_file, "r") as f:
            reader = csv.reader(f, delimiter=",", quotechar=quotechar)
            lines = []
            for line in reader:
                if sys.version_info[0] == 2:
                    line = list(unicode(cell, 'utf-8') for cell in line)
                lines.append(line)
            return lines


class DumbProcessorClean(DataProcessor):
    def get_train_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "train_clean.tsv")), "train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "dev_clean.tsv")), "dev")

    def get_labels(self):
        """See base class."""
        return ["0", "1"]

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text_a = line[3]
            label = line[1]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
        return examples


class DumbProcessor(DataProcessor):
    """Processor for the MRPC data set (GLUE version)."""

    def get_train_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "train_wordnet_amb.tsv")), "train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "dev_wordnet_amb.tsv")), "dev")

    def get_labels(self):
        """See base class."""
        return ["0", "1"]

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text_a = line[3]
            label = line[1]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
        return examples


class MnliProcessor(DataProcessor):
    """Processor for the MultiNLI data set (GLUE version)."""

    def get_train_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "dev_matched.tsv")),
            "dev_matched")

    def get_labels(self):
        """See base class."""
        return ["contradiction", "entailment", "neutral"]

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            if i == 0:
                continue
            guid = "%s-%s" % (set_type, line[0])
            text_a = line[8]
            text_b = line[9]
            label = line[-1]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
        return examples


class ColaProcessor(DataProcessor):
    """Processor for the CoLA data set (GLUE version)."""

    def get_train_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "dev.tsv")), "dev")

    def get_labels(self):
        """See base class."""
        return ["0", "1"]

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text_a = line[3]
            label = line[1]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
        return examples


class Sst2Processor(DataProcessor):
    """Processor for the SST-2 data set (GLUE version)."""

    def get_train_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "dev.tsv")), "dev")

    def get_labels(self):
        """See base class."""
        return ["0", "1"]

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            if i == 0:
                continue
            guid = "%s-%s" % (set_type, i)
            text_a = line[0]
            label = line[1]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
        return examples


def load_and_cache_examples(args, tokenizer, ambiguity_fn, task_name):
    '''
    Loads in a cached file for training and/or builds a cached file for this data

    :return:
    '''
    processors = {
        "old": ColaProcessor,
        "new_clean": DumbProcessorClean,
        "new": DumbProcessor
    }

    # Build the dataset
    task = 'test'

    logger.info("Creating features from dataset file at %s", args.data_dir)

    if args.old_load:
        logger.info('using old data features')

        processor = processors[task_name]()
        label_list = processor.get_labels()

        if not evaluate:
            examples = processor.get_train_examples(args.data_dir)
        else:
            examples = processor.get_dev_examples(args.data_dir)

        features = convert_examples_new(examples, label_list, args.max_seq_length, tokenizer)

        input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        input_masks = torch.tensor([f.input_mask for f in features], dtype=torch.long)
        token_type_ids = torch.tensor([f.segment_ids for f in features], dtype=torch.long)
        labels = torch.tensor([f.label_id for f in features], dtype=torch.long)

        dataset = TensorDataset(input_ids, input_masks, token_type_ids, labels)

    else:
        logger.info("creating features from new dataset")

        dataset = HumorDetectionDataset(args.data_dir, args.max_seq_length, task, ambiguity_fn,
                                        args.use_clean_data)
        features = convert_dataset_to_features(dataset, args.max_seq_length, tokenizer)

        # convert features to tensor dataset
        input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        input_masks = torch.tensor([f.input_mask for f in features], dtype=torch.long)
        token_type_ids = torch.tensor([f.segment_ids for f in features], dtype=torch.long)
        ambiguity_scores = torch.tensor([f.ambiguity for f in features], dtype=torch.long)
        labels = torch.tensor([f.label_id for f in features], dtype=torch.long)

        dataset = TensorDataset(input_ids, input_masks, token_type_ids, labels, ambiguity_scores)

    logger.info("Features Built.")
    return dataset


def accuracy(out, labels):
    outputs = np.argmax(out, axis=1)
    return np.sum(outputs == labels)


def get_metrics(logits, labels):
    # import pdb;pdb.set_trace()
    outputs = np.argmax(logits, axis=1)
    f1 = f1_score(labels, outputs)
    prec = precision_score(labels, outputs)
    recall = recall_score(labels, outputs)
    return f1, prec, recall


def evaluate(args, model, tokenizer, ambiguity_fn, task_name):
    eval_data = load_and_cache_examples(args, tokenizer, ambiguity_fn, task_name)

    logger.info("***** Running evaluation *****")
    logger.info("  Num examples = %d", len(eval_data))
    logger.info("  Batch size = %d", args.eval_batch_size)

    # Run prediction for full data
    eval_sampler = SequentialSampler(eval_data)
    eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=args.eval_batch_size)

    model.eval()
    eval_loss, eval_accuracy = 0, 0
    nb_eval_steps, nb_eval_examples = 0, 0
    full_logits = None
    full_labels = None

    for batch in tqdm(eval_dataloader, desc="Evaluating"):
        batch = tuple(t.to(args.device) for t in batch)

        inputs = {'input_ids': batch[0],
                  'token_type_ids': batch[2],
                  'attention_mask': batch[1],
                  'labels': batch[3]}

        if "baseline_" not in args.data_dir:
            inputs['ambiguity_scores'] = batch[4]

        with torch.no_grad():
            outputs = model(**inputs)
            tmp_eval_loss, logits = outputs[:2]

        logits = logits.detach().cpu().numpy()
        label_ids = inputs['labels'].to('cpu').numpy()

        # combine the labels for F1 scores
        if full_labels is None:
            full_labels = label_ids
        else:
            full_labels = np.append(full_labels, label_ids, axis=0)

        if full_logits is None:
            full_logits = logits
        else:
            full_logits = np.append(full_logits, logits, axis=0)

        tmp_eval_accuracy = accuracy(logits, label_ids)

        eval_loss += tmp_eval_loss.mean().item()
        eval_accuracy += tmp_eval_accuracy

        nb_eval_examples += inputs['input_ids'].size(0)
        nb_eval_steps += 1

    eval_f1, eval_precision, eval_recall = get_metrics(full_logits, full_labels)
    full_accuracy = accuracy(full_logits, full_labels)

    eval_loss = eval_loss / nb_eval_steps
    eval_accuracy = eval_accuracy / nb_eval_examples

    # TODO: could return precision and recall here
    return eval_loss, eval_accuracy, eval_f1


def main():
    parser = argparse.ArgumentParser()

    # Required parameters
    parser.add_argument("--data_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="The input data dir. Should contain the .tsv files (or other data files) for the task.")
    parser.add_argument("--bert_model", default=None, type=str, required=True,
                        help="Bert pre-trained model selected in the list: bert-base-uncased, "
                             "bert-large-uncased, bert-base-cased, bert-large-cased, bert-base-multilingual-uncased, "
                             "bert-base-multilingual-cased, bert-base-chinese.")

    # Other parameters
    parser.add_argument("--cache_dir",
                        default="",
                        type=str,
                        help="Where do you want to store the pre-trained models downloaded from s3")
    parser.add_argument("--max_seq_length",
                        default=128,
                        type=int,
                        help="The maximum total input sequence length after WordPiece tokenization. \n"
                             "Sequences longer than this will be truncated, and sequences shorter \n"
                             "than this will be padded.")
    parser.add_argument("--do_lower_case",
                        action='store_true',
                        help="Set this flag if you are using an uncased model.")
    parser.add_argument("--train_batch_size",
                        default=16,
                        type=int,
                        help="Total batch size for training.")
    parser.add_argument("--eval_batch_size",
                        default=8,
                        type=int,
                        help="Total batch size for eval.")
    parser.add_argument("--no_cuda",
                        action='store_true',
                        help="Whether not to use CUDA when available")
    parser.add_argument("--local_rank",
                        type=int,
                        default=-1,
                        help="local_rank for distributed training on gpus")
    parser.add_argument('--old_load', action='store_true')
    parser.add_argument('--fp16',
                        action='store_true',
                        help="Whether to use 16-bit float precision instead of 32-bit")
    parser.add_argument('--loss_scale',
                        type=float, default=0,
                        help="Loss scaling to improve fp16 numeric stability. Only used when fp16 set to True.\n"
                             "0 (default value): dynamic loss scaling.\n"
                             "Positive power of 2: static loss scaling value.\n")
    parser.add_argument("--overwrite_cache", action='store_true')
    parser.add_argument('--use_clean_data', action='store_true', default=False,
                        help='Whether to use clean data.')
    parser.add_argument('--bert_base', action='store_true', default=False,
                        help='loads in bert-base instead of our custom model.')
    parser.add_argument('--model_weights', required=True, help="Path to model weights, if loading a saved model. "
                        "If you wish to evaluate multiple models, separate with commas (no spaces). "
                        "Models must differ ONLY in random seed and/or ambiguity_fn.")
    args = parser.parse_args()

    args.device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    args.n_gpu = torch.cuda.device_count()

    logger.info("device: {} n_gpu: {}, distributed training: {}, 16-bits training: {}".format(
        args.device, args.n_gpu, bool(args.local_rank != -1), args.fp16))

    tokenizer = BertTokenizer.from_pretrained(args.bert_model, do_lower_case=args.do_lower_case)
    ambiguity_fn = "none"
    if "_csi_" in args.model_weights:
        ambiguity_fn = "csi"
    elif "_wn_" in args.model_weights:
        ambiguity_fn = "wn"
    elif "_tf-idf_" in args.model_weights:
        ambiguity_fn = "tf-idf"
    task_name = "old"
    if "new_clean" in args.model_weights:
        task_name = "new_clean"
    elif "new" in args.model_weights:
        task_name = "new"
    if args.bert_base:
        model = BertForSequenceClassification.from_pretrained(args.bert_model, num_labels=2).to(args.device)
    else:
        use_ambiguity = ambiguity_fn != "none"
        model = HumorDetectionModel(rnn_size=768, use_ambiguity=use_ambiguity).to(args.device)
    for weights_path in args.model_weights.split(","):
        state_dict = torch.load(weights_path)
        model.load_state_dict(state_dict)
        print(f"Evaluating model: {weights_path}")
        eval_loss, eval_accuracy, eval_f1 = evaluate(args, model, tokenizer, ambiguity_fn, task_name)
        print(f"Loss: {eval_loss}")
        print(f"Accuracy: {eval_accuracy}")
        print(f"F1 {eval_f1}")


if __name__ == "__main__":
    main()
