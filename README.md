# arxiv-pipeline

一個基於 AWS Lambda 的自動化 arXiv 論文資料處理 pipeline，用於收集、處理並索引 arXiv 論文元資料到 OpenSearch。

## 🏗️ 架構概述

此專案採用無伺服器架構，包含以下主要組件：

- **Collection Layer**: 從 Kaggle 下載並處理 arXiv 元資料
- **Data Process Layer**: 轉換並索引資料到 OpenSearch
- **OpenSearch**: 提供論文搜尋與分析功能
- **AWS CDK**: IaC, 用於部署相關 aws 服務

## 📁 專案結構

```
arxiv-pipeline/
├── app.py                          # CDK 應用程式入口 (可忽略)
├── pyproject.toml                  # Python 專案配置
├── pipeline_cdk/                   # 處理 aws 服務部署, 定義該專案相關之 aws 服務
│   └── pipeline_cdk_stack.py
├── collection_layer/               # 資料收集層
│   ├── arxiv_metadata.py           # 主要邏輯
│   ├── Dockerfile                  
│   └── utils/                      
├── data_process_layer/             # 資料處理層
│   ├── arxiv_metadata.py           # 主要邏輯
│   ├── Dockerfile                  
│   └── utils/                     
├── create_index_with_mapping/      # OpenSearch 索引初始化
│   └── main.py                     # 建立索引與 mapping
└── tests/                          # 測試檔案(由CDK 自動建立)
```

## 前置需求

- Python 3.12+
- AWS CLI 已配置
- Docker (用於本地開發測試)
- Node.js (用於 AWS CDK)
- uv (用於管理 python library)
