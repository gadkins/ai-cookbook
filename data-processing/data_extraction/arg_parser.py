# arg_parser.py
import argparse


class CheckRange(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not 1 <= values <= 30000:
            raise argparse.ArgumentTypeError(
                "Value must be between 1 and 30000. 7500 token limit, approx 4 characters per token, 30k context limit"
            )
        setattr(namespace, self.dest, values)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run a test for long or short context."
    )
    parser.add_argument(
        "--chunk_length",
        type=int,
        default=6000,
        action=CheckRange,
        help="Number of characters for the description length (default: 8000, max: 30000)",
    )
    parser.add_argument(
        "--output_format",
        type=str,
        choices=["yaml", "json"],
        default="json",
        help="Output format, options are yaml and json. Default is json.",
    )
    parser.add_argument(
        "--output_file_name",
        type=str,
        default="output",
        help="Output file name, default is 'output'.",
    )
    parser.add_argument(
        "--batching",
        type=bool,
        default=True,
        help="Set to True for batching, will execute the requests concurrently based on the context limit of model. Default is False, will execute the requests into parallel mode",
    )
    parser.add_argument(
        "--input_file_name",
        type=str,
        default="berkshire23_12.5k.txt",
        help="Input file name, default is 'berkshire23_12.5k.txt'.",
    )
    return parser.parse_args()
