參考：
https://jumping-code.com/2021/07/28/aws-lambda-python-packages/


1. `uv export --format requirements-txt --no-hashes > requirements.txt`
2. `pip install --target . -r requirements.txt`
3. `zip -r dependencies.zip ./python`