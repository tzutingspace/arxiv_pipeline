import os

from aws_cdk import CfnParameter, Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()


EXCLUDE_FILES = ["*.env", ".env*", "*.pyc", "*.pyo", "*.pyd", "*.pyw", "*.pyz"]


class PipelineCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # 定義參數
        KAGGLE_USERNAME = CfnParameter(
            self,
            "KAGGLE_USERNAME",
            type="String",
            description="KAGGLE_USERNAME",
            no_echo=True,  # 配置参数不顯示
        )
        KAGGLE_KEY = CfnParameter(
            self,
            "KAGGLE_KEY",
            type="String",
            description="KAGGLE_KEY",
            no_echo=True,  # 配置参数不顯示
        )

        OPENSEARCH_HOST = CfnParameter(
            self,
            "OPENSEARCH_HOST",
            type="String",
            description="OPENSEARCH_HOST",
            no_echo=True,  # 配置参数不顯示
        )

        # 透過角色 ARN 來取得現有的 IAM 角色
        existing_role_arn = f"arn:aws:iam::{os.environ['AWS_ACCOUNT']}:role/{os.environ['AWS_ROLE']}"
        existing_role = iam.Role.from_role_arn(self, "ExistingRole", role_arn=existing_role_arn)

        # Defines an AWS Lambda resource
        collection_layer = _lambda.DockerImageFunction(
            self,
            "collection_layer",
            code=_lambda.DockerImageCode.from_image_asset("./collection_layer"),
            role=existing_role,
            timeout=Duration.seconds(900),  # max:15min
            memory_size=10240,
            # ephemeral_storage_size="10240 MiB",
            environment={
                "S3_BUCKET_NAME": os.environ["S3_BUCKET_NAME"],
                "S3_FOLDER_PREFIX": os.environ["S3_FOLDER_PREFIX"],
                "KAGGLE_USERNAME": KAGGLE_USERNAME.value_as_string,
                "KAGGLE_KEY": KAGGLE_KEY.value_as_string,
                "KAGGLE_CONFIG_DIR": "/tmp",
            },
            description="collection layer function deployed with Docker image via CDK",
        )

        data_process_layer = _lambda.DockerImageFunction(
            self,
            "data_process_layer",
            code=_lambda.DockerImageCode.from_image_asset("./data_process_layer"),
            role=existing_role,
            timeout=Duration.seconds(900),  # max:15min
            memory_size=512,
            environment={
                "OPENSEARCH_HOST": OPENSEARCH_HOST.value_as_string,
            },
            description="data process layer function deployed with Docker image via CDK",
        )
