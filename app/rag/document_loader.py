"""
文档加载器：读取 knowledge_base/products/*.md，解析为产品文档列表。

每个 .md 文件用 `# 产品名` 标题切分产品，字段用 `标签：值` 描述。
返回结构：
    [{"text": 产品全文, "metadata": {product_name, category, source, ...字段}}]
"""
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base" / "products"

# 字段标签 -> 规范 key
_FIELD_MAP = {
    "产品名称": "name",
    "适用客户": "target_customer",
    "产品特点": "description",
    "申请条件": "condition",
    "业务场景": "business_scenario",
    "营销重点": "marketing_point",
}


def _parse_product_blocks(text: str) -> list[dict]:
    """按 `# 产品名` 标题把 markdown 拆成产品块，再解析字段。"""
    products: list[dict] = []
    current: dict | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            name = line.lstrip("#").strip()
            if current:
                products.append(current)
            current = {"name": name, "fields": {}, "order": []}
            continue

        if current is None:
            continue

        # 字段行：`标签：值`（值可空，此时后续非标签行作为续行追加）
        m = re.match(r"^([^\s：:]+)[：:]\s*(.*)$", line)
        if m:
            key = _FIELD_MAP.get(m.group(1).strip())
            value = m.group(2).strip()
            if key:
                current["fields"][key] = value
                current["order"].append(key)
        elif current["order"]:
            # 续行：追加到最后一个字段
            last = current["order"][-1]
            current["fields"][last] += " " + line

    if current:
        products.append(current)
    return products


def load_documents(directory: str | Path | None = None) -> list[dict]:
    """加载知识库目录下所有 .md 文件，返回产品文档列表。"""
    directory = Path(directory) if directory else DEFAULT_KB_DIR
    files = sorted(directory.glob("*.md"))
    docs: list[dict] = []

    for md_file in files:
        category = md_file.stem  # 文件名作为类别，如 loan_products
        text = md_file.read_text(encoding="utf-8")
        for p in _parse_product_blocks(text):
            name = p["name"]
            fields = p["fields"]
            full_text = " ".join([name] + [fields[k] for k in p["order"]])
            docs.append({
                "text": full_text,
                "metadata": {
                    "product_name": name,
                    "category": category,
                    "source": md_file.name,
                    "target_customer": fields.get("target_customer", ""),
                    "description": fields.get("description", ""),
                    "condition": fields.get("condition", ""),
                    "business_scenario": fields.get("business_scenario", ""),
                    "marketing_point": fields.get("marketing_point", ""),
                },
            })

    logger.info("文档加载完成 | files=%d | products=%d", len(files), len(docs))
    return docs
