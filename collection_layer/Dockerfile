FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# 複製 requirements 文件
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# 安裝依賴
RUN pip install -r requirements.txt

# 複製函數代碼
COPY . ${LAMBDA_TASK_ROOT}
# COPY arxiv_metadata.py ${LAMBDA_TASK_ROOT}

# 設置 Lambda 處理器
CMD [ "arxiv_metadata.lambda_handler" ]