from collections import defaultdict, deque
from operator import itemgetter


def process(data):
    # build the characters dictionary
    chars_dict = build_chars_dict(data)
    # find non-overlapping sequences
    seqs = get_sequences(data, chars_dict)
    # find available symbols
    symbols = [symbol for symbol in range(0, 255) if chr(symbol) not in chars_dict.keys()]
    # keep the top n highest scored sequences, depending on the available symbols
    seqs = sorted(seqs, key=itemgetter(2), reverse=True)
    seqs = seqs[:len(symbols)]
    # encode the data
    encoded_data = encode_data(data, seqs, symbols)

    # seqs_print = [[k, len(v), s] for k, v, s in seqs]
    # print(sorted(seqs_print, key=itemgetter(2), reverse=True))

    return encoded_data


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
        replacements.append([seq[0].encode("ascii"), symbols[index].to_bytes(1, "little")])
    # replace symbols in data
    new_data = bytearray(data.encode("ascii"))
    for repl in replacements:
        new_data = new_data.replace(repl[0], repl[1])
    # TODO: express symbols as sequence of other symbols
    # build header
    header_bytes = bytearray()
    header_bytes.extend(len(replacements).to_bytes(1, "little"))
    for repl in replacements:
        header_bytes.extend(repl[1])  # symbol
        header_bytes.extend(len(repl[0]).to_bytes(1, "little"))     # length of sequence
        header_bytes.extend(repl[0])
    # combine header with data
    encoded_data = header_bytes + new_data
    return encoded_data


def get_sequences(data, chars_dict):    # TODO: find a better name
    # find repeating sequences
    seqs = find_sequences(data, chars_dict)
    # calculate the sequence score
    seqs = update_score(seqs)
    # remove fully overlapping sequences where all instances overlap with a longer one
    seqs = remove_fully_overlapping(seqs)
    # remove partially overlapping sequences, keep the ones with higher score
    seqs = remove_partially_overlapping(seqs, len(data))
    # update the sequence score
    seqs = update_score(seqs)
    return seqs


def find_sequences(data, chars_dict):
    data = data + chr(0x00)  # add padding at the end
    # search for repeating sequences
    seqs = []
    q = deque([[k, v] for k, v in chars_dict.items()])
    while q:
        k, v = q.pop()
        if len(v) > 1:
            next_chars = defaultdict(list)
            for i in v:
                next_chars[data[i + 1]].append(i + 1)
            new_entries = 0
            for nck, ncv in next_chars.items():
                if len(ncv) > 1:
                    q.append([k + nck, ncv])
                    new_entries += len(ncv)
            if len(k) > 1 and len(v) > 1 and (len(v) - new_entries) >= 1:
                seqs.append([k, v, 0])
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
