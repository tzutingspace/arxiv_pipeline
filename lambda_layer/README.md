# 目的：原本要用於 Lambda Layer 的建立

# 參考：
https://jumping-code.com/2021/07/28/aws-lambda-python-packages/

# Step
-  `rm -rf ./python`
-  `mkdir ./python`
- `cd python`
-  `uv export --format requirements-txt --no-hashes --no-dev > requirements.txt`
-  `uv pip install --no-cache-dir --target . -r requirements.txt`
-  `cd ..`
-  `zip -r dependencies.zip ./python`

# Changelog
- 後續 lambda layer 改用 image -> container 形式 (因為套件安裝一直遇到問題 e.g. `numpy` )