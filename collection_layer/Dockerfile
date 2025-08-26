FROM public.ecr.aws/lambda/python:3.11

# 複製 requirements 文件
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# 安裝依賴
RUN pip install -r requirements.txt

# 複製函數代碼
COPY arxiv_metadata.py ${LAMBDA_TASK_ROOT}

# 設置 Lambda 處理器
CMD [ "arxiv_metadata.lambda_handler" ]