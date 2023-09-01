import pulumi
from pulumi_aws import (
    iam,
    cloudformation
)

class CustomResourceArgs:
    def __init__(
        self,
        topic_arn: pulumi.Input[str],
        bucket_role_arn: pulumi.Input[str],
        bucket_role: iam.Role,
    ):
        self.topic_arn = topic_arn
        self.bucket_role_arn = bucket_role_arn
        self.bucket_role = bucket_role

class CustomResourceStack(pulumi.ComponentResource):
    def __init__(self, name: str, args: CustomResourceArgs, opts: pulumi.ResourceOptions | None = None):
        print("hi from component")
        super().__init__("pkg:index:mycomponent", name, args, opts)
        self.custom_resource_stack = cloudformation.Stack(
            "test-stack",
            opts=pulumi.ResourceOptions(
                parent=self,
                ignore_changes="templateBody",
                depends_on=[args.bucket_role],
            ),
            name="CustomResourceTestStack",
            template_body=self.__template_body(
                some_str="random",
                role_arn=args.bucket_role_arn,
                sns_arn=args.topic_arn,
            ),
        )

        self.register_outputs({})

    @staticmethod
    def __template_body(
        some_str: str, role_arn: pulumi.Input[str], sns_arn: pulumi.Input[str]
    ) -> pulumi.Output[str]:
        return pulumi.Output.json_dumps(
            {
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
            }
        )
