import json
from datetime import datetime


class JsonWriterPipeline:
    """Simple pipeline that writes items to JSONL files in ./data"""

    def open_spider(self, spider):
        import os
        self.files = {}
        self.base_path = 'data'
        try:
            os.makedirs(self.base_path, exist_ok=True)
        except Exception:
            pass

    def _get_file(self, spider_name):
        if spider_name not in self.files:
            fname = f"data/{spider_name}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"
            f = open(fname, 'w', encoding='utf-8')
            self.files[spider_name] = f
        return self.files[spider_name]

    def process_item(self, item, spider):
        f = self._get_file(spider.name)
        line = json.dumps(dict(item), ensure_ascii=False)
        f.write(line + '\n')
        return item

    def close_spider(self, spider):
        for f in self.files.values():
            try:
                f.close()
            except Exception:
                pass
