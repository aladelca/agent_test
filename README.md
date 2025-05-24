# Course Management Telegram Bot

A multilingual Telegram bot for managing university course information, updates, and documents. The bot supports both Spanish and Quechua languages, making it accessible to a diverse student population.

## Features

- 🌐 Multilingual Support (Spanish and Quechua)
- 📚 Course Information Management
- 📝 Real-time Course Updates
- 📄 Document Management with S3 Storage
- 🔍 Semantic Search Capabilities.
- 🤖 AI-Powered Content Moderation
- 📅 Academic Cycle Management
- 👥 Section-based Organization

## Prerequisites

- Python 3.8+
- AWS Account with S3 access
- OpenAI API Key
- Telegram Bot Token
- AWS CLI installed and configured
- Terraform (optional, for IaC deployment)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
S3_BUCKET_NAME=your_s3_bucket_name
```

## AWS Deployment

### Option 1: Manual Deployment with ECS

1. Create an ECR repository:
```bash
aws ecr create-repository --repository-name course-bot --region your-region
```

2. Build and push Docker image:
```bash
# Login to ECR
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com

# Build image
docker build -t course-bot .

# Tag image
docker tag course-bot:latest your-account-id.dkr.ecr.your-region.amazonaws.com/course-bot:latest

# Push image
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/course-bot:latest
```

3. Create ECS Cluster AWS:
   - Go to AWS ECS Console
   - Create new cluster using Fargate
   - Configure networking (VPC, subnets)
   - Set up task definition with the container image
   - Configure environment variables
   - Set CPU (0.25 vCPU) and Memory (512MB)

4. Create ECS Service:
   - Deploy 1 task using Fargate
   - Configure networking and security groups
   - Enable service auto-scaling if needed

### Option 2: Automated Deployment with Terraform

1. Initialize Terraform:
```bash
cd terraform
terraform init
```

2. Review and modify variables:
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

3. Deploy infrastructure:
```bash
terraform plan
terraform apply
```

### Option 3: Continuous Deployment with GitHub Actions

The project includes automated deployment using GitHub Actions. When you push to the `main` branch, it will automatically:
1. Build the Docker image
2. Push it to Amazon ECR
3. Update the ECS task definition
4. Deploy the new version to ECS

To set up Continuous Deployment:

1. Create an IAM User for GitHub Actions:
   - Go to AWS IAM Console
   - Create a new IAM user
   - Attach the following policies:
     - `AmazonECS_FullAccess`
     - `AmazonECR_FullAccess`
   - Create and save the access key credentials

2. Configure GitHub Secrets:
   Go to your repository's Settings > Secrets and add:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key ID
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key
   - `AWS_REGION`: Your AWS region (e.g., us-east-1)

3. Configure ECS Task Definition:
   Make sure your ECS Task Definition includes these environment variables:
   ```json
   "environment": [
     {
       "name": "OPENAI_API_KEY",
       "value": "your-openai-api-key"
     },
     {
       "name": "TELEGRAM_BOT_TOKEN",
       "value": "your-telegram-bot-token"
     },
     {
       "name": "AWS_REGION",
       "value": "your-aws-region"
     },
     {
       "name": "S3_BUCKET_NAME",
       "value": "your-s3-bucket-name"
     }
   ]
   ```

4. Push to main:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

The workflow will automatically deploy your changes to ECS using:
- ECR Repository: `aladelcabot`
- ECS Cluster: `aladelcabot-cluster`
- Task Definition: `aladelcabot`
- Service: `aladelcabot`

### Monitoring Deployments

You can monitor deployments in:
1. GitHub Actions tab in your repository
2. AWS ECS Console
3. CloudWatch Logs

### Required AWS Resources

1. **VPC and Networking:**
   - VPC with public subnets
   - Internet Gateway
   - Route Tables
   - Security Groups

2. **ECS Resources:**
   - ECS Cluster
   - Task Definition
   - Service
   - Container Instances (managed by Fargate)

3. **IAM Roles and Policies:**
   - ECS Task Execution Role
   - ECS Task Role
   - S3 access policy

4. **S3 Bucket:**
   - For storing course documents
   - Configured with appropriate lifecycle policies

5. **CloudWatch:**
   - Container Insights enabled
   - Log groups for container logs
   - Service health alarms

### Cost Optimization

1. **Fargate Pricing:**
   - Using minimum required CPU (0.25 vCPU) and memory (512MB)
   - No need to pay for idle time unlike Lambda
   - Predictable pricing based on running time

2. **Auto-scaling:**
   - Service maintains single task
   - No over-provisioning
   - Cost-effective for 24/7 operation

### Monitoring and Maintenance

1. Set up CloudWatch Alarms:
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name course-bot-service-health \
    --alarm-description "Alert when service is unhealthy" \
    --metric-name RunningTaskCount \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 1 \
    --comparison-operator LessThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions your-sns-topic-arn \
    --dimensions Name=ClusterName,Value=course-bot-cluster Name=ServiceName,Value=course-bot
```

2. View container logs:
```bash
aws logs tail /ecs/course-bot --follow
```

## Project Structure

```
src/
├── config/
│   └── settings.py         # Configuration and environment variables
├── i18n/
│   └── messages.py         # Multilingual message translations
├── models/
│   └── state.py           # User state management models
├── services/
│   ├── content_moderator.py # Content moderation service
│   └── llm_service.py      # Language model service
├── utils/
│   ├── s3.py              # S3 storage utilities
│   ├── state.py           # State management utilities
│   └── validators.py       # Input validation utilities
├── database.py            # Database operations
├── main.py               # Main bot application
└── semantic_search.py     # Semantic search functionality
```

## Features in Detail

### Course Management
- Create and update course information
- Organize content by academic cycles and sections
- Support for multiple course modules (A/B)

### Document Management
- Upload and store course documents in S3
- Support for multiple file formats (PDF, Word, text files)
- Automatic content extraction and processing

### Content Moderation
- AI-powered content moderation
- Detection of inappropriate content
- Automatic warning system

### Multilingual Support
- Full support for Spanish and Quechua
- Language selection interface
- Translated responses and system messages

### Semantic Search
- Advanced search capabilities
- Context-aware responses
- Support for natural language queries

## Usage

1. Start the bot:
```bash
python src/main.py
```

2. In Telegram:
   - Start a conversation with the bot using `/start`
   - Select your preferred language
   - Follow the prompts to access course information

### Basic Commands
- `/start` - Begin interaction and select language
- `/update` - Update course information (for authorized users)
- Type 'menu' to return to the main menu at any time

## Security Features

- Content moderation for inappropriate content
- Secure file storage in S3
- Input validation and sanitization
- Error handling and logging

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Contact

For any queries or issues, please contact:
Professor Carlos Adrian Alarcon - pciscala@upc.edu.pe

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.