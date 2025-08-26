參考：
https://jumping-code.com/2021/07/28/aws-lambda-python-packages/


-  `rm -rf ./python`
-  `mkdir ./python`
- `cd python`
-  `uv export --format requirements-txt --no-hashes --no-dev > requirements.txt`
-  `uv pip install --no-cache-dir --target . -r requirements.txt`
-  `cd ..`
-  `zip -r dependencies.zip ./python`