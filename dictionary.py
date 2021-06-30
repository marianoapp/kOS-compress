import sys
import os.path
from collections import defaultdict, deque
from operator import itemgetter


def process(data, level, max_entries, sfx):
    # convert data to bytearray to make it mutable
    data = bytearray(data)
    # prepare data by replacing newlines with a space
    if sfx:
        data = data.replace(b"\n", b" ").replace(b"\r", b" ")
    # build the characters dictionary
    chars_dict = build_chars_dict(data)
    # find non-overlapping sequences
    seqs = get_sequences(data, level, chars_dict)
    # find available symbols
    symbols = [bytes([symbol]) for symbol in range(0, 255) if symbol not in chars_dict.keys()]
    # remove newlines from available symbols
    if sfx:
        symbols = [symbol for symbol in symbols if symbol not in [b"\n", b"\r"]]
    # limit symbols available to max_entries, if specified
    if max_entries is not None:
        symbols = symbols[:max_entries]
    # keep the top n highest scored sequences, depending on the available symbols
    seqs = sorted(seqs, key=itemgetter(2), reverse=True)
    seqs = seqs[:len(symbols)]
    # encode the data
    encoded_data, replacements = encode_data(data, seqs, symbols)
    # build file
    file_content = build_file(encoded_data, replacements, sfx)

    # seqs_print = [[k, len(v), s] for k, v, s in seqs]
    # print(sorted(seqs_print, key=itemgetter(2), reverse=True))

    return file_content


def build_chars_dict(data):
    chars_dict = defaultdict(list)
    for i, c in enumerate(data):
        chars_dict[c].append(i)
    return chars_dict


def encode_data(data, seqs, symbols):
    # sort sequences by length, to replace the longer ones first
    seqs = sorted(seqs, key=lambda x: len(x[0]), reverse=True)
    # replacements table
    replacements = []
    for index, seq in enumerate(seqs):
        replacements.append([seq[0], symbols[index]])
    # replace symbols in data
    encoded_data = data
    for repl in replacements:
        encoded_data = encoded_data.replace(repl[0], repl[1])
    # express symbols using other symbols
    replacements = sorted(replacements, key=itemgetter(0))
    for index, repl in enumerate(replacements):
        for sr in replacements[index+1:]:
            if repl[0] in sr[0]:
                sr[0] = sr[0].replace(repl[0], repl[1])
    # return encoded data and sorted replacements
    return encoded_data, replacements


def build_file(encoded_data, replacements, sfx):
    # build header
    header_bytes = bytearray()
    header_bytes.extend(len(replacements).to_bytes(1, "little"))
    header_bytes.extend(len(encoded_data).to_bytes(2, "little"))
    for repl in replacements:
        header_bytes.extend(repl[1])  # symbol
        header_bytes.extend(len(repl[0]).to_bytes(1, "little"))  # length of sequence
        header_bytes.extend(repl[0])  # sequence
    # combine header with data
    file_content = bytearray()
    if sfx:
        file_content.extend(b"//")
    file_content.extend(header_bytes)
    file_content.extend(encoded_data)
    # append decompression stub
    if sfx:
        file_content.extend(b"\n")
        file_content.extend(get_sfx_stub())
    return file_content


def get_sfx_stub():
    stub_path = os.path.join(sys.path[0], "sfxstub.ks")
    with open(stub_path, "r") as f:
        text = f.read()
    return text.encode("ascii")


def get_sequences(data, level, chars_dict):    # TODO: find a better name
    # find repeating sequences
    seqs = find_sequences(data, level, chars_dict)
    # calculate the sequence score
    seqs = update_score(seqs)
    # remove fully overlapping sequences where all instances overlap with a longer one
    seqs = remove_fully_overlapping(seqs)
    # remove partially overlapping sequences, keep the ones with higher score
    seqs = remove_partially_overlapping(seqs, len(data))
    # update the sequence score
    seqs = update_score(seqs)
    return seqs


def find_sequences(data, level, chars_dict):
    data_length = len(data)
    # compression level
    min_matches = 6 - level
    # search for repeating sequences
    seqs = []
    q = deque([[[k], v] for k, v in chars_dict.items()])
    while q:
        k, v = q.pop()
        if len(v) > 1:
            next_chars = defaultdict(list)
            gen = (i for i in v if (i + 1) < data_length)
            for i in gen:
                next_chars[data[i + 1]].append(i + 1)
            new_entries = 0
            for nck, ncv in next_chars.items():
                if len(ncv) > min_matches:
                    new_key = k + [nck]
                    q.append([new_key, ncv])
                    new_entries += len(ncv)
            if len(k) > 1 and len(v) > 1 and (len(v) - new_entries) >= 1:
                seqs.append([bytearray(k), v, 0])
    return seqs


def update_score(seqs):
    scored_seqs = []
    for seq in seqs:
        key = seq[0]
        indices = seq[1]
        score = len(key) * (len(indices) - 1) - 2 - len(indices)
        if score > 0:
            seq[2] = score
            scored_seqs.append(seq)
    return scored_seqs


def remove_fully_overlapping(seqs):
    # sort by sequence length, longest first
    sorted_seqs = sorted([[k, len(v)] for k, v, _ in seqs], key=lambda x: len(x[0]), reverse=True)
    longer_seqs = []
    seqs_remove = []
    # TODO: assign better variable names
    for k, length in sorted_seqs:
        for a, b in longer_seqs:
            if k in a and length == b:
                seqs_remove.append(k)
                break
        longer_seqs.append([k, length])
    seqs = [seq for seq in seqs if seq[0] not in seqs_remove]
    return seqs


def remove_partially_overlapping(seqs, data_size):
    # TODO: this could be replaced with a bit map, but the data sizes are so small that it doesn't really matter
    claimed_map = [False] * data_size
    # sort by score, highest first
    sorted_seqs = sorted(seqs, key=itemgetter(2), reverse=True)
    for seq in sorted_seqs:
        key_length = len(seq[0])
        for end_index in list(seq[1]):
            start_index = end_index - key_length + 1
            removed = False
            for check_index in range(start_index, end_index):
                if claimed_map[check_index]:
                    seq[1].remove(end_index)
                    removed = True
                    break
            if not removed:
                for claim_index in range(start_index, end_index):
                    claimed_map[claim_index] = True
    return sorted_seqs
