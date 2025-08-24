import os

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()


EXCLUDE_FILES = ["*.env", ".env*", "*.pyc", "*.pyo", "*.pyd", "*.pyw", "*.pyz"]


class PipelineCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 透過角色 ARN 來取得現有的 IAM 角色
        existing_role_arn = f"arn:aws:iam::{os.environ['AWS_ACCOUNT']}:role/{os.environ['AWS_ROLE']}"
        existing_role = iam.Role.from_role_arn(self, "ExistingRole", role_arn=existing_role_arn)

        # Defines an AWS Lambda Layer
        lambda_layer = _lambda.LayerVersion(
            self,
            "lambda-layer",
            code=_lambda.AssetCode("lambda_layer/"),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_12,
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_10,
            ],
        )

        # Defines an AWS Lambda resource
        # scheduler
        collection_layer = _lambda.Function(
            self,
            "collection_layer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset(
                "collection_layer",
                exclude=EXCLUDE_FILES,
            ),
            handler="arxiv_metadata.lambda_handler",
            layers=[lambda_layer],
            role=existing_role,
            timeout=Duration.seconds(900),  # max:15min
            environment={
                "S3_BUCKET_NAME": os.environ["S3_BUCKET_NAME"],
                "S3_FOLDER_PREFIX": os.environ["S3_FOLDER_PREFIX"],
            },
        )
