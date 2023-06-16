import yaml

def read_config_file(config_file_path : str):
    with open(config_file_path) as f_in:
        data = yaml.safe_load(f_in)
    
    return data
        
def save_config_file(fileName, json_data):
    with open(fileName, "w") as fp:
        yaml.dump(json_data , fp)