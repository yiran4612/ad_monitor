# Layer: infrastructure
"""P1 静态省市区数据。

地区树在 P1 阶段不建表、不引入外部依赖，直接以内联常量维护
（后续接行政区划库时，只需替换本模块的 ``get_area_tree`` / ``resolve_area_id`` 实现）。

- id 采用国家统计局行政区划代码，``0`` 表示根节点
- 前端 a-cascader 的 field-names 是 ``{label: 'name', value: 'id', children: 'children'}``，
  因此节点结构固定为 ``{"id": int, "name": str, "children": [...]}``
- ``getAreaInfo?id=0`` 返回全量树（前端未做懒加载，一次取全量即可级联选择）
"""

ROOT_ID = 0

# 结构：[{"id": 省代码, "name": 省名, "children": [{"id": 市代码, ..., "children": [区]}]}]
_AREAS: list[dict] = [
    {
        "id": 110000,
        "name": "北京市",
        "children": [
            {
                "id": 110100,
                "name": "北京市",
                "children": [
                    {"id": 110101, "name": "东城区"},
                    {"id": 110102, "name": "西城区"},
                    {"id": 110105, "name": "朝阳区"},
                    {"id": 110106, "name": "丰台区"},
                    {"id": 110108, "name": "海淀区"},
                ],
            }
        ],
    },
    {
        "id": 310000,
        "name": "上海市",
        "children": [
            {
                "id": 310100,
                "name": "上海市",
                "children": [
                    {"id": 310101, "name": "黄浦区"},
                    {"id": 310104, "name": "徐汇区"},
                    {"id": 310106, "name": "静安区"},
                    {"id": 310109, "name": "虹口区"},
                    {"id": 310115, "name": "浦东新区"},
                ],
            }
        ],
    },
    {
        "id": 320000,
        "name": "江苏省",
        "children": [
            {
                "id": 320100,
                "name": "南京市",
                "children": [
                    {"id": 320102, "name": "玄武区"},
                    {"id": 320106, "name": "鼓楼区"},
                    {"id": 320113, "name": "栖霞区"},
                    {"id": 320115, "name": "江宁区"},
                ],
            },
            {
                "id": 320500,
                "name": "苏州市",
                "children": [
                    {"id": 320505, "name": "虎丘区"},
                    {"id": 320506, "name": "吴中区"},
                    {"id": 320508, "name": "姑苏区"},
                    {"id": 320571, "name": "苏州工业园区"},
                ],
            },
        ],
    },
    {
        "id": 330000,
        "name": "浙江省",
        "children": [
            {
                "id": 330100,
                "name": "杭州市",
                "children": [
                    {"id": 330102, "name": "上城区"},
                    {"id": 330105, "name": "拱墅区"},
                    {"id": 330106, "name": "西湖区"},
                    {"id": 330108, "name": "滨江区"},
                    {"id": 330110, "name": "余杭区"},
                ],
            },
            {
                "id": 330200,
                "name": "宁波市",
                "children": [
                    {"id": 330203, "name": "海曙区"},
                    {"id": 330205, "name": "江北区"},
                    {"id": 330206, "name": "北仑区"},
                    {"id": 330212, "name": "鄞州区"},
                ],
            },
        ],
    },
    {
        "id": 440000,
        "name": "广东省",
        "children": [
            {
                "id": 440100,
                "name": "广州市",
                "children": [
                    {"id": 440103, "name": "荔湾区"},
                    {"id": 440104, "name": "越秀区"},
                    {"id": 440106, "name": "天河区"},
                    {"id": 440113, "name": "番禺区"},
                ],
            },
            {
                "id": 440300,
                "name": "深圳市",
                "children": [
                    {"id": 440303, "name": "罗湖区"},
                    {"id": 440304, "name": "福田区"},
                    {"id": 440305, "name": "南山区"},
                    {"id": 440306, "name": "宝安区"},
                ],
            },
        ],
    },
]


def _copy_node(node: dict) -> dict:
    """深拷贝节点，避免调用方改动模块级常量。"""
    return {
        "id": node["id"],
        "name": node["name"],
        "children": [_copy_node(child) for child in node.get("children", [])],
    }


def _find_node(nodes: list[dict], node_id: int) -> dict | None:
    for node in nodes:
        if node["id"] == node_id:
            return node
        found = _find_node(node.get("children", []), node_id)
        if found is not None:
            return found
    return None


def get_area_tree(parent_id: int = ROOT_ID) -> list[dict]:
    """返回 ``parent_id`` 的子节点列表。

    - ``parent_id=0``：全量省树（含市、区两级 children）
    - ``parent_id=<省/市代码>``：该节点的直接子节点
    - 节点不存在或是叶子：返回 ``[]``
    """
    if parent_id == ROOT_ID:
        return [_copy_node(node) for node in _AREAS]

    node = _find_node(_AREAS, parent_id)
    if node is None:
        return []
    return [_copy_node(child) for child in node.get("children", [])]


def resolve_area_id(path: str) -> int:
    """把「浙江省/杭州市/西湖区」逐级匹配到最深层节点 id。

    匹配不到返回 ``ROOT_ID``；只匹配到部分层级时返回已命中的最深层 id，
    兼容前端只选到省、或只选到省市的场景。
    """
    if not path:
        return ROOT_ID

    nodes = _AREAS
    matched = ROOT_ID
    for name in [part.strip() for part in path.split("/") if part.strip()]:
        for node in nodes:
            if node["name"] == name:
                matched = node["id"]
                nodes = node.get("children", [])
                break
        else:
            break
    return matched
