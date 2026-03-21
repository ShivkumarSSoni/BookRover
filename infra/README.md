# BookRover — Infrastructure (Terraform)

Terraform IaC for all AWS resources. To be written in Phase 7 after manual AWS Console setup is complete and understood.

## Planned Structure
```
modules/
├── dynamodb/         # DynamoDB tables + GSIs
├── lambda/           # Lambda function + layers
├── api_gateway/      # HTTP API + Lambda integration
├── s3_cloudfront/    # S3 bucket + CloudFront distribution
└── iam/              # IAM roles + policies
environments/
├── dev.tfvars        # Dev environment variable values
└── prod.tfvars       # Prod environment variable values
main.tf               # Root module
variables.tf          # Input variable definitions
outputs.tf            # Output values (URLs, ARNs)
```

## AWS Services Covered
- S3, CloudFront, ACM
- API Gateway (HTTP API)
- Lambda
- DynamoDB (7 tables + GSIs)
- IAM roles + policies
- CloudWatch (log groups, alarms)
- Route 53 (optional)

## Prerequisites
- Complete manual AWS Console setup (Phase 4) first.
- Terraform >= 1.7
- AWS CLI configured with appropriate credentials.
