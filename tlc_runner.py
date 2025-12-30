import re
import os

from graph_conversions import generate_graph_from_graphwalker_json

def load_tlc_test_suite(tlc_path, remove_duplicates=False):
    # Tüm dosyayı okuyup "currentElementName" değerlerini çıkart
    elems = []
    with open(tlc_path, "r", encoding="utf-8") as f:
        content = f.read()
        # tüm eşleşmeleri bul
        matches = re.findall(r'"currentElementName"\s*:\s*"([^"]+)"', content)
        elems.extend(matches)

    # Vertexler ve edge'leri birlikte tutacak şekilde test case'i oluştur
    # Vertex: 'start' veya q ile başlayan (q0, q1, q2, ..., q8 gibi)
    # Edge: Diğer tüm elemanlar
    
    # v_Start/start mutlaka olmalı
    if "start" not in elems:
        raise ValueError("TLC dosyasında 'start' bulunamadı. Lütfen GraphWalker çıktısını kontrol edin.")

    # Test case'leri: her 'start' gördüğümüzde yeni test başlat
    test_suite = []
    current_test = None
    
    for elem in elems:
        if elem == "start":
            # Yeni test başla
            if current_test is not None:
                if remove_duplicates:
                    if current_test not in test_suite:
                        test_suite.append(current_test.copy())
                else:
                    test_suite.append(current_test.copy())
            current_test = [elem]
        else:
            # start'tan sonra gelen tüm elemanları ekle (vertex ve edge'ler)
            if current_test is not None:
                current_test.append(elem)

    # Son testi ekle
    if current_test is not None:
        if remove_duplicates:
            if current_test not in test_suite:
                test_suite.append(current_test.copy())
        else:
            test_suite.append(current_test.copy())

    return test_suite

def run_tlc_on_model(tlc_path, model_json_name, verbose=True, remove_duplicates=False):
    if not os.path.exists(tlc_path):
        raise FileNotFoundError(f"{tlc_path} bulunamadı.")
    model = generate_graph_from_graphwalker_json(model_json_name)
    test_suite = load_tlc_test_suite(tlc_path, remove_duplicates=remove_duplicates)

    from main import apply_test_execution_on_model
    return apply_test_execution_on_model(test_suite, model, verbose)