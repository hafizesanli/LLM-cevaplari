import time
import os.path
from graph_conversions import *
from utility_functions import *
from tlc_runner import run_tlc_on_model

def check_if_path_exist(links, source, target):
    for link in links:
        if link["source"] == source and link["target"] == target:
            return True

    return False


def apply_test_execution_on_model(test_suite, model, verbose=True):
    # nodes_dict: vertex ismi -> [vertex ID'leri] (aynı isimde birden fazla vertex olabilir)
    nodes_dict = {}
    for node in model["nodes"]:
        name = node["name"]
        if name not in nodes_dict:
            nodes_dict[name] = []
        nodes_dict[name].append(node["id"])

    # edges_set: tüm valid edge isimleri
    edges_set = set()
    for link in model["links"]:
        edges_set.add(link["name"])

    start_names = {"v_Start", "start"}

    def is_vertex(name):
        """Vertex mi edge mi kontrolü"""
        return name in start_names or (isinstance(name, str) and (name.startswith("v_") or name.startswith("q")))

    for test_case in test_suite:
        if verbose is True:
            print(f"Test case to apply: {test_case}")
        previous_item = ""
        previous_item_name = ""
        i = 0
        
        while i < len(test_case):
            item = test_case[i]
            
            # Eğer item bir start işaretleyicisi ise previous_item'i ayarla
            if item in start_names:
                if item not in nodes_dict:
                    if verbose is True:
                        print(f"Unknown node name in test case: {item}")
                    return False
                # start için ilk ID'yi al
                previous_item = nodes_dict[item][0]
                previous_item_name = item
                i += 1
                continue
            
            # Eğer item bir edge ismi ise (ve sonraki bir vertex olacaksa)
            if not is_vertex(item):
                # Edge validation
                if item not in edges_set:
                    if verbose is True:
                        print(f"Invalid edge name in test case: '{item}' (not found in model)")
                    return False
                
                # Sonraki element vertex olmalı
                if i + 1 >= len(test_case):
                    if verbose is True:
                        print(f"Edge '{item}' has no target vertex")
                    return False
                
                next_item = test_case[i + 1]
                if not is_vertex(next_item):
                    if verbose is True:
                        print(f"After edge '{item}', expected a vertex but got '{next_item}'")
                    return False
                
                if next_item not in nodes_dict:
                    if verbose is True:
                        print(f"Unknown node name in test case: {next_item}")
                    return False
                
                # Sonraki vertex'e gidebilir miyiz kontrol et
                current_items = nodes_dict[next_item]
                found_path = False
                matched_current_item = None
                
                for current_item in current_items:
                    for link in model["links"]:
                        if link["source"] == previous_item and link["target"] == current_item and link["name"] == item:
                            found_path = True
                            matched_current_item = current_item
                            break
                    if found_path:
                        break
                
                if found_path:
                    if verbose is True:
                        print(
                            f"successfully moved from {previous_item_name} -> {next_item} via edge '{item}'"
                        )
                    previous_item = matched_current_item
                    previous_item_name = next_item
                    i += 2
                else:
                    if verbose is True:
                        print(
                            f"No path found for: {previous_item_name} -> {next_item} via edge '{item}'"
                        )
                    return False
            else:
                # Vertex - bu durum olmaz normalde, çünkü vertices arasında edge olmalı
                if verbose is True:
                    print(f"Unexpected vertex '{item}' without preceding edge")
                return False

    return True


if __name__ == "__main__":
   ##############################################################################
   ok = run_tlc_on_model("json_models/TLC.txt", "TLC.json", verbose=True)
   print("All passed" if ok else "Some failed")