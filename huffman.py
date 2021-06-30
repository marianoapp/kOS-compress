from collections import Counter
from queue import PriorityQueue


class Node:
    symbol = ""
    freq = 0
    left = None
    right = None

    def __init__(self, symbol, freq):
        self.symbol = symbol
        self.freq = freq

    def __lt__(self, other):
        return self.freq < other.freq


def process(data):
    # measure the frequency of each symbol (count how many time they appear)
    symbol_freqs = Counter(data)  # Counter({'l': 2, 'H': 1, 'e': 1, 'o': 1})
    # create nodes for each symbol and add them to the freq queue
    q = PriorityQueue()
    for symbol, freq in symbol_freqs.items():
        q.put(Node(symbol, freq))
    # build tree
    root_node = None
    while not q.empty():
        item_one = q.get()
        if not q.empty():
            item_two = q.get()
            node = Node(item_one.symbol + item_two.symbol, item_one.freq + item_two.freq)
            node.left = item_one
            node.right = item_two
            q.put(node)
        else:
            # item_one is the last node in the queue, so it's the root node
            root_node = item_one
            break
    # build symbol dictionary
    symbol_dict = {}
    build_symbol_dict(root_node, "", symbol_dict)
    # print(symbol_dict)
    # encode data
    bitstring = encode(data, symbol_dict)
    # append symbol codes
    codes = [code for symbol, code in symbol_dict.items()]
    bitstring = "".join(codes) + bitstring
    # pad with zeros at the end to make the length a multiple of 8
    pad_len = 8 - (len(bitstring) % 8)
    if pad_len > 0:
        bitstring += "0" * pad_len
    # print(bitstring)
    # convert encoded data to byte array
    buffer = bitstring_to_bytes(bitstring)
    # build entry list
    entries = [[symbol, len(code)] for symbol, code in symbol_dict.items()]
    entries_bytes = bytearray()
    for symbol, code_len in entries:
        # entries_bytes.append(ord(symbol))
        entries_bytes.append(symbol)
        entries_bytes.extend(code_len.to_bytes(1, "little"))
    # build header
    header_bytes = bytearray()
    header_bytes.extend(len(entries).to_bytes(1, "little"))
    header_bytes.extend(len(buffer).to_bytes(2, "little"))
    header_bytes.extend(pad_len.to_bytes(1, "little"))
    # file buffer
    file_buffer = bytearray()
    file_buffer.extend(header_bytes)
    file_buffer.extend(entries_bytes)
    file_buffer.extend(buffer)

    # print(sorted(symbol_dict.items(), key=lambda x: len(x[1])))

    return file_buffer


def bitstring_to_bytes(bitstring):
    b = bytearray()
    for i in range(0, len(bitstring), 8):
        byte = bitstring[i:i + 8]
        b.append(int(byte, 2))
    return b


def encode(data, symbol_dict):
    encoded = []
    for symbol in data:
        encoded.append(symbol_dict[symbol])
    bitstring = "".join(encoded)
    return bitstring


def build_symbol_dict(node, path, symbol_dict):
    # check if leaf node
    if node.left is None and node.right is None:
        symbol_dict[node.symbol] = path
    else:
        build_symbol_dict(node.left, path + "0", symbol_dict)
        build_symbol_dict(node.right, path + "1", symbol_dict)