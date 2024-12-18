import json
import argparse
def replace_keys_in_query(query_string, replacements):
    for key, value in replacements.items():
        query_string = query_string.replace(key, value)
    return query_string

def query_in_datasets(data, replacements):
    if isinstance(data, dict):
        if 'datasets' in data:
            for dataset in data['datasets']:
                if 'query' in dataset:
                    dataset['query'] = replace_keys_in_query(dataset['query'], replacements)

    return data

def parse_json_file(file_path, replacements, target_file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    dashboard_json = json.loads(data['serialized_dashboard'])
    modified_data = query_in_datasets(dashboard_json, replacements)

    with open(target_file_path, 'w') as file:
        json.dump(modified_data, file, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse JSON file')

    parser.add_argument('--file_path', required=True, help='Path to the Dashboard JSON file')
    parser.add_argument('--replacements', required=True, help='Replacements in JSON format')
    parser.add_argument('--target_file', required=True, help='Dashboard json modified file save location')


    args = parser.parse_args()
    print(args)
    print(args.replacements)

    parse_json_file(args.file_path, json.loads(f'{args.replacements}'), args.target_file)