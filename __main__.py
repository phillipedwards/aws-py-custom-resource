"""An AWS Python Pulumi program"""

import json
import pulumi
from pulumi.output import Inputs
from pulumi.resource import ResourceOptions
from pulumi_aws import (
    sns,
    iam,
    cloudformation
)

class CustomResourceStack(pulumi.ComponentResource):
    
    def __init__(self, name: str, opts: ResourceOptions | None = None) -> None:
        super().__init__("pkd:index:customResource", name, opts)
        self.topic = sns.Topic(
            "cfn-topic"
        )

        self.role = iam.Role(
            "role",
            assume_role_policy=json.dumps({
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Action': 'sts:AssumeRole',
                        'Principal': {
                            'Service': 'eks.amazonaws.com'
                        },
                        'Effect': 'Allow',
                        'Sid': ''
                    }
                ],
            }),
        )

        self.custom_resource_stack = cloudformation.Stack(
            "test-stack",
            opts=pulumi.ResourceOptions(
                parent=self,
                ignore_changes="templateBody",
                depends_on=[self.role]
            ),
            name="CustomResourceTestStack",
            template_body=self.__template_body(
                some_str="random",
                role_arn=self.role.arn,
                sns_arn=self.topic.arn,
            )
        )
    
    @staticmethod
    def __template_body(some_str: str, role_arn: pulumi.Input[str], sns_arn: pulumi.Input[str])-> pulumi.Output[str]:
        return pulumi.Output.all(
            some_str,
            role_arn,
            sns_arn,
        ).apply(lambda args: json.dumps({
            "Resources": {
                "CustomResourceTest": {
                    "Type": "Custom::SnsCustomResourceTest",
                    "Properties": {
                        "Type": "AWS_CFG",
                        "ServiceToken": args[2],
                        "IntegrationName": {
                            "Ref": "AWS::StackName"
                        },
                        "RandomToken": args[0],
                        "RoleArn": args[1],
                        "TemplateVersion": "1.0",
                        "AWSAccountId": {
                            "Ref": "AWS::AccountId"
                        }
                    }
                }
            }
        }))

CustomResourceStack("test")
