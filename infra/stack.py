from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct


class FinanceAssistantStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        callback_url = self.node.try_get_context("callback_url") or "smartfinance://auth/callback"
        logout_url = self.node.try_get_context("logout_url") or "smartfinance://auth/logout"
        domain_prefix = self.node.try_get_context("cognito_domain_prefix") or "smart-finance-demo"

        user_pool = cognito.UserPool(
            self,
            "Users",
            sign_in_aliases=cognito.SignInAliases(email=True),
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN,
        )
        user_pool.add_domain(
            "ManagedLoginDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
            managed_login_version=cognito.ManagedLoginVersion.NEWER_MANAGED_LOGIN,
        )
        app_client = user_pool.add_client(
            "FlutterClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
                callback_urls=[callback_url],
                logout_urls=[logout_url],
            ),
            access_token_validity=Duration.minutes(60),
            refresh_token_validity=Duration.days(30),
            prevent_user_existence_errors=True,
        )

        table = dynamodb.Table(
            self,
            "FinanceTable",
            table_name=f"{self.stack_name}-finance",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(name="GSI1PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI1SK", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        receipts = s3.Bucket(
            self,
            "Receipts",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        gemini_secret = secretsmanager.Secret(self, "GeminiApiKey", description="Gemini API key for the finance assistant")

        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC)],
        )
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc, container_insights=True)
        log_group = logs.LogGroup(
            self,
            "ApiLogs",
            log_group_name=f"/ecs/{self.stack_name}/api",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        task = ecs.FargateTaskDefinition(self, "ApiTask", cpu=512, memory_limit_mib=1024)
        container = task.add_container(
            "Api",
            image=ecs.ContainerImage.from_asset(".."),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="api", log_group=log_group),
            environment={
                "ENVIRONMENT": "production",
                "AWS_REGION": self.region,
                "USE_IN_MEMORY_REPOSITORY": "false",
                "FINANCE_TABLE_NAME": table.table_name,
                "RECEIPTS_BUCKET_NAME": receipts.bucket_name,
                "COGNITO_REGION": self.region,
                "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                "COGNITO_APP_CLIENT_ID": app_client.user_pool_client_id,
                "LOG_JSON": "true",
            },
            secrets={"GEMINI_API_KEY": ecs.Secret.from_secrets_manager(gemini_secret)},
        )
        container.add_port_mappings(ecs.PortMapping(container_port=8000))
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=cluster,
            task_definition=task,
            public_load_balancer=True,
            assign_public_ip=True,
            desired_count=1,
            health_check_grace_period=Duration.seconds(90),
        )
        service.target_group.configure_health_check(path="/api/health/check", healthy_http_codes="200")
        table.grant_read_write_data(task.task_role)
        receipts.grant_read_write(task.task_role)
        gemini_secret.grant_read(task.execution_role)

        service.service.metric_cpu_utilization().create_alarm(
            self, "HighCpu", threshold=80, evaluation_periods=3, datapoints_to_alarm=2
        )
        service.load_balancer.metrics.http_code_elb(elbv2.HttpCodeElb.ELB_5XX_COUNT).create_alarm(
            self, "LoadBalancer5xx", threshold=5, evaluation_periods=2
        )
        dashboard = cloudwatch.Dashboard(self, "OperationsDashboard", dashboard_name=f"{self.stack_name}-operations")
        dashboard.add_widgets(cloudwatch.GraphWidget(title="API CPU", left=[service.service.metric_cpu_utilization()]))

        CfnOutput(self, "ApiUrl", value=f"http://{service.load_balancer.load_balancer_dns_name}")
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=app_client.user_pool_client_id)
        CfnOutput(self, "CognitoDomain", value=f"https://{domain_prefix}.auth.{self.region}.amazoncognito.com")
        CfnOutput(self, "FinanceTableName", value=table.table_name)
        CfnOutput(self, "ReceiptsBucketName", value=receipts.bucket_name)
        CfnOutput(self, "GeminiSecretArn", value=gemini_secret.secret_arn)
        CfnOutput(self, "ApiLogGroupName", value=log_group.log_group_name)
        CfnOutput(self, "EcsClusterName", value=cluster.cluster_name)
        CfnOutput(self, "EcsServiceName", value=service.service.service_name)
