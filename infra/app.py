import aws_cdk as cdk

from stack import FinanceAssistantStack

app = cdk.App()
FinanceAssistantStack(app, "SmartFinanceAssistant")
app.synth()
