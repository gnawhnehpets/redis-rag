import json
import argparse
import os

"""_summary_
Parses a JSON file containing descriptions, sources, and a list of items.
This script can either output the parsed data to a JSONL file or print it to the console.
Setup:
    source setup_env.sh
Usage:
    python parser.py <file_path> [--output <output_path>]
    python3 search/parser.py search/assets 
"""

def parse_data(file_path, output_path=None):
    """
    Parses a JSON file containing descriptions, sources, and a list of items.

    Args:
        file_path (str): The path to the JSON file.
        output_path (str, optional): The path to the output JSONL file.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    source_filename = os.path.basename(file_path)

    if output_path:
        with open(output_path, 'w') as f_out:
            if isinstance(data, dict):
                data_key = None
                for key in ['diseases', 'symptoms', 'cancers', 'drugs', 'codes']:
                    if key in data:
                        data_key = key
                        break

                if data_key:
                    items = data[data_key]
                    for item in items:
                        if data_key == 'codes':
                            description = item.get('desc')
                        elif isinstance(item, list):
                            description = ' -> '.join(item)
                        else:
                            description = item
                        
                        json_line = {
                            "description": description,
                            "source": source_filename
                        }
                        f_out.write(json.dumps(json_line) + '\n')
            elif isinstance(data, list):
                 for item in data:
                    json_line = {
                        "description": item,
                        "source": source_filename
                    }
                    f_out.write(json.dumps(json_line) + '\n')
        print(f"Successfully created JSONL file at {output_path}")
    else:
        if isinstance(data, dict):
            description = data.get('description', 'No description provided.')
            source = data.get('source', 'No source provided.')
            print(f"Description: {description}")
            print(f"Source: {source}")
            print("-" * 20)
            
            data_key = None
            for key in ['diseases', 'symptoms', 'cancers', 'drugs', 'codes']:
                if key in data:
                    data_key = key
                    break
            
            if data_key:
                print(f"{data_key.capitalize()}:")
                for item in data[data_key]:
                    if data_key == 'codes':
                        print(f"- {item.get('code')}: {item.get('desc')}")
                    elif isinstance(item, list):
                        print(f"- {' -> '.join(item)}")
                    else:
                        print(f"- {item}")
            else:
                print("No known data key found in the JSON file.")
        elif isinstance(data, list):
            for item in data:
                print(f"- {item}")
        else:
            print("Unsupported JSON structure.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse JSON data files from a directory.")
    parser.add_argument("directory_path", type=str, help="The path to the directory containing JSON files.")
    args = parser.parse_args()

    for filename in os.listdir(args.directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(args.directory_path, filename)
            output_path = os.path.join(args.directory_path, f"{os.path.splitext(filename)[0]}.jsonl")
            parse_data(file_path, output_path)
