import os
import json


def get_directory_tree(root_dir):
    tree = {"name": os.path.basename(root_dir), "type": "directory", "children": []}
    try:
        for name in os.listdir(root_dir):
            path = os.path.join(root_dir, name)
            if os.path.isdir(path):
                tree["children"].append(get_directory_tree(path))
            else:
                tree["children"].append({"name": name, "type": "file"})
    except PermissionError:
        pass
    return tree


def directory_tree_to_json(root_dir):
    directory_tree = get_directory_tree(root_dir)
    return json.dumps(directory_tree, indent=4)
