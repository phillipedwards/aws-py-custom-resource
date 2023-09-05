"""An AWS Python Pulumi program"""

import json
import pulumi
from pulumi_aws import sns, iam, sns, lambda_, s3, cloudformation
import pulumi_random
import cloud_formation


def template_body(
    some_str: str, role_arn: pulumi.Input[str], sns_arn: pulumi.Input[str]
) -> pulumi.Output[str]:
    return pulumi.Output.json_dumps(
        {
            "Resources": {
                "CustomResourceTest": {
                    "Type": "Custom::SnsCustomResourceTest",
                    "Properties": {
                        "Type": "AWS_CFG",
                        "ServiceToken": sns_arn,
                        "IntegrationName": {"Ref": "AWS::StackName"},
                        "RandomToken": some_str,
                        "RoleArn": role_arn,
                        "TemplateVersion": "1.0",
                        "AWSAccountId": {"Ref": "AWS::AccountId"},
                    },
                }
            }
        }
    )


topic = sns.Topic(
    "test-topic",
)

lambda_role = iam.Role(
    "lambda-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Effect": "Allow",
                    "Sid": "",
                }
            ],
        }
    ),
)

iam.RolePolicyAttachment(
    "lambda-rpa",
    policy_arn=iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE,
    role=lambda_role.name,
)

fn = lambda_.Function(
    "test-func",
    runtime=lambda_.Runtime.NODE_JS16D_X,
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./function")}),
    handler="index.handler",
    environment=lambda_.FunctionEnvironmentArgs(variables={"TOPIC_ARN": topic.arn}),
    role=lambda_role.arn,
)

bucket = s3.Bucket("test-bucket")

bucket_policy = iam.Policy(
    "bucket-policy",
    policy=pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:PutObject",
                    "Resource": pulumi.Output.concat(bucket.arn, "/*"),
                }
            ],
        }
    ),
)

iam.RolePolicyAttachment(
    "lambda-bucket-rpa",
    role=lambda_role.name,
    policy_arn=bucket_policy.arn,
)

lambda_.Permission(
    "lambda-perm",
    action="lambda:InvokeFunction",
    function=fn.name,
    principal="sns.amazonaws.com",
    source_arn=topic.arn,
)

sns.TopicSubscription(
    "topic-sub",
    topic=topic.arn,
    protocol="lambda",
    endpoint=fn.arn,
)

# cloud_formation.CustomResourceStack(
#     "test",
#     cloud_formation.CustomResourceArgs(
#         topic_arn=topic.arn, bucket_role_arn=lambda_role.arn, bucket_role=lambda_role
#     ),
# )
rand = pulumi_random.RandomId(
    "random",
    byte_length=6,
)

cloudformation.Stack(
    "test-stack",
    opts=pulumi.ResourceOptions(
        ignore_changes="templateBody",
        depends_on=[lambda_role],
    ),
    name=pulumi.Output.concat("CustomResourceTestStack", rand.id),
    template_body=template_body(
        some_str="random",
        role_arn=lambda_role.arn,
        sns_arn=topic.arn,
    ),
)

pulumi.export("lambda_arn", fn.arn)
