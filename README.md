# 展陈调色核料册

领料员把称量票、容器皮重、颜料批号和回桶收据核在同一张工单上。克重收据显示秤单净量、按成分重建的实际回桶量、班后余罐量和申报差异，可打印或下载签发证据。

## 启动

```sh
docker compose up --build
```

访问 `http://localhost:18467/`。本地 Python 3.12 用以下命令。

```sh
python -m pip install -r requirements-test.txt
python -m flask --app app.main run --port 18467
python -m pytest -q
```

留档存入 `var/receipts`，容器挂载 `palette-receipts` 卷。需要重置自建环境时，在停服后删除指定留档目录或该卷。

## 演示

1. 首页选择「班后回桶样例」。期初 100.000 g 与领用 250.010 g，分别归入上件 140.000 g、损耗 30.000 g、回桶 146.010 g 和争议留罐 34.000 g。
2. 打开「容器皮重」，定位 B08 的重叠版本和负净量；在「回桶分料」筛选 A12 查看回桶票 0005 的两个批号来源。
3. 「库存核料」显示两笔申报差异。点击「封存工单」，进入「证据签发」下载。也可在工作台打印收据。

试算入口为 `GET /api/trial/{dirty|clean}/{stage}`。阶段名见深度登记。自有原件可提交 `POST /api/books`，JSON 用 `sheets` 包含 `job`、`weights`、`tares`、`lots`、`claims` 的 UTF-8 文本，也可使用 `{"sample":"dirty"}`。`GET /api/books` 查历史，`GET /api/books/{key}` 查单册库存，`GET /api/export/{key}` 下载证据。

- [数据定义](docs/DATA-DICTIONARY.md)
- [模块与陷阱](docs/DEPTH.md)
- [复核一张回桶票](docs/RECEIPT-REVIEW.md)
