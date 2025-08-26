import os

from aws_cdk import CfnParameter, Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_sqs as sqs
from aws_cdk.aws_lambda_event_sources import SqsEventSource
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

        # 透過角色 ARN 來取得現有的 IAM 角色
        existing_role_arn = f"arn:aws:iam::{os.environ['AWS_ACCOUNT']}:role/{os.environ['AWS_ROLE']}"
        existing_role = iam.Role.from_role_arn(self, "ExistingRole", role_arn=existing_role_arn)

        # Defines an AWS Lambda Layer
        lambda_layer = _lambda.LayerVersion(
            self,
            "lambda-layer",
            code=_lambda.AssetCode("lambda_layer/"),
            compatible_architectures=[
                _lambda.Architecture.ARM_64,
            ],
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_12,
            ],
        )

        # Defines an AWS Lambda resource
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
                "KAGGLE_USERNAME": KAGGLE_USERNAME.value_as_string,
                "KAGGLE_KEY": KAGGLE_KEY.value_as_string,
                "KAGGLE_CONFIG_DIR": "/tmp",
            },
            architecture=_lambda.Architecture.ARM_64,
        )

        data_process_layer = _lambda.Function(
            self,
            "data_process_layer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset(
                "data_process_layer",
                exclude=EXCLUDE_FILES,
            ),
            handler="arxiv_metadata.lambda_handler",
            layers=[lambda_layer],
            role=existing_role,
            timeout=Duration.seconds(900),  # max:15min
            # environment={
            #     "S3_BUCKET_NAME": os.environ["S3_BUCKET_NAME"],
            #     "S3_FOLDER_PREFIX": os.environ["S3_FOLDER_PREFIX"],
            # },
            architecture=_lambda.Architecture.ARM_64,
        )

        # Defines the transform queue
        transform_queue = sqs.Queue(
            self,
            "transformQueue",
            queue_name="transformQueue",
            visibility_timeout=Duration.seconds(960),  # 16min,
            receive_message_wait_time=Duration.seconds(20),
            # dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=1, queue=dlq),
        )

        transform_event_source = SqsEventSource(transform_queue, batch_size=1)
        data_process_layer.add_event_source(transform_event_source)

        #### test

        # docker_image_asset = ecr_assets.DockerImageAsset(
        #     self,
        #     "LambdaDockerImage",
        #     directory="./collection_layer",
        #     file="Dockerfile",
        #     platform=ecr_assets.Platform.LINUX_AMD64,
        #     build_args={
        #         "BUILDKIT_INLINE_CACHE": "1",
        #         # 可以加入更多 build args
        #     },
        #     exclude=["*.md", "*.pyc", "__pycache__", ".git", ".gitignore"],
        # )

        # dockerfile_dir = "./collection_layer"
        # lambda_function = _lambda.DockerImageFunction(
        #     self,
        #     "LambdaDockerFunction",
        #     function_name="my-lambda-docker-function",
        #     code=_lambda.DockerImageCode.from_image_asset(dockerfile_dir),
        #     role=existing_role,
        #     timeout=Duration.seconds(30),
        #     memory_size=256,
        #     environment={
        #         "S3_BUCKET_NAME": os.environ["S3_BUCKET_NAME"],
        #         "S3_FOLDER_PREFIX": os.environ["S3_FOLDER_PREFIX"],
        #         "KAGGLE_USERNAME": KAGGLE_USERNAME.value_as_string,
        #         "KAGGLE_KEY": KAGGLE_KEY.value_as_string,
        #     },
        #     description="Lambda function deployed with Docker image via CDK",
        # )
