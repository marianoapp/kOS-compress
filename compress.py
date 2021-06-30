import sys
import argparse
import dictionary
import huffman


def main():
    default_input = None if sys.stdin.isatty() else sys.stdin
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--method", dest="method", choices={"d", "h"}, default="d",
                        help="compression method")
    parser.add_argument("-l", "--level", dest="level", type=int, choices=range(1, 6), default=5,
                        help="compression level")
    parser.add_argument("--sfx", action="store_true", help="create a self extracting package")
    parser.add_argument("file", nargs="?", type=argparse.FileType("rb"), default=default_input,
                        help="file to compress")
    parser.add_argument("outfile", nargs="?", type=argparse.FileType("wb"), default=sys.stdout,
                        help="compressed file")
    if len(sys.argv) == 1:
        parser.print_help()
        return

    output = None
    args = parser.parse_args()
    data = args.file.read()
    # if the data is read from stdout it comes as a string
    if type(data) is str:
        data = data.encode("ascii")
    # compress
    if args.method == "d":
        output = dictionary.process(data, args.level, None, args.sfx)
    elif args.method == "h":
        output = huffman.process(data)
    # write the output
    if output is not None:
        args.outfile.write(output)


if __name__ == "__main__":
    main()
