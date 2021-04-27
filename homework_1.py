"""
Источник: https://5ka.ru/special_offers/
Задача организовать сбор данных,
необходимо иметь метод сохранения данных в .json файлы
результат: Данные скачиваются с источника, при вызове метода/функции сохранения в файл скачанные данные
сохраняются в Json вайлы, для каждой категории товаров должен быть создан отдельный файл и содержать товары исключительно соответсвующие данной категории.
пример структуры данных для файла:
нейминг ключей можно делать отличным от примера
{
"name": "имя категории",
"code": "Код соответсвующий категории (используется в запросах)",
"products": [{PRODUCT}, {PRODUCT}........] # список словарей товаров соответсвующих данной категории
}
"""
import json
import time
from pathlib import Path
import requests

class Parse5ka_cat:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/72.0"
    }
    params = {
        "records_per_page": 20,
        "categories": None
    }

    def __init__(self, url_cats: str, url_prods: str, save_path: Path):
        self.url_cats = url_cats
        self.url_prods = url_prods
        self.save_path = save_path

    def _get_response(self, url, *args, **kwargs):
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(3)

    def run(self):
        for category in self._parse(self.url_cats, self.url_prods):
            if category['group_code']:
                file_path = self.save_path.joinpath(f"{category['group_code']}.json")
            else:
                file_path = self.save_path.joinpath(f"{category['parent_group_code']}.json")
            self._save(category, file_path)

    def _parse(self, url_cats: str, url_prods: str):
        time.sleep(0.1)
        response = self._get_response(url_cats, headers=self.headers)
        data_parent_cats = response.json()
        for parent_category in data_parent_cats:
            url_new_cats = url_cats + parent_category['parent_group_code'] + '/'
            time.sleep(0.1)
            response = self._get_response(url_new_cats, headers=self.headers)
            data_new_cats = response.json()
            result = {}
            if data_new_cats:
                for new_category in data_new_cats:
                    result.clear()
                    result["parent_group_name"] = parent_category['parent_group_name']
                    result["parent_group_code"] = parent_category['parent_group_code']
                    result["group_name"] = new_category['group_name']
                    result["group_code"] = new_category['group_code']
                    result["products"] = []
                    params = self.params.copy()
                    params["categories"] = int(new_category['group_code'])
                    self._parse_prods(url_prods, params, result)
                    yield result
            else:
                result.clear()
                result["parent_group_name"] = parent_category['parent_group_name']
                result["parent_group_code"] = parent_category['parent_group_code']
                result["group_name"] = None
                result["group_code"] = None
                result["products"] = []
                params = self.params.copy()
                params["categories"] = int(parent_category['parent_group_code'])
                self._parse_prods(url_prods, params, result)
                yield result

    def _parse_prods(self, url_prods: str, params: dict, result: dict):
        page = 1
        next_page = True
        while next_page:
            time.sleep(0.1)
            response = self._get_response(url_prods, headers=self.headers, params=params)
            data = response.json()
            for product in data["results"]:
                result["products"].append(product)
            next_page = data["next"]
            if next_page:
                page += 1
                params["page"] = page

    def _save(self, data: dict, file_path):
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

def get_save_path(dir_name):
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path

if __name__ == "__main__":
    save_path = get_save_path("categories")
    url_cats = "https://5ka.ru/api/v2/categories/"
    url_prods = "https://5ka.ru/api/v2/special_offers/"
    parser = Parse5ka_cat(url_cats, url_prods, save_path)
    parser.run()